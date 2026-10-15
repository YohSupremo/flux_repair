from decimal import Decimal
from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id, save_table
from utils import require_text, parse_money, parse_positive_int, parse_non_negative_int
from logic.auth import can


def list_parts():
    """Return all inventory parts."""
    return list(get_rows('parts'))


def get_part(part_id):
    """Retrieve part by ID."""
    for p in get_rows('parts'):
        if p['part_id'] == part_id:
            return p
    return None


def add_part(name, quantity, unit_price, low_stock_threshold, acting_user):
    """Add a part to inventory (Admin only, FR-33, FR-33a)."""
    if not can(acting_user['role'], 'manage_parts'):
        raise RuleError("Only Admin can manage inventory parts.")

    p_name = require_text(name, "Part name")
    p_qty = parse_non_negative_int(quantity, "Stock quantity")
    p_price = parse_money(unit_price, "Unit price")
    p_thresh = parse_non_negative_int(low_stock_threshold, "Low stock threshold")

    pid = next_id('P', 3)
    row = {
        'part_id': pid,
        'name': p_name,
        'quantity': str(p_qty),
        'unit_price': f"{p_price:.2f}",
        'low_stock_threshold': str(p_thresh)
    }
    insert('parts', row)
    return row


def edit_part(part_id, name, quantity, unit_price, low_stock_threshold, acting_user):
    """Edit part in inventory (Admin only)."""
    if not can(acting_user['role'], 'manage_parts'):
        raise RuleError("Only Admin can manage inventory parts.")

    existing = get_part(part_id)
    if not existing:
        raise ValidationError(f"Part {part_id} not found.")

    p_name = require_text(name, "Part name")
    p_qty = parse_non_negative_int(quantity, "Stock quantity")
    p_price = parse_money(unit_price, "Unit price")
    p_thresh = parse_non_negative_int(low_stock_threshold, "Low stock threshold")

    changes = {
        'name': p_name,
        'quantity': str(p_qty),
        'unit_price': f"{p_price:.2f}",
        'low_stock_threshold': str(p_thresh)
    }
    update('parts', 'part_id', part_id, changes)


def delete_part(part_id, acting_user):
    """Delete part; blocked if part is used in any job order (FR-33a)."""
    if not can(acting_user['role'], 'manage_parts'):
        raise RuleError("Only Admin can manage inventory parts.")

    existing = get_part(part_id)
    if not existing:
        raise ValidationError(f"Part {part_id} not found.")

    for jp in get_rows('job_parts'):
        if jp['part_id'] == part_id:
            raise RuleError(
                f"Part {part_id} cannot be deleted because it is recorded on Job {jp['job_id']}."
            )

    delete('parts', 'part_id', part_id)


def add_part_to_job(job_id, part_id, qty, acting_user):
    """Attach part to a job, verifying stock and decrementing inventory (FR-34, FR-36)."""
    part = get_part(part_id)
    if not part:
        raise ValidationError(f"Part {part_id} not found.")

    use_qty = parse_positive_int(qty, "Quantity used")
    current_stock = int(part['quantity'])
    if use_qty > current_stock:
        raise RuleError(f"Insufficient stock for {part['name']}. Available: {current_stock}, requested: {use_qty}.")

    # Decrement inventory stock
    update('parts', 'part_id', part_id, {'quantity': str(current_stock - use_qty)})

    # Insert into job_parts (with snapshotted unit price)
    insert('job_parts', {
        'job_id': job_id,
        'part_id': part_id,
        'quantity_used': str(use_qty),
        'unit_price': part['unit_price']
    })


def remove_part_from_job(job_id, part_id, acting_user):
    """Remove part from job and return stock to inventory."""
    job_parts = get_rows('job_parts')
    target = None
    for jp in job_parts:
        if jp['job_id'] == job_id and jp['part_id'] == part_id:
            target = jp
            break

    if not target:
        raise ValidationError(f"Part {part_id} is not attached to Job {job_id}.")

    qty_to_restore = int(target['quantity_used'])
    part = get_part(part_id)
    if part:
        new_stock = int(part['quantity']) + qty_to_restore
        update('parts', 'part_id', part_id, {'quantity': str(new_stock)})

    # Remove from job_parts
    db_parts = get_rows('job_parts')
    new_list = [jp for jp in db_parts if not (jp['job_id'] == job_id and jp['part_id'] == part_id)]
    import storage
    storage.db['job_parts'] = new_list
    storage.save_table('job_parts')


def restore_stock(job_id):
    """Restore all parts allocated to job back into stock on job cancellation (FR-28b)."""
    for jp in list(get_rows('job_parts')):
        if jp['job_id'] == job_id:
            qty = int(jp['quantity_used'])
            part = get_part(jp['part_id'])
            if part:
                new_stock = int(part['quantity']) + qty
                update('parts', 'part_id', jp['part_id'], {'quantity': str(new_stock)})


def low_stock_parts():
    """Return parts where quantity is at or below threshold (FR-35)."""
    results = []
    for p in get_rows('parts'):
        qty = int(p['quantity'])
        thresh = int(p['low_stock_threshold'])
        if qty <= thresh:
            results.append(p)
    return results
