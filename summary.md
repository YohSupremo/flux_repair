# Computer & Laptop Repair Service System
## Implementation Progress & Functional Requirements Checklist

**Project:** FLUX Repair Co. / CircuitCare  
**Course:** IT Professional Elective 1 (ITEP310-T)  
**Specification:** `Functional_Requirements.md` (Section 3)  
**Overall Completion:** **100% (69 / 69 Functional Requirements Completed)**

---

### Progress by Category Summary

| Category | Total Items | Completed | Percentage |
|---|:---:|:---:|:---:|
| **3.1 Authentication & User Management** | 7 | 7 | 100% |
| **3.2 Customer Management** | 6 | 6 | 100% |
| **3.3 Device & Job Order (Intake)** | 9 | 9 | 100% |
| **3.4 Service Catalog & Pricing** | 6 | 6 | 100% |
| **3.5 Technician Assignment & Repair Tracking** | 12 | 12 | 100% |
| **3.6 Parts & Inventory (Module)** | 5 | 5 | 100% |
| **3.7 Billing & Payment** | 6 | 6 | 100% |
| **3.8 Reports & Analytics** | 4 | 4 | 100% |
| **3.9 Data Management & Persistence** | 4 | 4 | 100% |
| **3.10 Validation & Error Handling** | 5 | 5 | 100% |
| **3.11 GUI Architecture & Design** | 5 | 5 | 100% |
| **TOTAL** | **69** | **69** | **100%** |

---

### Priority Breakdown

| Priority Level | Total Items | Completed | Fulfillment |
|---|:---:|:---:|:---:|
| **Must Have (M)** | 42 | 42 | 100% |
| **Should Have (S)** | 21 | 21 | 100% |
| **Could Have (C)** | 6 | 6 | 100% |

---

## Detailed Requirements Checklist

### 3.1 Authentication & User Management
- [x] **FR-01** `[M]` The system displays a login window with username and password entry. (`gui/login.py`)
- [x] **FR-02** `[M]` Validates credentials against stored user records and surfaces graphical error messages on failure. (`logic/auth.py`, `gui/login.py`)
- [x] **FR-03** `[M]` Opens role-customized dashboard/menu based on role: Admin, Staff, Technician, Customer. (`gui/main_menu.py`)
- [x] **FR-04** `[M]` Masks password field with `show="*"`. (`gui/login.py`)
- [x] **FR-05** `[S]` Admin can add, edit, and delete user accounts. Deletion of the last remaining Admin is blocked. (`logic/auth.py`, `gui/users_ui.py`)
- [x] **FR-05a** `[M]` Automatically seeds initial default Admin account if `users.csv` is empty and prompts for setup. (`storage.py`, `logic/auth.py`)
- [x] **FR-06** `[M]` Provides logout button returning immediately to the login window. (`gui/main_menu.py`)

### 3.2 Customer Management
- [x] **FR-07** `[M]` Adds customer with auto-generated ID (`C-XXXX`), full name, contact number, email, and address. (`logic/customers.py`, `gui/customers_ui.py`)
- [x] **FR-08** `[M]` Allows editing customer profile details. (`logic/customers.py`, `gui/customers_ui.py`)
- [x] **FR-09** `[S]` Deletes customer records with safety check: blocked if linked to any active or past job orders. (`logic/customers.py`)
- [x] **FR-10** `[M]` Displays all customer records in a table (`ttk.Treeview`). (`gui/customers_ui.py`)
- [x] **FR-11** `[M]` Real-time multi-field search filter by name, customer ID, or contact number. (`gui/customers_ui.py`)
- [x] **FR-12** `[S]` Dedicated customer repair history dossier modal (`CustomerHistoryModal`). (`gui/customers_ui.py`)

