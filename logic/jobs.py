import os
from decimal import Decimal
from errors import ValidationError, RuleError
from storage import get_rows, insert, update, next_id
from models import TRANSITIONS, DEVICE_TYPES, PRIORITIES
from utils import require_text, now_str, money
from logic.auth import can
from logic.parts import restore_stock
from config import RECEIPT_DIR


def current_status(job_id):
    """Determine current status from latest log entry ordered by log_id (FR-29)."""
    logs = [l for l in get_rows('status_log') if l['job_id'] == job_id]
    if not logs:
        return 'Received'
    # Log IDs are formatted L-00001
    return max(logs, key=lambda l: int(l['log_id'].split('-')[1]))['status']


def status_map():
    """Build single-pass map of {job_id: current_status} for fast table rendering."""
    latest = {}
    for l in get_rows('status_log'):
        n = int(l['log_id'].split('-')[1])
        jid = l['job_id']
        if jid not in latest or n > latest[jid][0]:
            latest[jid] = (n, l['status'])
    return {j: v[1] for j, v in latest.items()}


def find_job(job_id):
    """Find job record by ID."""
    for j in get_rows('jobs'):
        if j['job_id'] == job_id:
            return j
    return None


def create_job(data, accessories, service_ids, acting_user):
    """
    Intake a new repair job order (FR-13 - FR-20).
    Saves in fixed order: jobs -> job_accessories -> job_services -> status_log.
    """
    is_cust = (acting_user['role'] == 'Customer')
    if not can(acting_user['role'], 'create_jobs') and not is_cust:
        raise RuleError("You do not have permission to intake job orders.")

    cid = require_text(data.get('customer_id'), "Customer")
    # Verify customer exists
    cust = next((c for c in get_rows('customers') if c['customer_id'] == cid), None)
    if not cust:
        raise ValidationError(f"Customer {cid} does not exist.")

    if is_cust and cust['name'].strip().lower() != acting_user['full_name'].strip().lower():
        raise RuleError("Customers can only request repairs under their own account.")

    dtype = require_text(data.get('device_type'), "Device type")
    if dtype not in DEVICE_TYPES:
        raise ValidationError(f"Device type must be one of: {', '.join(DEVICE_TYPES)}.")

    brand = require_text(data.get('brand'), "Brand")
    model = require_text(data.get('model'), "Model")
    serial_no = require_text(data.get('serial_no'), "Serial number")
    problem = require_text(data.get('problem'), "Problem description")
    condition = str(data.get('device_condition', "")).strip() or "Normal wear"
    priority = data.get('priority', 'Normal')
    if priority not in PRIORITIES:
        priority = 'Normal'
    est_completion = str(data.get('est_completion', "")).strip()
    tech_id = "" if is_cust else str(data.get('technician_id', "")).strip()

    if tech_id:
        tech = next((u for u in get_rows('users') if u['user_id'] == tech_id and u['role'] == 'Technician'), None)
        if not tech:
            raise ValidationError("Assigned technician must be a valid user with role Technician.")

    jid = next_id('J', 4)
    received_time = now_str()

    # Safeguard: Clean slate for jid in case IDs were recycled or tables manually edited
    for tbl in ('job_accessories', 'job_services', 'job_parts', 'payments', 'status_log'):
        existing = get_rows(tbl)
        if any(r.get('job_id') == jid for r in existing):
            from storage import db, save_table
            db[tbl] = [r for r in existing if r.get('job_id') != jid]
            save_table(tbl)

    job_row = {
        'job_id': jid,
        'customer_id': cid,
        'technician_id': tech_id,
        'received_by': acting_user['user_id'],
        'device_type': dtype,
        'brand': brand,
        'model': model,
        'serial_no': serial_no,
        'problem': problem,
        'device_condition': condition,
        'priority': priority,
        'date_received': received_time,
        'est_completion': est_completion,
        'diagnosis': '',
        'notes': '',
        'cancel_reason': ''
    }

    # Step 1: Save job
    insert('jobs', job_row)

    # Step 2: Save accessories
    for acc in accessories:
        if str(acc).strip():
            insert('job_accessories', {
                'job_id': jid,
                'accessory': str(acc).strip()
            })

    # Step 3: Save services (copying catalog prices, FR-24a)
    services_catalog = {s['service_id']: s for s in get_rows('services')}
    for sid in service_ids:
        if sid in services_catalog:
            s_item = services_catalog[sid]
            insert('job_services', {
                'job_id': jid,
                'service_id': sid,
                'price': s_item['price']
            })

    # Step 4: Save initial status log (Received)
    lid = next_id('L', 5)
    insert('status_log', {
        'log_id': lid,
        'job_id': jid,
        'status': 'Received',
        'changed_at': received_time,
        'changed_by': acting_user['user_id']
    })

    # Generate intake receipt file
    save_intake_receipt(jid)

    return jid


