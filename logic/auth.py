from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id
from models import ROLES
from utils import require_text, valid_contact

# Permission matrix based on §2.1
PERMISSIONS = {
    'Admin': {
        'manage_users': True,
        'manage_services': True,
        'manage_parts': True,
        'customers': True,
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
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'role': user['role'],
            'full_name': user['full_name']
        }
    raise ValidationError("Invalid username, email, or password.")


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
            'full_name': u['full_name']
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


def register_user(username, password, confirm_password, full_name, contact_no='', email='', address='', role="Customer"):
    """
    Self-registration: Always creates account with 'Customer' role by default.
    Elevated system roles (Admin, Staff, Technician) can only be assigned by Admins.
    Stores personal contact details and delivery/service address in linked customer profile.
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

    delete('users', 'user_id', user_id)


def get_user_profile(user_id, username=None):
    """Retrieve full profile details including linked customer contact info."""
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

    # Fetch customer record if present
    for c in get_rows('customers'):
        if c['name'].strip().lower() == target['full_name'].strip().lower():
            profile['contact_no'] = c.get('contact_no', '')
            profile['email'] = c.get('email', '')
            profile['address'] = c.get('address', '')
            break

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

    update('users', 'user_id', user_id, {
        'full_name': target['full_name'],
        'password': target['password']
    })

    # Sync with customers table
    from logic.customers import ensure_customer_record
    found_customer = False
    for c in get_rows('customers'):
        if c['name'].strip().lower() in (old_name.strip().lower(), fn_clean.strip().lower()):
            cust_updates = {'name': fn_clean}
            if contact_no is not None:
                c_clean = str(contact_no).strip()
                if c_clean:
                    c_clean = valid_contact(c_clean, "Contact number")
                cust_updates['contact_no'] = c_clean
            if email is not None:
                cust_updates['email'] = str(email).strip()
            if address is not None:
                cust_updates['address'] = str(address).strip()
            update('customers', 'customer_id', c['customer_id'], cust_updates)
            found_customer = True
            break

    if not found_customer and target['role'] == 'Customer':
        ensure_customer_record(fn_clean, contact_no or '', email or '', address or '')

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
