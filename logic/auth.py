from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id
from models import ROLES
from utils import require_text, valid_contact, valid_email

# Permission matrix based on §2.1
PERMISSIONS = {
    'Admin': {
        'manage_users': True,
        'manage_services': True,
        'manage_parts': True,
        'customers': True,
        'view_customer_accounts': True,
        'edit_customer_details': True,
        'register_customer_accounts': True,
        'manage_customer_accounts': True,
        'deactivate_customers': True,
        'create_jobs': True,
        'assign_tech': True,
        'update_status': True,
        'record_diagnosis': True,
        'billing': True,
        'reports': True,
        'backup': True,
    },
    'Staff': {
        'manage_users': False,
        'manage_services': False,
        'manage_parts': False,
        'customers': True,
        'view_customer_accounts': True,
        'edit_customer_details': True,
        'register_customer_accounts': True,
        'manage_customer_accounts': False,
        'deactivate_customers': False,
        'create_jobs': True,
        'assign_tech': True,
        'update_status': True,
        'record_diagnosis': False,
        'billing': True,
        'reports': True,
        'backup': False,
    },
    'Technician': {
        'manage_users': False,
        'manage_services': False,
        'manage_parts': False,
        'customers': False,
        'view_customer_accounts': False,
        'edit_customer_details': False,
        'register_customer_accounts': False,
        'manage_customer_accounts': False,
        'deactivate_customers': False,
        'create_jobs': False,
        'assign_tech': False,
        'update_status': True,        # own jobs only
        'record_diagnosis': True,     # own jobs only
        'billing': False,
        'reports': False,
        'backup': False,
    },
    'Customer': {
        'manage_users': False,
        'manage_services': False,
        'manage_parts': False,
        'customers': False,
        'view_customer_accounts': False,
        'edit_customer_details': False,
        'register_customer_accounts': False,
        'manage_customer_accounts': False,
        'deactivate_customers': False,
        'create_jobs': False,
        'assign_tech': False,
        'update_status': False,
        'record_diagnosis': False,
        'billing': False,
        'reports': False,
        'backup': False,
    }
}


def can(role, action):
    """Check if the given role has permission to execute action."""
    return PERMISSIONS.get(role, {}).get(action, False)


def validate_registration_email(email):
    """Validate registration email syntax and ensure it is not already registered."""
    email_clean = valid_email(email, "Email address")
    if any(c.get('email', '').strip().lower() == email_clean.lower() for c in get_rows('customers')):
        raise ValidationError("Email address is already registered.")
    return email_clean


def seed_default_admin():
    """Ensure at least one admin exists on startup (FR-05a)."""
    users = get_rows('users')
    if not users:
        admin_id = next_id('U', 3)
        row = {
            'user_id': admin_id,
            'username': 'admin',
            'password': 'admin123',
            'role': 'Admin',
            'full_name': 'Default Administrator'
        }
        insert('users', row)
        return "Default admin account created (admin / admin123). Please change password."
    return None


def find_user_by_identity(identity):
    """Find user record by username or registered customer email."""
    id_clean = require_text(identity, "Username or Email").strip().lower()
    users = get_rows('users')
    
    # 1. Match by username
    for u in users:
        if u['username'].lower() == id_clean:
            return u

    # 2. Match by email in customers table
    customers = get_rows('customers')
    for c in customers:
        if c.get('email', '').strip().lower() == id_clean:
            cust_name = c['name'].strip().lower()
            for u in users:
                if u['full_name'].strip().lower() == cust_name:
                    return u

    return None


def login(username_or_email, password):
    """Authenticate credentials by username or email and return user dictionary (FR-01, FR-02)."""
    p_clean = require_text(password, "Password")
    user = find_user_by_identity(username_or_email)

    if user and user['password'] == p_clean:
        status = next(
            (s.get('status') for s in get_rows('account_status')
             if s.get('user_id') == user['user_id']),
            'Active'
        )
        if status != 'Active':
            raise ValidationError("This account is deactivated.")
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'full_name': user['full_name']
        }
    raise ValidationError("Invalid username, email, or password.")