def edit_job(job_id, data, acting_user):
    """Edit job intake details until status is Completed (FR-20a)."""
    st = current_status(job_id)
    if st in ('Completed', 'Released', 'Cancelled'):
        raise RuleError(f"Cannot edit intake details for job in {st} status.")

    job = find_job(job_id)
    if not job:
        raise ValidationError(f"Job {job_id} not found.")

    dtype = require_text(data.get('device_type'), "Device type")
    brand = require_text(data.get('brand'), "Brand")
    model = require_text(data.get('model'), "Model")
    serial_no = require_text(data.get('serial_no'), "Serial number")
    problem = require_text(data.get('problem'), "Problem description")
    condition = str(data.get('device_condition', "")).strip()
    priority = data.get('priority', 'Normal')
    est_completion = str(data.get('est_completion', "")).strip()

    changes = {
        'device_type': dtype,
        'brand': brand,
        'model': model,
        'serial_no': serial_no,
        'problem': problem,
        'device_condition': condition,
        'priority': priority,
        'est_completion': est_completion
    }
    update('jobs', 'job_id', job_id, changes)


def assign_technician(job_id, technician_id, acting_user):
    """Assign or reassign technician to job (FR-25)."""
    if not can(acting_user['role'], 'assign_tech'):
        raise RuleError("You do not have permission to assign technicians.")

    job = find_job(job_id)
    if not job:
        raise ValidationError(f"Job {job_id} not found.")

    if technician_id:
        tech = next((u for u in get_rows('users') if u['user_id'] == technician_id and u['role'] == 'Technician'), None)
        if not tech:
            raise ValidationError("Selected user is not a registered Technician.")
        update('jobs', 'job_id', job_id, {'technician_id': technician_id})
    else:
        update('jobs', 'job_id', job_id, {'technician_id': ''})


def record_diagnosis(job_id, diagnosis, notes, acting_user):
    """Record diagnostic findings and repair notes (FR-27)."""
    job = find_job(job_id)
    if not job:
        raise ValidationError(f"Job {job_id} not found.")

    if acting_user['role'] == 'Technician' and job['technician_id'] != acting_user['user_id']:
        raise RuleError("Technicians may only update notes on their own assigned jobs.")

    changes = {
        'diagnosis': str(diagnosis).strip(),
        'notes': str(notes).strip()
    }
    update('jobs', 'job_id', job_id, changes)


def add_service_to_job(job_id, service_id, acting_user, custom_price=None):
    """Add service to job until status is Completed (FR-24a, FR-24b)."""
    st = current_status(job_id)
    if st in ('Completed', 'Released', 'Cancelled'):
        raise RuleError(f"Cannot add services to a {st} job.")

    srv = next((s for s in get_rows('services') if s['service_id'] == service_id), None)
    if not srv:
        raise ValidationError(f"Service {service_id} not found.")

    price = f"{Decimal(custom_price):.2f}" if custom_price is not None else srv['price']
    insert('job_services', {
        'job_id': job_id,
        'service_id': service_id,
        'price': price
    })


