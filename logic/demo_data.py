"""Idempotent demo data seeding for the local CSV database."""

import datetime
from decimal import Decimal

from storage import get_rows, insert, next_id


PARTS = [
    ("SSD 512GB NVMe", "12", "3"),
    ("Laptop Battery Pack", "8", "2"),
    ("LCD Panel 15.6 inch", "5", "1"),
    ("Thermal Paste Kit", "20", "5"),
    ("USB-C Charging Port", "15", "4"),
]

ACCOUNT_SPECS = [
    ("demo_staff", "Demo Staff", "Staff", "demo_staff@flux.local", "09170000001"),
    ("frontdesk", "Front Desk Demo", "Staff", "frontdesk@flux.local", "09170000002"),
    ("benchtech", "Bench Technician", "Technician", "benchtech@flux.local", "09170000003"),
    ("microsolder", "Microsoldering Technician", "Technician", "microsolder@flux.local", "09170000004"),
    ("demo_customer01", "Mia Santos", "Customer", "mia.santos@demo.local", "09170000005"),
    ("demo_customer02", "Noah Reyes", "Customer", "noah.reyes@demo.local", "09170000006"),
    ("demo_customer03", "Ava Cruz", "Customer", "ava.cruz@demo.local", "09170000007"),
    ("demo_customer04", "Liam Garcia", "Customer", "liam.garcia@demo.local", "09170000008"),
]

JOBS = [
    {
        "customer_index": 0,
        "brand": "Lenovo",
        "model": "ThinkPad T14",
        "serial_no": "DEMO-THINKPAD-001",
        "problem": "Laptop is slow and requires an SSD upgrade.",
        "service_index": 6,
        "part_name": "SSD 512GB NVMe",
        "part_qty": "1",
        "diagnosis": "Existing storage is healthy but near capacity.",
        "notes": "Customer approved the upgrade estimate.",
    },
    {
        "customer_index": 1,
        "brand": "Dell",
        "model": "Inspiron 15",
        "serial_no": "DEMO-DELL-002",
        "problem": "Battery drains quickly and shuts down without the charger.",
        "service_index": 4,
        "part_name": "Laptop Battery Pack",
        "part_qty": "1",
        "diagnosis": "Battery health is below replacement threshold.",
        "notes": "Run charge and discharge verification after installation.",
    },
    {
        "customer_index": 2,
        "brand": "ASUS",
        "model": "VivoBook 14",
        "serial_no": "DEMO-ASUS-003",
        "problem": "Display has flickering and intermittent blackouts.",
        "service_index": 3,
        "part_name": "LCD Panel 15.6 inch",
        "part_qty": "1",
        "diagnosis": "Panel failure confirmed; cable passed continuity test.",
        "notes": "Awaiting customer approval before replacement.",
    },
    {
        "customer_index": 3,
        "brand": "Acer",
        "model": "Aspire 5",
        "serial_no": "DEMO-ACER-004",
        "problem": "Device overheats during normal use.",
        "service_index": 8,
        "part_name": "Thermal Paste Kit",
        "part_qty": "1",
        "diagnosis": "Thermal paste is dry and heatsink is heavily dusted.",
        "notes": "Cleaned fan and scheduled post-service stress test.",
    },
    {
        "customer_email": "mia.santos@demo.local",
        "brand": "Apple",
        "model": "MacBook Air M1",
        "serial_no": "DEMO-MACBOOK-005",
        "problem": "No power after liquid exposure.",
        "service_index": 2,
        "part_name": "USB-C Charging Port",
        "part_qty": "1",
        "target_status": "Diagnosing",
    },
    {
        "customer_email": "noah.reyes@demo.local",
        "brand": "HP",
        "model": "Pavilion 15",
        "serial_no": "DEMO-HP-006",
        "problem": "Keyboard keys are not responding.",
        "service_index": 5,
        "part_name": None,
        "part_qty": "0",
        "target_status": "Under Repair",
    },
    {
        "customer_email": "ava.cruz@demo.local",
        "brand": "Lenovo",
        "model": "IdeaPad 3",
        "serial_no": "DEMO-LENOVO-007",
        "problem": "Operating system corruption and boot errors.",
        "service_index": 1,
        "part_name": None,
        "part_qty": "0",
        "target_status": "Completed",
    },
    {
        "customer_email": "liam.garcia@demo.local",
        "brand": "Nintendo",
        "model": "Switch OLED",
        "serial_no": "DEMO-SWITCH-008",
        "problem": "Charging port is loose and intermittent.",
        "service_index": 2,
        "part_name": "USB-C Charging Port",
        "part_qty": "1",
        "target_status": "Released",
    },
]