def deactivate_account(user_id, acting_user):
    """Deactivate a customer account by itself or an Admin."""
    target = next((u for u in get_rows('users') if u.get('user_id') == user_id), None)
    if not target:
        raise ValidationError(f"User {user_id} not found.")

    is_self = acting_user.get('user_id') == user_id
    is_admin = acting_user.get('role') == 'Admin'
    if not is_self and not is_admin:
        raise RuleError("Only the account owner or an Admin can deactivate this account.")
    if target.get('role') == 'Admin' and is_self:
        raise RuleError("Admin accounts must be deactivated by another Admin.")

    existing = next(
        (s for s in get_rows('account_status') if s.get('user_id') == user_id),
        None
    )
    if existing:
        update('account_status', 'user_id', user_id, {'status': 'Deactivated'})
    else:
        insert('account_status', {'user_id': user_id, 'status': 'Deactivated'})


def reactivate_account(user_id, acting_user):
    """Reactivate an account; only Admins may perform this action."""
    if not can(acting_user.get('role'), 'manage_users'):
        raise RuleError("Only Admin can reactivate accounts.")
    target = next((u for u in get_rows('users') if u.get('user_id') == user_id), None)
    if not target:
        raise ValidationError(f"User {user_id} not found.")
    existing = next(
        (s for s in get_rows('account_status') if s.get('user_id') == user_id),
        None
    )
    if existing:
        update('account_status', 'user_id', user_id, {'status': 'Active'})


def account_status(user_id):
    """Return Active unless an explicit deactivation record exists."""
    row = next((s for s in get_rows('account_status') if s.get('user_id') == user_id), None)
    return row.get('status', 'Active') if row else 'Active'


def recover_password(identity, new_password, confirm_password):
    """Reset password for verified user identity."""
    user = find_user_by_identity(identity)
    if not user:
        raise ValidationError(f"No account found matching \"{identity}\".")

    np = str(new_password).strip()
    cp = str(confirm_password).strip()

    if len(np) < 8:
        raise ValidationError("New password must be at least 8 characters.")
    if np != cp:
        raise ValidationError("New passwords do not match.")

    update('users', 'user_id', user['user_id'], {'password': np})
    return user


def list_users():
    """Return all users without exposing passwords."""
    return [
        {
            'user_id': u['user_id'],
            'username': u['username'],
            'role': u['role'],
            'full_name': u['full_name'],
            'status': account_status(u['user_id'])
        }
        for u in get_rows('users')
    ]


def get_technicians():
    """Return list of users with Technician role for job assignment (FR-25)."""
    return [u for u in get_rows('users') if u['role'] == 'Technician']


def add_user(username, password, role, full_name, acting_user):
    """Add a new user (Admin only, FR-05)."""
    if not can(acting_user['role'], 'manage_users'):
        raise RuleError("Only Admin can add users.")

    u_clean = require_text(username, "Username")
    if " " in u_clean or len(u_clean) < 3 or len(u_clean) > 20:
        raise ValidationError("Username must be 3-20 characters with no spaces.")

    p_clean = require_text(password, "Password")
    if len(p_clean) < 8:
        raise ValidationError("Password must be at least 8 characters.")

    if role not in ROLES:
        raise ValidationError(f"Role must be one of: {', '.join(ROLES)}.")

    fn_clean = require_text(full_name, "Full Name")

    # Check unique username (FR-55)
    for u in get_rows('users'):
        if u['username'].lower() == u_clean.lower():
            raise ValidationError(f"Username '{u_clean}' is already taken.")

    uid = next_id('U', 3)
    row = {
        'user_id': uid,
        'username': u_clean,
        'password': p_clean,
        'role': role,
        'full_name': fn_clean
    }
    insert('users', row)
    return row