def remove_service_from_job(job_id, service_id, acting_user):
    """Remove a service from job before Completed (FR-24a)."""
    st = current_status(job_id)
    if st in ('Completed', 'Released', 'Cancelled'):
        raise RuleError(f"Cannot modify services on a {st} job.")

    js_rows = get_rows('job_services')
    target = next((r for r in js_rows if r['job_id'] == job_id and r['service_id'] == service_id), None)
    if not target:
        raise ValidationError(f"Service {service_id} is not attached to Job {job_id}.")

    new_list = [r for r in js_rows if not (r['job_id'] == job_id and r['service_id'] == service_id)]
    import storage
    storage.db['job_services'] = new_list
    storage.save_table('job_services')


def change_status(job_id, new_status, acting_user, cancel_reason=None):
    """
    Transition job status according to state machine rules (FR-28a, FR-28b, FR-42).
    """
    job = find_job(job_id)
    if not job:
        raise ValidationError(f"Job {job_id} not found.")

    curr = current_status(job_id)
    allowed = TRANSITIONS.get(curr, [])
    if new_status not in allowed:
        raise RuleError(f"Illegal transition: Cannot change from '{curr}' to '{new_status}'.")

    # Role enforcement
    if acting_user['role'] == 'Technician':
        if job['technician_id'] != acting_user['user_id']:
            raise RuleError("Technicians may only update status for their own assigned jobs.")
        if new_status in ('Released', 'Cancelled'):
            raise RuleError("Technicians cannot release or cancel job orders.")

    # Rule FR-42: Released requires balance == 0
    if new_status == 'Released':
        from logic.billing import compute_bill
        bill = compute_bill(job_id)
        if bill['balance'] > Decimal('0.00'):
            raise RuleError(
                f"Cannot release device: Remaining balance of {money(bill['balance'])} must be paid in full."
            )

    # Rule FR-28b: Cancelled requires reason and restores inventory parts
    if new_status == 'Cancelled':
        c_reason = require_text(cancel_reason, "Cancellation reason")
        update('jobs', 'job_id', job_id, {'cancel_reason': c_reason})
        restore_stock(job_id)

    lid = next_id('L', 5)
    insert('status_log', {
        'log_id': lid,
        'job_id': job_id,
        'status': new_status,
        'changed_at': now_str(),
        'changed_by': acting_user['user_id']
    })


def list_jobs(status_filter=None, search_text=None, technician_id=None, customer_name_filter=None):
    """
    List job orders with optional status filter, technician filter, customer filter, and search.
    (FR-26, FR-30, FR-31)
    """
    jobs = get_rows('jobs')
    s_map = status_map()
    customers = {c['customer_id']: c['name'] for c in get_rows('customers')}

    results = []
    q = (search_text or "").strip().lower()
    c_filter = customer_name_filter.strip().lower() if customer_name_filter else None

    for j in jobs:
        jid = j['job_id']
        st = s_map.get(jid, 'Received')
        c_name = customers.get(j['customer_id'], 'Unknown')

        # Filter by customer
        if c_filter and c_name.strip().lower() != c_filter:
            continue

        # Filter by technician
        if technician_id and j.get('technician_id') != technician_id:
            continue

        # Filter by status
        if status_filter and status_filter != 'All' and st != status_filter:
            continue

        # Search filter (Job ID, customer name, serial number)
        if q:
            if not (q in jid.lower() or q in c_name.lower() or q in j['serial_no'].lower()):
                continue

        results.append({
            **j,
            'status': st,
            'customer_name': c_name
        })

    # Return descending by job_id
    results.sort(key=lambda x: int(x['job_id'].split('-')[1]), reverse=True)
    return results