### 3.3 Device & Job Order (Intake)
- [x] **FR-13** `[M]` Generates job order with sequential ticket ID (`J-XXXX`), arrival timestamp, and initial status **Received**. (`logic/jobs.py`)
- [x] **FR-14** `[M]` Records customer, device type (Laptop, Desktop, All-in-One), brand, model, serial number, and accessories. (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-15** `[M]` Records customer's reported problem description. (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-16** `[S]` Records physical hardware condition on arrival (chassis wear, cracks, scratches). (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-17** `[S]` Records priority classification (**Normal** / **Urgent**). (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-18** `[S]` Records estimated completion target date. (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-19** `[S]` Generates viewable and exportable text intake receipt (`receipts/J-XXXX_intake.txt`). (`logic/jobs.py`, `gui/receipt_ui.py`)
- [x] **FR-20** `[M]` Blocks submission if required fields are missing. (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-20a** `[S]` Staff/Admin can modify intake details until job status is Completed. (`logic/jobs.py`)

### 3.4 Service Catalog & Pricing
- [x] **FR-21** `[M]` Admin can add, edit, and delete services (Service ID, name, description, price). Deletion blocked if referenced by existing jobs. (`logic/catalog.py`, `gui/catalog_ui.py`)
- [x] **FR-22** `[M]` Seeded default catalog: Diagnostic, OS Reinstallation, Virus Removal, Screen Replacement, Battery Replacement, Keyboard Replacement, Hardware Upgrade, Data Backup, Cleaning/Thermal Paste. (`data/services.csv`)
- [x] **FR-23** `[M]` Services are selectable via multi-select Listbox/modal and attachable to job orders. (`gui/job_form.py`, `gui/job_details_ui.py`)
- [x] **FR-24** `[M]` Supports attaching multiple services to a single job order. (`logic/jobs.py`, `gui/job_form.py`)
- [x] **FR-24a** `[M]` Services can be added/removed dynamically during repair lifecycle before completion; catalog price snapshot copied to job. (`logic/jobs.py`, `gui/job_details_ui.py`)
- [x] **FR-24b** `[S]` Custom job-specific service price overrides (e.g. specialized screen replacement pricing per laptop model). (`logic/jobs.py`)

### 3.5 Technician Assignment & Repair Tracking
- [x] **FR-25** `[M]` Staff/Admin can assign or reassign bench technicians (role Technician only) to jobs. (`logic/jobs.py`, `gui/job_details_ui.py`)
- [x] **FR-26** `[M]` Technicians automatically filtered to view only their assigned jobs. (`logic/jobs.py`, `gui/jobs_ui.py`)
- [x] **FR-27** `[M]` Technicians record root-cause diagnosis and detailed repair/bench notes per job. (`logic/jobs.py`, `gui/job_details_ui.py`)
- [x] **FR-27a** `[C]` Records cost quote and tracks customer repair approval notes after diagnostic inspection. (`logic/jobs.py`, `gui/job_details_ui.py`)
- [x] **FR-28** `[M]` Full workflow state machine: **Received → Diagnosing → Waiting for Parts → Under Repair → Completed → Released** (and **Cancelled**). (`models.py`, `logic/jobs.py`)
- [x] **FR-28a** `[M]` Strict transition validation rules; terminal states **Released** and **Cancelled** are immutable. (`models.py`, `logic/jobs.py`)
- [x] **FR-28b** `[S]` Cancellation requires reason, restores reserved parts inventory stock, and flags unrefunded balances. (`logic/jobs.py`)
- [x] **FR-29** `[M]` Audit trail logs every status transition with sequential log ID, timestamp, and actor ID into `status_log.csv`. (`logic/jobs.py`, `data/status_log.csv`)
- [x] **FR-30** `[M]` All jobs rendered in filterable `ttk.Treeview` with status pill tags. (`gui/jobs_ui.py`)
- [x] **FR-31** `[M]` Live search by Job Ticket ID, customer name, device brand/model, or serial number. (`gui/jobs_ui.py`)
- [x] **FR-31a** `[M]` Comprehensive repair dossier workbench displaying intake specs, services, parts, status history, ledger, and balance. (`gui/job_details_ui.py`)
- [x] **FR-32** `[C]` On-screen notification prompt upon marking job Completed instructing staff to contact customer. (`gui/job_details_ui.py`)

### 3.6 Parts & Inventory (Module)
- [x] **FR-33** `[S]` Hardware inventory stores Part ID (`P-XXXX`), component name, quantity in stock, unit price, and reorder threshold. (`data/parts.csv`, `logic/parts.py`)
- [x] **FR-33a** `[S]` Admin can add, edit, and delete parts (deletion prevented if part is allocated to any job). (`logic/parts.py`, `gui/parts_ui.py`)
- [x] **FR-34** `[S]` Allocating parts to a job automatically decrements stock; removing part returns quantity back to inventory. (`logic/parts.py`, `gui/job_details_ui.py`)
- [x] **FR-35** `[C]` Visual low-stock alert badges displayed in inventory workbench when stock ≤ threshold. (`gui/parts_ui.py`, `logic/parts.py`)
- [x] **FR-36** `[S]` Prevents part allocation if available quantity is less than requested quantity. (`logic/parts.py`)

### 3.7 Billing & Payment
- [x] **FR-37** `[M]` Computes invoice totals in real-time using `Decimal('0.01')`: `Services Total + Parts Total`. (`logic/billing.py`)
- [x] **FR-38** `[S]` Supports downpayments / retainers (supports initial intake deposits even before diagnostic completion). (`logic/billing.py`, `gui/billing_ui.py`, `gui/job_form.py`)
- [x] **FR-39** `[M]` Itemized payment ledger: amount, payment method (**Cash / GCash / Card**), date/time, and cashier ID. Supports multiple installments. (`logic/billing.py`, `gui/billing_ui.py`)
- [x] **FR-40** `[M]` Computes remaining balance due and cash change for over-tendered cash payments. (`logic/billing.py`, `gui/billing_ui.py`)
- [x] **FR-41** `[M]` Generates official invoice / final statement (`receipts/J-XXXX_official.txt`) and modal viewer. (`logic/billing.py`, `gui/receipt_ui.py`)
- [x] **FR-42** `[M]` Release gatekeeper: Job can only be marked **Released** when status is Completed AND balance is exactly `₱0.00`. (`logic/jobs.py`)

### 3.8 Reports & Analytics
- [x] **FR-43** `[S]` Visual analytics dashboard summarizing real-time ticket volume by status. (`gui/reports_ui.py`, `logic/reports.py`)
- [x] **FR-44** `[S]` Daily and monthly financial sales revenue reports broken down by payment methods. (`gui/reports_ui.py`, `logic/reports.py`)
- [x] **FR-45** `[S]` Dedicated pending / active unfinished jobs report. (`gui/reports_ui.py`, `logic/reports.py`)
- [x] **FR-46** `[C]` One-click report export to formatted `.txt` and `.csv` files. (`logic/reports.py`, `gui/reports_ui.py`)

### 3.9 Data Management & Persistence
- [x] **FR-47** `[M]` All entities persisted to standard local CSV files in `data/` using standard library file I/O. (`storage.py`)
- [x] **FR-48** `[M]` In-memory caching with automatic table loading upon application bootstrap. (`storage.py`)
- [x] **FR-49** `[M]` Automatic directory and missing table initialization on first boot. (`storage.py`)
- [x] **FR-50** `[C]` One-click manual backup copying entire `data/` store to timestamped `backups/backup_YYYYMMDD_HHMMSS/`. (`storage.py`, `gui/reports_ui.py`)

### 3.10 Validation & Error Handling
- [x] **FR-51** `[M]` Rigorous type and range validation: non-negative decimals for currency, positive integer quantities, phone number regex, email regex. (`utils.py`, `errors.py`)
- [x] **FR-52** `[M]` Graphical modal alerts (`showerror`, `showwarning`, `showinfo`) replace terminal crashes via `@guard` decorator. (`gui/widgets.py`)
- [x] **FR-53** `[M]` Destructive actions (deletions, job cancellation, logout) require explicit confirmation dialog (`askyesno`). (`gui/`)
- [x] **FR-54** `[M]` Atomic file persistence: writes to `.tmp` file and atomically replaces destination to guarantee zero file corruption. (`storage.py`)
- [x] **FR-55** `[M]` Unique auto-incrementing ID generators (`counters.csv`); IDs are never recycled; uniqueness enforced on usernames and service names. (`storage.py`, `logic/auth.py`, `logic/catalog.py`)

### 3.11 GUI Architecture & Design
- [x] **FR-56** `[M]` 100% desktop GUI built in Python 3 + Tkinter; zero terminal prompts required during operation. (`app.py`, `gui/`)
- [x] **FR-57** `[M]` Role-gated left sidebar navigation: Customers, Jobs, Catalog, Inventory, Reports, Users. (`gui/main_menu.py`)
- [x] **FR-58** `[M]` Strict widget adherence: `Entry`, `Text`, `ttk.Combobox`, `Checkbutton`, `Spinbox`, `Frame`, `Label`, `Button`, `Toplevel`, `ttk.Treeview`. (`gui/widgets.py`)
- [x] **FR-59** `[M]` All record grids rendered with scrollbars and alternating row striping. (`gui/widgets.py`)
- [x] **FR-60** `[S]` Consistent design language, emerald/slate palette, clear button affordance, and hover micro-animations. (`gui/theme.py`, `gui/widgets.py`)