def register_user(username, password, confirm_password, full_name, contact_no='', email='', address='', role="Customer", allow_existing_customer_email=False):
    """
    Self-registration: Always creates account with 'Customer' role by default.
    Elevated system roles (Admin, Staff, Technician) can only be assigned by Admins.
    Stores personal contact details and delivery/service address in linked customer profile.

    When allow_existing_customer_email is True, an email that already belongs to the
    same customer profile is accepted so staff can create a login for an existing
    walk-in customer (see logic.customers.register_customer_account).
    """
    assigned_role = "Customer"

    u_clean = require_text(username, "Username")
    if " " in u_clean or len(u_clean) < 3 or len(u_clean) > 20:
        raise ValidationError("Username must be 3-20 characters with no spaces.")

    p_clean = require_text(password, "Password")
    if len(p_clean) < 8:
        raise ValidationError("Password must be at least 8 characters.")

    cp_clean = require_text(confirm_password, "Confirm Password")
    if p_clean != cp_clean:
        raise ValidationError("Passwords do not match.")

    fn_clean = require_text(full_name, "Full Name")

    c_contact = str(contact_no or '').strip()
    if c_contact:
        c_contact = valid_contact(c_contact, "Contact number")
    c_email = str(email or '').strip()
    if c_email:
        if allow_existing_customer_email:
            c_email = valid_email(c_email, "Email address")
        else:
            c_email = validate_registration_email(c_email)
    c_addr = str(address or '').strip()

    # Check duplicate username
    for u in get_rows('users'):
        if u['username'].lower() == u_clean.lower():
            raise ValidationError(f"Username '{u_clean}' is already registered.")

    uid = next_id('U', 3)
    row = {
        'user_id': uid,
        'username': u_clean,
        'password': p_clean,
        'role': assigned_role,
        'full_name': fn_clean
    }
    insert('users', row)

    insert('profiles', {
        'user_id': uid,
        'contact_no': c_contact,
        'email': c_email,
        'address': c_addr
    })

    # Automatically create/sync customer record with contact details and address
    from logic.customers import ensure_customer_record
    ensure_customer_record(fn_clean, contact_no=c_contact, email=c_email, address=c_addr)

    return {
        'user_id': uid,
        'username': u_clean,
        'role': assigned_role,
        'full_name': fn_clean
    }


def edit_user(user_id, username, password, role, full_name, acting_user):
    """Edit user details (Admin only)."""
    if not can(acting_user['role'], 'manage_users'):
        raise RuleError("Only Admin can edit users.")

    users = get_rows('users')
    existing = next((u for u in users if u['user_id'] == user_id), None)
    if not existing:
        raise ValidationError(f"User {user_id} not found.")

    u_clean = require_text(username, "Username")
    if " " in u_clean or len(u_clean) < 3 or len(u_clean) > 20:
        raise ValidationError("Username must be 3-20 characters with no spaces.")

    # Check duplicate username for other users
    for u in users:
        if u['user_id'] != user_id and u['username'].lower() == u_clean.lower():
            raise ValidationError(f"Username '{u_clean}' is already taken.")

    if role not in ROLES:
        raise ValidationError(f"Role must be one of: {', '.join(ROLES)}.")

    # Block demoting the last Admin (FR-05)
    if existing['role'] == 'Admin' and role != 'Admin':
        admin_count = sum(1 for u in users if u['role'] == 'Admin')
        if admin_count <= 1:
            raise RuleError("Cannot demote the last remaining Admin account.")

    fn_clean = require_text(full_name, "Full Name")

    changes = {
        'username': u_clean,
        'role': role,
        'full_name': fn_clean
    }
    if password and str(password).strip():
        if len(str(password).strip()) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        changes['password'] = str(password).strip()

    update('users', 'user_id', user_id, changes)


def delete_user(user_id, acting_user):
    """Delete user, preventing deletion of last Admin or referenced users (FR-05)."""
    if not can(acting_user['role'], 'manage_users'):
        raise RuleError("Only Admin can delete users.")

    users = get_rows('users')
    target = next((u for u in users if u['user_id'] == user_id), None)
    if not target:
        raise ValidationError(f"User {user_id} not found.")

    if target['role'] == 'Admin':
        admin_count = sum(1 for u in users if u['role'] == 'Admin')
        if admin_count <= 1:
            raise RuleError("Cannot delete the last remaining Admin account.")

    # Block delete if referenced in jobs, payments, or status_log
    for j in get_rows('jobs'):
        if j.get('technician_id') == user_id or j.get('received_by') == user_id:
            raise RuleError(f"User is referenced by Job {j['job_id']} and cannot be deleted.")

    for p in get_rows('payments'):
        if p.get('received_by') == user_id:
            raise RuleError(f"User is referenced by Payment {p['payment_id']} and cannot be deleted.")

    for l in get_rows('status_log'):
        if l.get('changed_by') == user_id:
            raise RuleError(f"User is referenced by Status Log {l['log_id']} and cannot be deleted.")

    if any(p.get('user_id') == user_id for p in get_rows('profiles')):
        delete('profiles', 'user_id', user_id)

    delete('users', 'user_id', user_id)