def job_details(job_id):
    """Gather full job dossier (FR-31a)."""
    job = find_job(job_id)
    if not job:
        raise ValidationError(f"Job {job_id} not found.")

    cust = next((c for c in get_rows('customers') if c['customer_id'] == job['customer_id']), None)
    tech = next((u for u in get_rows('users') if u['user_id'] == job['technician_id']), None)
    recv = next((u for u in get_rows('users') if u['user_id'] == job['received_by']), None)

    accessories = [r['accessory'] for r in get_rows('job_accessories') if r['job_id'] == job_id]

    # Services
    srv_cat = {s['service_id']: s['name'] for s in get_rows('services')}
    services = [
        {
            'service_id': r['service_id'],
            'name': srv_cat.get(r['service_id'], 'Unknown Service'),
            'price': r['price']
        }
        for r in get_rows('job_services') if r['job_id'] == job_id
    ]

    # Parts
    part_cat = {p['part_id']: p['name'] for p in get_rows('parts')}
    parts = [
        {
            'part_id': r['part_id'],
            'name': part_cat.get(r['part_id'], 'Unknown Part'),
            'quantity_used': r['quantity_used'],
            'unit_price': r['unit_price'],
            'line_total': f"{Decimal(r['unit_price']) * int(r['quantity_used']):.2f}"
        }
        for r in get_rows('job_parts') if r['job_id'] == job_id
    ]

    # Status logs
    user_map = {u['user_id']: u['full_name'] for u in get_rows('users')}
    history = [
        {
            **l,
            'actor_name': user_map.get(l['changed_by'], l['changed_by'])
        }
        for l in get_rows('status_log') if l['job_id'] == job_id
    ]
    history.sort(key=lambda l: int(l['log_id'].split('-')[1]))

    # Payments
    payments = [
        {
            **p,
            'receiver_name': user_map.get(p['received_by'], p['received_by'])
        }
        for p in get_rows('payments') if p['job_id'] == job_id
    ]

    from logic.billing import compute_bill
    bill = compute_bill(job_id)

    return {
        'job': job,
        'customer': cust,
        'technician': tech,
        'received_by_user': recv,
        'status': current_status(job_id),
        'accessories': accessories,
        'services': services,
        'parts': parts,
        'history': history,
        'payments': payments,
        'bill': bill
    }


def intake_receipt_text(job_id):
    """Generate clean fixed-width intake receipt text (FR-19)."""
    details = job_details(job_id)
    j = details['job']
    c = details['customer'] or {}

    lines = []
    lines.append("=" * 48)
    lines.append("           FLUX REPAIR CO. ATELIER")
    lines.append("       SURGICAL ELECTRONICS DIAGNOSTICS")
    lines.append("=" * 48)
    lines.append(f"JOB TICKET: {j['job_id']}".ljust(24) + f"DATE: {j['date_received']}".rjust(24))
    lines.append("-" * 48)
    lines.append(f"CUSTOMER: {c.get('name', 'N/A')}")
    lines.append(f"CONTACT:  {c.get('contact_no', 'N/A')}")
    lines.append("-" * 48)
    lines.append(f"DEVICE:    {j['device_type']} - {j['brand']} {j['model']}")
    lines.append(f"SERIAL NO: {j['serial_no']}")
    lines.append(f"CONDITION: {j['device_condition']}")
    lines.append(f"PRIORITY:  {j['priority']}")
    if details['accessories']:
        lines.append(f"ACCESSORIES: {', '.join(details['accessories'])}")
    lines.append("-" * 48)
    lines.append("REPORTED ISSUE:")
    lines.append(f"  {j['problem']}")
    lines.append("-" * 48)
    lines.append("INITIAL SERVICES AT INTAKE:")
    if details['services']:
        for s in details['services']:
            lines.append(f"  • {s['name'][:30].ljust(32)} {money(s['price']).rjust(12)}")
    else:
        lines.append("  • Diagnostic & Bench Assessment")
    lines.append("-" * 48)
    lines.append("ESTIMATED TOTAL:".ljust(32) + money(details['bill']['total']).rjust(16))
    lines.append("=" * 48)
    lines.append("Notice: Devices unclaimed after 60 days are subject")
    lines.append("to workshop disposal rules. Thank you for your trust.")
    lines.append("=" * 48)
    return "\n".join(lines)


def save_intake_receipt(job_id):
    """Save intake receipt to receipts/ folder."""
    try:
        os.makedirs(RECEIPT_DIR, exist_ok=True)
        path = os.path.join(RECEIPT_DIR, f"{job_id}_intake.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(intake_receipt_text(job_id))
        return path
    except OSError:
        return None
