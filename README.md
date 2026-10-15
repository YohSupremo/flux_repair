# FLUX Repair Co. — Computer & Laptop Repair Service System

**Course:** IT Professional Elective 1 (ITEP310-T)  
**Platform:** Python 3.8+ / Tkinter Desktop Application  
**Persistence:** Local UTF-8 CSV Files in `data/`  
**Dependencies:** Standard Python Library Only (No `pip install`)

---

## 1. Quick Start

### Launch Application
```bash
python main.py
```

### Initial Administrator Login
On first boot, the system auto-initializes the database tables and creates the master administrator account:
- **Username:** `admin`
- **Password:** `admin123`

---

## 2. Architecture & Layer Decoupling

Following the implementation plan, the system strictly enforces 3-tier separation:

```
circuitcare/
├── main.py                 # Application bootstrapper
├── config.py               # Paths, date formats, PHP (₱) currency constants
├── errors.py               # ValidationError, RuleError, StorageError
├── models.py               # CSV table schemas, role constants, state machine transitions
├── utils.py                # Regex validators, Decimal currency formatters
├── storage.py              # Atomic CSV load/save, counters.csv ID generator, backups
├── logic/                  # Pure business rules (ZERO Tkinter imports, fully unit-tested)
│   ├── auth.py             # Credentials validation, role permissions matrix, user CRUD
│   ├── customers.py        # Customer directory, contact validation, repair history
│   ├── catalog.py          # Repair service catalog, FR-22 standard service seeding
│   ├── parts.py            # Inventory management, threshold tracking, stock deduction
│   ├── jobs.py             # Job intake, FR-28a status state machine, technician assignments
│   ├── billing.py          # Decimal bill computation, multi-tender payments, cash change
│   └── reports.py          # Real-time status distribution, sales reporting, CSV exports
├── gui/                    # Presentation Layer (Tkinter + ttk with Cleanroom Atelier theme)
│   ├── theme.py            # FLUX Repair Co. Cleanroom design tokens & ttk styles
│   ├── widgets.py          # Reusable tables, cards, @guard exception decorator
│   ├── login.py            # Masked login card (FR-01, FR-04)
│   ├── main_menu.py        # Role-based sidebar, live telemetry clock, dashboard homepage
│   ├── customers_ui.py     # Customer management, live search, repair history dossier
│   ├── catalog_ui.py       # Services table, price adjustments
│   ├── parts_ui.py         # Hardware inventory, stock adjustments, low-stock alerts
│   ├── job_form.py         # Full intake modal (accessories, customer picker, auto receipt)
│   ├── job_details_ui.py   # Comprehensive repair workbench dossier & status stepper
│   ├── jobs_ui.py          # Master ticket registry, status filter tabs, search
│   ├── billing_ui.py       # Payment modal, cash change calculator
│   ├── receipt_ui.py       # Monospace receipt viewer with .txt export
│   ├── reports_ui.py       # Dashboard telemetry, date range sales, CSV exports
│   └── users_ui.py         # Admin user accounts manager
├── data/                   # Auto-created UTF-8 CSV database files
├── receipts/               # Auto-saved intake and official text receipts
├── exports/                # Exported CSV and TXT reports
├── backups/                # Full timestamped data directory snapshots
└── tests/                  # Unit tests (runnable with `python -m unittest`)
```

---

## 3. User Roles & Permissions (§2.1)

| Function | Admin | Staff | Technician |
|---|---|---|---|
| User Accounts Management | ✔ | – | – |
| Services & Parts Management | ✔ | – | – |
| Customer Directory & History | ✔ | ✔ | – |
| Job Intake & Tech Assignment | ✔ | ✔ | – |
| Status Progression | ✔ | ✔ | ✔ (own jobs only) |
| Diagnostic Verdict & Notes | ✔ | – | ✔ (own jobs only) |
| Billing & Device Release | ✔ | ✔ | – |
| Reports & Backups | ✔ | ✔ (Reports) | – |

---

## 4. Running Tests

Run the automated test suite verifying storage atomicity, business rules, and state machine transitions:

```bash
python -m unittest discover -s tests
```
