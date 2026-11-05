from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id
from utils import require_text, valid_contact, valid_email
from logic.auth import can, register_user


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
    for c in reversed(get_rows('customers')):
        if c['name'].strip().lower() == fn.lower():
            updates = {}
            if contact_no:
                updates['contact_no'] = contact_no
            if email:
                updates['email'] = email
            if address:
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


def register_customer_account(username, password, confirm_password, full_name,
                              contact_no='', email='', address='', acting_user=None):
    """
    Onboard a customer with a login account, mirroring self-registration (FR-07).

    Authorized roles (Admin/Staff) can create the account on the customer's behalf.
    The new login is always assigned the Customer role; elevated roles remain
    Admin-only through the User Administration panel.
    """
    if acting_user is None or not can(acting_user['role'], 'customers'):
        raise RuleError("You do not have permission to add customers.")

    # Existing walk-in profiles may already own this email. Allow the login to be
    # attached to that same person, but reject emails belonging to another customer.
    email_clean = str(email or '').strip()
    if email_clean:
        email_clean = valid_email(email_clean, "Email address")
        existing = next(
            (c for c in get_rows('customers')
             if c.get('email', '').strip().lower() == email_clean.lower()),
            None
        )
        if existing and existing.get('name', '').strip().lower() != str(full_name).strip().lower():
            raise ValidationError("Email address is already registered.")

    return register_user(
        username=username,
        password=password,
        confirm_password=confirm_password,
        full_name=full_name,
        contact_no=contact_no,
        email=email,
        address=address,
        role="Customer",
        allow_existing_customer_email=True
    )


def find_linked_user_for_customer(customer_id_or_dict):
    """
    Find the Customer user account linked to a customer record.
    Matches by:
    1. Exact full name match.
    2. Email in profiles or customer registry.
    3. Prefix/submatch fallback for recently renamed accounts.
    """
    if isinstance(customer_id_or_dict, dict):
        cust = customer_id_or_dict
    else:
        cust = get_customer(customer_id_or_dict)
    if not cust:
        return None

    c_name = cust.get('name', '').strip().lower()
    c_email = cust.get('email', '').strip().lower()

    customer_users = [u for u in get_rows('users') if u.get('role') == 'Customer']

    # Prefer the profile email because names are not unique.
    if c_email:
        profiles = get_rows('profiles')
        for p in reversed(profiles):
            if p.get('email', '').strip().lower() == c_email:
                for u in customer_users:
                    if u.get('user_id') == p.get('user_id'):
                        return u

    # Only use a name match when it identifies exactly one account. Picking the
    # newest same-name account can update another customer's login.
    exact_name_matches = [
        u for u in customer_users
        if u.get('full_name', '').strip().lower() == c_name
    ]
    if len(exact_name_matches) == 1:
        return exact_name_matches[0]

    return None


def reset_customer_account_password(customer_id, new_password, confirm_password, acting_user):
    """
    Reset the login account password for a customer (Admin only).
    """
    if not can(acting_user['role'], 'manage_customer_accounts'):
        raise RuleError("Only Admin can reset customer passwords.")

    existing = get_customer(customer_id)
    if not existing:
        raise ValidationError(f"Customer {customer_id} not found.")

    np = str(new_password or '').strip()
    cp = str(confirm_password or '').strip()

    if not np:
        raise ValidationError("New password is required.")
    if len(np) < 8:
        raise ValidationError("Password must be at least 8 characters.")
    if np != cp:
        raise ValidationError("Passwords do not match.")

    linked_user = find_linked_user_for_customer(existing)
    if not linked_user:
        raise RuleError(
            "No login account is linked to this customer. "
            "Use + Register Customer to create one first."
        )

    update('users', 'user_id', linked_user['user_id'], {'password': np})


def update_customer_account_username(customer_id, new_username, acting_user):
    """
    Change the login username for a customer account (Admin only).
    """
    if not can(acting_user['role'], 'manage_customer_accounts'):
        raise RuleError("Only Admin can update customer usernames.")

    existing = get_customer(customer_id)
    if not existing:
        raise ValidationError(f"Customer {customer_id} not found.")

    u_clean = str(new_username or '').strip()
    if not u_clean:
        raise ValidationError("Username is required.")
    if ' ' in u_clean or len(u_clean) < 3 or len(u_clean) > 20:
        raise ValidationError("Username must be 3-20 characters with no spaces.")

    linked_user = find_linked_user_for_customer(existing)
    if not linked_user:
        raise RuleError(
            "No login account is linked to this customer. "
            "Use + Register Customer to create one first."
        )

    if linked_user.get('username') == u_clean:
        return

    # Reject if taken by another account
    for u in get_rows('users'):
        if u['user_id'] != linked_user['user_id'] and \
                u['username'].lower() == u_clean.lower():
            raise ValidationError(f"Username '{u_clean}' is already taken.")

    update('users', 'user_id', linked_user['user_id'], {'username': u_clean})


def edit_customer(customer_id, name, contact_no, email, address, acting_user):
    """Update customer details (FR-08)."""
    if not can(acting_user['role'], 'edit_customer_details'):
        raise RuleError("You do not have permission to edit customers.")

    existing = get_customer(customer_id)
    if not existing:
        raise ValidationError(f"Customer {customer_id} not found.")

    # Find linked user BEFORE updating customer record
    linked_user = find_linked_user_for_customer(existing)

    c_name    = require_text(name, "Customer name")
    c_contact = valid_contact(contact_no, "Contact number")
    c_email   = valid_email(email, "Email address")
    c_addr    = require_text(address, "Address")

    changes = {
        'name':       c_name,
        'contact_no': c_contact,
        'email':      c_email,
        'address':    c_addr
    }
    update('customers', 'customer_id', customer_id, changes)

    # Keep the linked Customer user account and profile in sync
    if linked_user:
        if linked_user.get('full_name', '').strip() != c_name:
            update('users', 'user_id', linked_user['user_id'], {'full_name': c_name})
            linked_user['full_name'] = c_name

        # If user has a profile record, sync that as well
        profiles = get_rows('profiles')
        for p in profiles:
            if p.get('user_id') == linked_user['user_id']:
                update('profiles', 'user_id', linked_user['user_id'], {
                    'contact_no': c_contact,
                    'email': c_email,
                    'address': c_addr
                })
                break


def delete_customer(customer_id, acting_user):
    """Delete customer; blocked if any job order exists (FR-09)."""
    if not can(acting_user['role'], 'deactivate_customers'):
        raise RuleError("Only Admin can deactivate customer accounts.")

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