def _find_customer_by_name(full_name):
    """Return the most recent customer record matching a full name."""
    name = str(full_name or '').strip().lower()
    if not name:
        return None
    for c in reversed(get_rows('customers')):
        if c.get('name', '').strip().lower() == name:
            return c
    return None


def _get_profile_row(user_id):
    """Return the dedicated profile row for a user, if one exists."""
    for p in get_rows('profiles'):
        if p.get('user_id') == user_id:
            return p
    return None


def _save_profile_row(user_id, contact_no='', email='', address=''):
    """Insert or update the dedicated profile row for any role."""
    values = {
        'contact_no': str(contact_no or '').strip(),
        'email': str(email or '').strip(),
        'address': str(address or '').strip(),
    }
    if _get_profile_row(user_id):
        update('profiles', 'user_id', user_id, values)
    else:
        insert('profiles', {'user_id': user_id, **values})


def get_user_profile(user_id, username=None):
    """Retrieve full profile details for any role (customer registry or profile store)."""
    users = get_rows('users')
    target = None
    if username:
        target = next((u for u in users if u['username'].lower() == str(username).lower()), None)
    if not target and user_id:
        target = next((u for u in users if u['user_id'] == user_id), None)
    if not target:
        return None

    profile = {
        'user_id': target['user_id'],
        'username': target['username'],
        'role': target['role'],
        'full_name': target['full_name'],
        'contact_no': '',
        'email': '',
        'address': ''
    }

    # Customer accounts keep the customer registry as their source of truth.
    if target['role'] == 'Customer':
        customer = _find_customer_by_name(target['full_name'])
        if customer:
            profile['contact_no'] = customer.get('contact_no', '')
            profile['email'] = customer.get('email', '')
            profile['address'] = customer.get('address', '')
            return profile

    # Staff/Admin (and customers without a registry record) use the profile store.
    profile_row = _get_profile_row(target['user_id'])
    if profile_row:
        profile['contact_no'] = profile_row.get('contact_no', '')
        profile['email'] = profile_row.get('email', '')
        profile['address'] = profile_row.get('address', '')

    return profile