def seed_demo_data():
    """Fill sparse local tables without creating services or invalid references."""
    users = get_rows("users")
    customers = get_rows("customers")
    services = get_rows("services")
    if not users or not customers or not services:
        return

    operators = [u for u in users if u.get("role") in ("Admin", "Staff")]
    technicians = [u for u in users if u.get("role") == "Technician"]
    if not operators:
        return

    for username, full_name, role, email, contact in ACCOUNT_SPECS:
        if any(u.get("username", "").lower() == username.lower() for u in users):
            continue
        user_id = next_id("U", 3)
        insert("users", {
            "user_id": user_id,
            "username": username,
            "password": "DemoPass123",
            "role": role,
            "full_name": full_name,
        })
        insert("profiles", {
            "user_id": user_id,
            "contact_no": contact,
            "email": email,
            "address": "Demo Address, Metro Manila, 1000",
        })
        if role == "Customer":
            customer_id = next_id("C", 3)
            insert("customers", {
                "customer_id": customer_id,
                "name": full_name,
                "contact_no": contact,
                "email": email,
                "address": "Demo Address, Metro Manila, 1000",
            })

    users = get_rows("users")
    customers = get_rows("customers")
    operators = [u for u in users if u.get("role") in ("Admin", "Staff")]
    technicians = [u for u in users if u.get("role") == "Technician"]

    for name, quantity, threshold in PARTS:
        if not any(p.get("name", "").strip().lower() == name.lower() for p in get_rows("parts")):
            insert("parts", {
                "part_id": next_id("P", 3),
                "name": name,
                "quantity": quantity,
                "unit_price": "500.00",
                "low_stock_threshold": threshold,
            })

    service_ids = [s["service_id"] for s in services]
    parts_by_name = {
        p["name"].strip().lower(): p for p in get_rows("parts")
    }
    operator = operators[0]
    technician = technicians[0] if technicians else {}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    customers_by_email = {
        c.get("email", "").strip().lower(): c for c in customers
    }
    for spec in JOBS:
        customer = (
            customers[spec["customer_index"]]
            if "customer_index" in spec and spec["customer_index"] < len(customers)
            else customers_by_email.get(spec.get("customer_email", "").lower())
        )
        if not customer:
            continue
        if any(j.get("serial_no") == spec["serial_no"] for j in get_rows("jobs")):
            continue

        job_id = next_id("J", 4)
        insert("jobs", {
            "job_id": job_id,
            "customer_id": customer["customer_id"],
            "technician_id": technician.get("user_id", ""),
            "received_by": operator["user_id"],
            "device_type": "Laptop",
            "brand": spec["brand"],
            "model": spec["model"],
            "serial_no": spec["serial_no"],
            "problem": spec["problem"],
            "device_condition": "Normal cosmetic wear, no major chassis cracks",
            "priority": "Normal",
            "date_received": now,
            "est_completion": "",
            "diagnosis": spec.get("diagnosis", "Bench inspection completed and fault isolated."),
            "notes": spec.get("notes", "Demo repair record for reporting and workflow testing."),
            "cancel_reason": "",
        })

        service_id = service_ids[spec["service_index"] % len(service_ids)]
        service = next(s for s in services if s["service_id"] == service_id)
        insert("job_services", {
            "job_id": job_id,
            "service_id": service_id,
            "price": service["price"],
        })

        part = (
            parts_by_name.get(spec["part_name"].lower())
            if spec.get("part_name")
            else None
        )
        if part:
            insert("job_parts", {
                "job_id": job_id,
                "part_id": part["part_id"],
                "quantity_used": spec["part_qty"],
                "unit_price": part["unit_price"],
            })

        status_steps = {
            "Received": ["Received"],
            "Diagnosing": ["Received", "Diagnosing"],
            "Waiting for Parts": ["Received", "Diagnosing", "Waiting for Parts"],
            "Under Repair": ["Received", "Diagnosing", "Under Repair"],
            "Completed": ["Received", "Diagnosing", "Under Repair", "Completed"],
            "Released": ["Received", "Diagnosing", "Under Repair", "Completed", "Released"],
        }
        for status in status_steps.get(spec.get("target_status", "Received"), ["Received"]):
            insert("status_log", {
                "log_id": next_id("L", 5),
                "job_id": job_id,
                "status": status,
                "changed_at": now,
                "changed_by": technician.get("user_id", operator["user_id"]) if status != "Received" else operator["user_id"],
            })

        service_total = Decimal(service["price"])
        part_total = Decimal(part["unit_price"]) * int(spec["part_qty"]) if part else Decimal("0.00")
        total = service_total + part_total
        if total > Decimal("0.00") and spec.get("target_status") in ("Completed", "Released"):
            insert("payments", {
                "payment_id": next_id("PAY", 4),
                "job_id": job_id,
                "amount": f"{total:.2f}",
                "method": "GCash" if spec.get("target_status") == "Completed" else "Cash",
                "payment_date": now,
                "received_by": operator["user_id"],
            })
