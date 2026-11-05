from errors import RuleError, ValidationError
from logic.auth import seed_default_admin
from logic.catalog import seed_sample_services
from logic.customers import ensure_customer_record
from logic.jobs import create_job
from storage import get_rows, init_storage
from utils import require_text


SERVICE_NAME_MAP = {
    "Screens & Displays": "Screen Replacement",
    "Screens and Displays": "Screen Replacement",
    "Liquid Damage Recovery": "Diagnostic",
    "Board-Level Micro-Soldering": "Diagnostic",
    "Batteries and Power Systems": "Battery Replacement",
    "Batteries & Power Systems": "Battery Replacement",
    "Dedicated Data Recovery": "Data Backup",
    "Retro Audio & Consoles": "Diagnostic",
    "Retro Audio and Consoles": "Diagnostic",
}


def submit_public_booking(name, contact, device_description, service_title):
    """Create a customer and an initial repair job from the public booking form."""
    init_storage()
    seed_default_admin()
    seed_sample_services()

    customer_name = require_text(name, "Your name")
    customer_contact = require_text(contact, "Email or phone number")
    device = require_text(device_description, "Device model and issue description")
    customer = ensure_customer_record(customer_name, contact_no=customer_contact)

    staff_user = next(
        (u for u in get_rows("users") if u["role"] in ("Admin", "Staff")),
        None
    )
    if not staff_user:
        raise RuleError("No workshop staff account is available to receive this request.")

    service_name = SERVICE_NAME_MAP.get(service_title, "Diagnostic")
    service = next(
        (s for s in get_rows("services") if s["name"] == service_name),
        None
    )
    if not service:
        raise ValidationError("The selected service category is unavailable.")

    job_id = create_job(
        {
            "customer_id": customer["customer_id"],
            "device_type": "Laptop",
            "brand": "Not specified",
            "model": device,
            "serial_no": f"ONLINE-{customer['customer_id']}",
            "problem": device,
            "device_condition": "To be inspected",
            "priority": "Normal",
            "est_completion": "",
            "technician_id": "",
        },
        [],
        [service["service_id"]],
        staff_user,
    )
    return job_id