def update_profile(user_id, full_name, contact_no=None, email=None, address=None, current_password=None, new_password=None, confirm_password=None, username=None):
    """
    Self-service profile and security update.
    Allows changing full name, linked contact details, and account password.
    """
    users = get_rows('users')
    target = None
    if username:
        target = next((u for u in users if u['username'].lower() == str(username).lower()), None)
    if not target and user_id:
        target = next((u for u in users if u['user_id'] == user_id), None)
    if not target:
        raise ValidationError(f"User {user_id or username} not found.")

    user_id = target['user_id']

    fn_clean = require_text(full_name, "Full Name")

    # If updating password
    if new_password and str(new_password).strip():
        np = str(new_password).strip()
        cp = str(confirm_password or "").strip()
        cur_p = str(current_password or "").strip()

        if not cur_p:
            raise ValidationError("Current password is required to change password.")
        if target['password'] != cur_p:
            raise ValidationError("Current password does not match.")
        if len(np) < 8:
            raise ValidationError("New password must be at least 8 characters.")
        if np != cp:
            raise ValidationError("New passwords do not match.")

        target['password'] = np

    old_name = target['full_name']
    target['full_name'] = fn_clean

    is_customer = (target['role'] == 'Customer')
    linked_customer = None
    if is_customer:
        linked_customer = _find_customer_by_name(old_name) or _find_customer_by_name(fn_clean)

    profile_row = _get_profile_row(user_id)

    # Resolve omitted values from the existing profile/customer record.
    if is_customer and linked_customer:
        current_contact = linked_customer.get('contact_no', '')
        current_email = linked_customer.get('email', '')
        current_address = linked_customer.get('address', '')
    elif profile_row:
        current_contact = profile_row.get('contact_no', '')
        current_email = profile_row.get('email', '')
        current_address = profile_row.get('address', '')
    elif linked_customer:
        current_contact = linked_customer.get('contact_no', '')
        current_email = linked_customer.get('email', '')
        current_address = linked_customer.get('address', '')
    else:
        current_contact = current_email = current_address = ''

    contact_clean = str(current_contact if contact_no is None else contact_no).strip()
    if contact_clean:
        contact_clean = valid_contact(contact_clean, "Contact number")

    email_clean = str(current_email if email is None else email).strip()
    if email_clean:
        email_clean = valid_email(email_clean, "Email address")
        excluded_customer_id = linked_customer.get('customer_id') if linked_customer else None
        if any(
            c.get('customer_id') != excluded_customer_id
            and c.get('email', '').strip().lower() == email_clean.lower()
            for c in get_rows('customers')
        ):
            raise ValidationError("Email address is already registered.")
        if any(
            p.get('user_id') != user_id
            and p.get('email', '').strip().lower() == email_clean.lower()
            for p in get_rows('profiles')
        ):
            raise ValidationError("Email address is already registered.")

    address_clean = str(current_address if address is None else address).strip()

    update('users', 'user_id', user_id, {
        'full_name': target['full_name'],
        'password': target['password']
    })

    # Persist contact details for every role, not just customers.
    _save_profile_row(user_id, contact_clean, email_clean, address_clean)

    # Keep the customer registry in sync for customer accounts only.
    if is_customer:
        from logic.customers import ensure_customer_record
        if linked_customer:
            update('customers', 'customer_id', linked_customer['customer_id'], {
                'name': fn_clean,
                'contact_no': contact_clean,
                'email': email_clean,
                'address': address_clean
            })
        else:
            ensure_customer_record(fn_clean, contact_clean, email_clean, address_clean)

    # If full name changed, update customer_name in jobs table
    if old_name.strip().lower() != fn_clean.strip().lower():
        for j in get_rows('jobs'):
            if j.get('customer_name', '').strip().lower() == old_name.strip().lower():
                update('jobs', 'job_id', j['job_id'], {'customer_name': fn_clean})

    return {
        'user_id': target['user_id'],
        'username': target['username'],
        'role': target['role'],
        'full_name': target['full_name']
    }


def split_full_name(full_name):
    """Split a full name into (first_name, last_name)."""
    full_name = (full_name or '').strip()
    if not full_name:
        return '', ''
    parts = full_name.split(' ', 1)
    return (parts[0], parts[1] if len(parts) > 1 else '')


def compose_full_name(first_name, last_name):
    """Combine first name and last name into full name string."""
    fn = (first_name or '').strip()
    ln = (last_name or '').strip()
    return f"{fn} {ln}".strip()


def compose_address(street='', unit='', city='', state='', postal_code=''):
    """Combine chopped address components into a single standard formatted address string."""
    parts = []
    for item in [street, unit, city, state, postal_code]:
        val = str(item or '').strip()
        if val:
            parts.append(val)
    return ", ".join(parts)


def parse_address(addr_str):
    """
    Parse an address string into component dictionary:
    {'street': ..., 'unit': ..., 'city': ..., 'state': ..., 'postal_code': ...}
    """
    res = {'street': '', 'unit': '', 'city': '', 'state': '', 'postal_code': ''}
    if not addr_str or not isinstance(addr_str, str):
        return res
    parts = [p.strip() for p in addr_str.split(',') if p.strip()]
    if len(parts) == 1:
        res['street'] = parts[0]
    elif len(parts) == 2:
        res['street'] = parts[0]
        res['city'] = parts[1]
    elif len(parts) == 3:
        res['street'] = parts[0]
        res['city'] = parts[1]
        res['postal_code'] = parts[2]
    elif len(parts) == 4:
        res['street'] = parts[0]
        res['city'] = parts[1]
        res['state'] = parts[2]
        res['postal_code'] = parts[3]
    elif len(parts) >= 5:
        res['street'] = parts[0]
        res['unit'] = parts[1]
        res['city'] = parts[2]
        res['state'] = parts[3]
        res['postal_code'] = ", ".join(parts[4:])
    return res
