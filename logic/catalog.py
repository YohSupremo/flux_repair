from errors import ValidationError, RuleError
from storage import get_rows, insert, update, delete, next_id
from utils import require_text, parse_money
from logic.auth import can

SAMPLE_SERVICES = [
    ("Diagnostic", "Initial hardware fault diagnosis and board-level inspection", "0.00"),
    ("OS Reinstallation", "Clean OS install with latest drivers and baseline updates", "500.00"),
    ("Virus Removal", "Malware, ransomware, and spyware scrubbing with registry clean", "600.00"),
    ("Screen Replacement", "Precision LCD/OLED panel replacement with color calibration", "2500.00"),
    ("Battery Replacement", "Original-spec cell installation with health & load verification", "1800.00"),
    ("Keyboard Replacement", "Chassis-level keyboard replacement with backlight testing", "1200.00"),
    ("Hardware Upgrade (RAM/SSD)", "High-speed NVMe or RAM installation and thermal benchmarking", "800.00"),
    ("Data Backup", "Bit-for-bit drive clone or selective archive to secure storage", "700.00"),
    ("Cleaning / Thermal Paste", "Ultrasonic dust removal and liquid metal / high-viscosity paste rework", "650.00"),
]


def seed_sample_services():
    """Seed the 9 standard repair services on first run (FR-22)."""
    services = get_rows('services')
    if not services:
        for name, desc, price in SAMPLE_SERVICES:
            sid = next_id('S', 3)
            insert('services', {
                'service_id': sid,
                'name': name,
                'description': desc,
                'price': price
            })


def list_services():
    """Return all catalog services."""
    return list(get_rows('services'))


def get_service(service_id):
    """Retrieve service by ID."""
    for s in get_rows('services'):
        if s['service_id'] == service_id:
            return s
    return None


def add_service(name, description, price, acting_user):
    """Add a service to catalog (Admin only, FR-21)."""
    if not can(acting_user['role'], 'manage_services'):
        raise RuleError("Only Admin can manage service catalog.")

    s_name = require_text(name, "Service name")
    s_desc = require_text(description, "Description")
    s_price = parse_money(price, "Service price")

    # Reject duplicate service names (FR-55)
    for s in get_rows('services'):
        if s['name'].lower() == s_name.lower():
            raise ValidationError(f"A service named '{s_name}' already exists.")

    sid = next_id('S', 3)
    row = {
        'service_id': sid,
        'name': s_name,
        'description': s_desc,
        'price': f"{s_price:.2f}"
    }
    insert('services', row)
    return row


def edit_service(service_id, name, description, price, acting_user):
    """Edit service in catalog (Admin only)."""
    if not can(acting_user['role'], 'manage_services'):
        raise RuleError("Only Admin can manage service catalog.")

    existing = get_service(service_id)
    if not existing:
        raise ValidationError(f"Service {service_id} not found.")

    s_name = require_text(name, "Service name")
    s_desc = require_text(description, "Description")
    s_price = parse_money(price, "Service price")

    for s in get_rows('services'):
        if s['service_id'] != service_id and s['name'].lower() == s_name.lower():
            raise ValidationError(f"A service named '{s_name}' already exists.")

    changes = {
        'name': s_name,
        'description': s_desc,
        'price': f"{s_price:.2f}"
    }
    update('services', 'service_id', service_id, changes)


def delete_service(service_id, acting_user):
    """Delete service; blocked if attached to any job order (FR-21)."""
    if not can(acting_user['role'], 'manage_services'):
        raise RuleError("Only Admin can manage service catalog.")

    existing = get_service(service_id)
    if not existing:
        raise ValidationError(f"Service {service_id} not found.")

    # Check if used in job_services
    for js in get_rows('job_services'):
        if js['service_id'] == service_id:
            raise RuleError(
                f"Service {service_id} cannot be deleted because it is linked to Job {js['job_id']}."
            )

    delete('services', 'service_id', service_id)
