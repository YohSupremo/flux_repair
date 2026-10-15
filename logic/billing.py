import os
from decimal import Decimal
from errors import ValidationError, RuleError
from storage import get_rows, insert, next_id
from utils import require_text, parse_money, now_str, money
from models import PAYMENT_METHODS
from logic.auth import can
from config import RECEIPT_DIR


def compute_bill(job_id):
    """
    Compute real-time bill breakdown using Decimal (FR-37, FR-40, Section 4).
    Nothing computed is stored in CSV.
    """
    zero = Decimal('0.00')

    # Sum of services
    services_total = sum(
        (Decimal(r['price']) for r in get_rows('job_services') if r['job_id'] == job_id),
        zero
    )

    # Sum of parts
    parts_total = sum(
        (Decimal(r['unit_price']) * int(r['quantity_used'])
         for r in get_rows('job_parts') if r['job_id'] == job_id),
        zero
    )

    # Sum of payments
    paid_total = sum(
        (Decimal(r['amount']) for r in get_rows('payments') if r['job_id'] == job_id),
        zero
    )

    total = services_total + parts_total
    balance = max(zero, total - paid_total)

    return {
        'services': services_total.quantize(Decimal('0.01')),
        'parts': parts_total.quantize(Decimal('0.01')),
        'total': total.quantize(Decimal('0.01')),
        'paid': paid_total.quantize(Decimal('0.01')),
        'balance': balance.quantize(Decimal('0.01'))
    }


def record_payment(job_id, tendered_amount, method, acting_user):
    """
    Record payment for a repair job order (FR-38, FR-39, FR-40).
    For cash, change is calculated and returned. Amount recorded equals the applied amount.
    """
    is_customer = (acting_user['role'] == 'Customer')
    if not can(acting_user['role'], 'billing') and not is_customer:
        raise RuleError("You do not have permission to process billing.")

    if is_customer:
        from logic.jobs import find_job
        job = find_job(job_id)
        if not job:
            raise ValidationError(f"Job {job_id} not found.")
        cust = next((c for c in get_rows('customers') if c['customer_id'] == job['customer_id']), None)
        if not cust or cust['name'].strip().lower() != acting_user['full_name'].strip().lower():
            raise RuleError("Customers can only pay or downpay their own repair jobs.")
        if method == 'Cash':
            raise ValidationError("Direct cash is only accepted on-site at the workshop counter. Please select GCash or Card for online payment.")

    bill = compute_bill(job_id)
    balance = bill['balance']

    if balance <= Decimal('0.00') and bill['total'] > Decimal('0.00'):
        raise RuleError("This job order is already fully paid.")

    tendered = parse_money(tendered_amount, "Payment amount")
    if tendered <= Decimal('0.00'):
        raise ValidationError("Payment amount must be greater than zero.")

    if method not in PAYMENT_METHODS:
        raise ValidationError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}.")

    # Calculate applied payment vs change
    if bill['total'] == Decimal('0.00'):
        # Initial advance downpayment / retainer deposit
        applied = tendered
        change = Decimal('0.00')
    elif method == 'Cash':
        if tendered < balance:
            # Partial / Downpayment
            applied = tendered
            change = Decimal('0.00')
        else:
            # Full payment or overpaid cash
            applied = balance
            change = tendered - balance
    else:
        # Non-cash methods (GCash / Card) cannot exceed balance
        if tendered > balance:
            raise ValidationError(
                f"Digital payment ({method}) cannot exceed balance due of {money(balance)}."
            )
        applied = tendered
        change = Decimal('0.00')

    pid = next_id('PAY', 4)
    pay_time = now_str()

    row = {
        'payment_id': pid,
        'job_id': job_id,
        'amount': f"{applied:.2f}",
        'method': method,
        'payment_date': pay_time,
        'received_by': acting_user['user_id']
    }
    insert('payments', row)

    # Save updated official receipt
    save_official_receipt(job_id)

    new_bill = compute_bill(job_id)

    return {
        'payment_id': pid,
        'applied': applied,
        'tendered': tendered,
        'change': change,
        'balance': new_bill['balance']
    }


def official_receipt_text(job_id):
    """Generate official invoice/receipt text layout (FR-41)."""
    from logic.jobs import job_details
    details = job_details(job_id)
    j = details['job']
    c = details['customer'] or {}
    bill = details['bill']

    lines = []
    lines.append("=" * 52)
    lines.append("             FLUX REPAIR CO. ATELIER")
    lines.append("           OFFICIAL REPAIR INVOICE")
    lines.append("      118 Beacon Works, Unit 3 • (555) 019-3350")
    lines.append("=" * 52)
    lines.append(f"JOB ORDER: {j['job_id']}".ljust(26) + f"DATE: {now_str()}".rjust(26))
    lines.append("-" * 52)
    lines.append(f"CUSTOMER: {c.get('name', 'N/A')}")
    lines.append(f"CONTACT:  {c.get('contact_no', 'N/A')}")
    lines.append(f"DEVICE:   {j['device_type']} ({j['brand']} {j['model']})")
    lines.append(f"SERIAL:   {j['serial_no']}")
    lines.append("=" * 52)
    lines.append("ITEMIZED SERVICES & LABOR".ljust(38) + "AMOUNT".rjust(14))
    lines.append("-" * 52)
    if details['services']:
        for s in details['services']:
            lines.append(f"  {s['name'][:34].ljust(36)} {money(s['price']).rjust(14)}")
    else:
        lines.append("  Standard Diagnostics".ljust(38) + money("0.00").rjust(14))
    lines.append("-" * 52)
    lines.append("SUBTOTAL (SERVICES):".ljust(36) + money(bill['services']).rjust(16))

    if details['parts']:
        lines.append("-" * 52)
        lines.append("HARDWARE & REPLACEMENT COMPONENTS".ljust(38) + "AMOUNT".rjust(14))
        lines.append("-" * 52)
        for p in details['parts']:
            lbl = f"  {p['name']} (x{p['quantity_used']})"
            lines.append(f"{lbl[:34].ljust(36)} {money(p['line_total']).rjust(16)}")
        lines.append("-" * 52)
        lines.append("SUBTOTAL (PARTS):".ljust(36) + money(bill['parts']).rjust(16))

    lines.append("=" * 52)
    lines.append("TOTAL REPAIR CHARGES:".ljust(36) + money(bill['total']).rjust(16))
    lines.append("PAYMENTS RECEIVED:".ljust(36) + money(bill['paid']).rjust(16))
    lines.append("-" * 52)
    lines.append("OUTSTANDING BALANCE:".ljust(36) + money(bill['balance']).rjust(16))
    lines.append("=" * 52)

    if details['payments']:
        lines.append("PAYMENT HISTORY:")
        for pay in details['payments']:
            p_desc = f"  [{pay['payment_date']}] {pay['method']}"
            lines.append(f"{p_desc.ljust(36)} {money(pay['amount']).rjust(16)}")
        lines.append("-" * 52)

    lines.append("WARRANTY & TERMS:")
    lines.append("• 90-Day parts and workmanship warranty on replaced ICs.")
    lines.append("• Physical impact and liquid re-ingress void warranty.")
    lines.append("• Thank you for supporting honest component repair!")
    lines.append("=" * 52)

    return "\n".join(lines)


def save_official_receipt(job_id):
    """Save official receipt text to receipts/ folder."""
    try:
        os.makedirs(RECEIPT_DIR, exist_ok=True)
        path = os.path.join(RECEIPT_DIR, f"{job_id}_official.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(official_receipt_text(job_id))
        return path
    except OSError:
        return None
