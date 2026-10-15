from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id
from utils import require_text, valid_contact, valid_email
from logic.auth import can


def list_customers():
    """Return all customer records."""
    return list(get_rows('customers'))


def get_customer(customer_id):
    """Retrieve customer by ID."""
    for c in get_rows('customers'):
        if c['customer_id'] == customer_id:
            return c
    return None


def ensure_customer_record(full_name, contact_no='', email='', address=''):
    """Find existing customer by name or auto-create a customer profile on registration/request."""
    fn = str(full_name).strip()
    if not fn:
        return None
    for c in get_rows('customers'):
        if c['name'].strip().lower() == fn.lower():
            updates = {}
            if contact_no and not c.get('contact_no'):
                updates['contact_no'] = contact_no
            if email and not c.get('email'):
                updates['email'] = email
            if address and not c.get('address'):
                updates['address'] = address
            if updates:
                update('customers', 'customer_id', c['customer_id'], updates)
                c.update(updates)
            return c
    cid = next_id('C', 3)
    row = {
        'customer_id': cid,
        'name': fn,
        'contact_no': contact_no or '',
        'email': email or '',
        'address': address or ''
    }
    insert('customers', row)
    return row


def add_customer(name, contact_no, email, address, acting_user):
    """Register a new customer (FR-07)."""
    if not can(acting_user['role'], 'customers'):
        raise RuleError("You do not have permission to add customers.")

    c_name = require_text(name, "Customer name")
    c_contact = valid_contact(contact_no, "Contact number")
    c_email = valid_email(email, "Email address")
    c_addr = require_text(address, "Address")

    cid = next_id('C', 3)
    row = {
        'customer_id': cid,
        'name': c_name,
        'contact_no': c_contact,
        'email': c_email,
        'address': c_addr
    }
    insert('customers', row)
    return row


def edit_customer(customer_id, name, contact_no, email, address, acting_user):
    """Update customer details (FR-08)."""
    if not can(acting_user['role'], 'customers'):
        raise RuleError("You do not have permission to edit customers.")

    existing = get_customer(customer_id)
    if not existing:
        raise ValidationError(f"Customer {customer_id} not found.")

    c_name = require_text(name, "Customer name")
    c_contact = valid_contact(contact_no, "Contact number")
    c_email = valid_email(email, "Email address")
    c_addr = require_text(address, "Address")

    changes = {
        'name': c_name,
        'contact_no': c_contact,
        'email': c_email,
        'address': c_addr
    }
    update('customers', 'customer_id', customer_id, changes)


def delete_customer(customer_id, acting_user):
    """Delete customer; blocked if any job order exists (FR-09)."""
    if not can(acting_user['role'], 'customers'):
        raise RuleError("You do not have permission to delete customers.")

    existing = get_customer(customer_id)
    if not existing:
        raise ValidationError(f"Customer {customer_id} not found.")

    # Block delete if referenced in any job order (active or past)
    jobs = get_rows('jobs')
    for j in jobs:
        if j['customer_id'] == customer_id:
            raise RuleError(
                f"Customer {customer_id} cannot be deleted because they have job orders on record (Job {j['job_id']})."
            )

    delete('customers', 'customer_id', customer_id)


def search_customers(query):
    """Search customers by name, ID, or contact number (FR-11)."""
    if not query or not query.strip():
        return list_customers()

    q = query.strip().lower()
    results = []
    for c in get_rows('customers'):
        if (q in c['customer_id'].lower() or
            q in c['name'].lower() or
            q in c['contact_no'].lower()):
            results.append(c)
    return results


def customer_history(customer_id):
    """Retrieve full repair history for a customer (FR-12)."""
    jobs = [j for j in get_rows('jobs') if j['customer_id'] == customer_id]
    return jobs
