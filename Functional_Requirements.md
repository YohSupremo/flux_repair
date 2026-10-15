# Computer & Laptop Repair Service System
## Functional Requirements Specification

**Course:** IT Professional Elective 1 (ITEP310-T)
**Language / GUI:** Python 3 + Tkinter (desktop GUI, no terminal interaction)
**Storage:** Local CSV files (UTF-8) in a `data/` folder using Python file I/O; TXT for receipts and exports

---

## 1. Introduction

### 1.1 Purpose
This document lists what the Computer & Laptop Repair Service System must do. The system helps a repair shop record customers, receive devices for repair, assign technicians, track repair progress, and issue billing.

### 1.2 Scope
A standalone desktop application with a graphical interface. All interaction (input, buttons, tables, messages) happens through windows. The terminal is only used to launch the program.

### 1.3 Technical Constraints (based on the lesson)
| Constraint | Detail |
|---|---|
| GUI library | Tkinter (`tkinter`, `tkinter.messagebox`, `tkinter.ttk` for tables/combobox) |
| Data storage | File I/O (`open()`, `read()`, `write()`, `os` module) |
| Data structures | Lists, tuples, dictionaries for records |
| Error handling | `try / except / finally` on all file and input operations |
| Code organization | Functions + modules (e.g., `gui.py`, `storage.py`, `models.py`) |
| Python version | Python 3, standard library only. Lesson examples use Python 2 syntax (`Tkinter`, `print x`); convert to `tkinter`, `print(x)`. |

### 1.4 Definitions
| Term | Meaning |
|---|---|
| Job Order / Ticket | A repair request for one device |
| Technician | Staff who diagnoses and repairs devices |
| Service | A repair task with a default price (e.g., OS reinstall); adjustable per job (FR-24b) |
| Balance | Total − payments received |
| Change | Cash tendered − amount due (cash only) |
| Conventions | Dates `YYYY-MM-DD HH:MM`; currency PHP (₱), 2 decimals; IDs prefixed (C-001, J-0001) |

---

## 2. User Roles

| Role | Description |
|---|---|
| **Admin** | Manages users, services, prices, and views all reports |
| **Front Desk / Staff** | Registers customers, creates job orders, processes payments, releases devices |
| **Technician** | Views assigned jobs, updates status, records diagnosis and parts used |

A Technician is a User with role Technician; only such users can be assigned to jobs.

### 2.1 Permissions

| Function | Admin | Staff | Technician |
|---|---|---|---|
| Manage users, services, prices, parts | ✔ | – | – |
| Customers (add/edit/search) | ✔ | ✔ | – |
| Create/edit job orders, assign technician | ✔ | ✔ | – |
| Update status (Received → Completed) | ✔ | ✔ | ✔ (own jobs) |
| Record diagnosis, notes, parts used | ✔ | – | ✔ (own jobs) |
| Billing, payment, mark Released, cancel job | ✔ | ✔ | – |
| Reports | ✔ | Dashboard, pending jobs | – |

---

## 3. Functional Requirements

Priority: **M** = Must have, **S** = Should have, **C** = Could have (if time allows)

### 3.1 Authentication & User Management
| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The system shall display a login window asking for username and password. | M |
| FR-02 | The system shall validate credentials against stored user records and show an error message on failure. | M |
| FR-03 | The system shall open a main menu based on the user's role (Admin, Staff, Technician). | M |
| FR-04 | The system shall mask the password field (`show="*"`). | M |
| FR-05 | Admin shall be able to add, edit, and delete user accounts. The last remaining Admin cannot be deleted. | S |
| FR-05a | If no users exist on startup, the system shall create a default Admin account and prompt to change its password. | M |
| FR-06 | The system shall provide a logout option that returns to the login window. | M |

### 3.2 Customer Management
| ID | Requirement | Priority |
|---|---|---|
| FR-07 | The system shall allow adding a customer with: Customer ID (auto-generated), full name, contact number, email, address. | M |
| FR-08 | The system shall allow editing customer details. | M |
| FR-09 | The system shall allow deleting a customer (blocked if the customer has any job order, active or past). | S |
| FR-10 | The system shall display all customers in a table. | M |
| FR-11 | The system shall allow searching customers by name, ID, or contact number. | M |
| FR-12 | The system shall show a customer's repair history. | S |

### 3.3 Device & Job Order (Intake)
| ID | Requirement | Priority |
|---|---|---|
| FR-13 | The system shall create a job order with an auto-generated Job ID, the current date/time, and initial status **Received**. | M |
| FR-14 | A job order shall record: customer, device type (Laptop / Desktop / All-in-One), brand, model, serial number, accessories received (charger, bag, etc.). | M |
| FR-15 | A job order shall record the customer's problem description. | M |
| FR-16 | A job order shall record the device's physical condition on arrival (scratches, cracks, etc.). | S |
| FR-17 | A job order shall record the priority level (Normal / Urgent). | S |
| FR-18 | The system shall record the estimated completion date. | S |
| FR-19 | The system shall generate a printable/viewable job receipt (text window or `.txt` file) for the customer. | S |
| FR-20 | The system shall prevent saving a job order if required fields are empty. | M |
| FR-20a | Staff/Admin shall edit a job order's intake details until its status is Completed. | S |

### 3.4 Service Catalog & Pricing
| ID | Requirement | Priority |
|---|---|---|
| FR-21 | Admin shall add, edit, and delete services with: Service ID, name, description, price. A service used by an existing job cannot be deleted. | M |
| FR-22 | Sample services shall include: Diagnostic, OS Reinstallation, Virus Removal, Screen Replacement, Battery Replacement, Keyboard Replacement, Hardware Upgrade (RAM/SSD), Data Backup, Cleaning/Thermal Paste. | M |
| FR-23 | Services shall be selectable (Listbox/Combobox) and attachable to a job order. | M |
| FR-24 | A job order may contain multiple services. | M |
| FR-24a | Services may be added to or removed from a job until status is Completed (e.g., after diagnosis). The service price is copied to the job when added. | M |
| FR-24b | Staff/Admin may adjust a job service's price (e.g., Screen Replacement varies by model); applies to that job only. | S |

### 3.5 Technician Assignment & Repair Tracking
| ID | Requirement | Priority |
|---|---|---|
| FR-25 | Staff/Admin shall assign or reassign a technician (role Technician only) to a job order. | M |
| FR-26 | Technicians shall see a list of jobs assigned to them. | M |
| FR-27 | Technicians shall record a diagnosis and repair notes per job. | M |
| FR-27a | After diagnosis, the system shall record a quote and whether the customer approved it before repair begins. | C |
| FR-28 | The system shall support these statuses: **Received → Diagnosing → Waiting for Parts → Under Repair → Completed → Released** (and **Cancelled**). | M |
| FR-28a | Allowed transitions: Received → Diagnosing; Diagnosing → Waiting for Parts / Under Repair / Completed (diagnostic-only); Waiting for Parts → Under Repair; Under Repair → Waiting for Parts / Completed; Completed → Released. Cancelled is allowed from any status before Released. Released and Cancelled are final. | M |
| FR-28b | Cancelling a job shall require a reason and restore any deducted parts stock. Payments already received stay on record and the job is flagged "Refund due". | S |
| FR-29 | The system shall record a timestamp and the acting user every time the status changes. The current status is the latest log entry. | M |
| FR-30 | The system shall display all job orders in a table, filterable by status. | M |
| FR-31 | The system shall search job orders by Job ID, customer name, or serial number. | M |
| FR-31a | The system shall provide a job details view: intake info, services, parts, status history, payments, balance. | M |
| FR-32 | Customers shall be notified of completion through an on-screen prompt for Staff to contact them (actual SMS/email is out of scope). | C |

### 3.6 Parts & Inventory (Optional Module)
| ID | Requirement | Priority |
|---|---|---|
| FR-33 | The system shall store parts with: Part ID, name, quantity, unit price, low-stock threshold. | S |
| FR-33a | Admin shall add, edit, and delete parts (delete blocked if used by a job). | S |
| FR-34 | Technicians shall add parts used to a job order; stock shall decrease automatically and the unit price is copied to the job. Removing a part from a job returns it to stock. | S |
| FR-35 | The system shall warn when a part's stock is at or below its low-stock threshold. | C |
| FR-36 | The system shall block adding a part if stock is insufficient. | S |

### 3.7 Billing & Payment
| ID | Requirement | Priority |
|---|---|---|
| FR-37 | The system shall compute the total = sum of job service prices + (parts used × unit price, if the Parts module is implemented). | M |
| FR-38 | The system shall allow recording a down payment/deposit as the first payment on a job. | S |
| FR-39 | The system shall record each payment: amount, method (Cash / GCash / Card), date, receiving user. A job may have multiple payments. | M |
| FR-40 | The system shall compute the remaining balance and, for cash, the change. | M |
| FR-41 | The system shall generate an official receipt/invoice (text window or `.txt` file) showing job ID, customer, services, parts, total, payments, balance, date. | M |
| FR-42 | A job can be marked **Released** only from Completed and only when the balance is 0. | M |

### 3.8 Reports
| ID | Requirement | Priority |
|---|---|---|
| FR-43 | The system shall show a dashboard with counts per status (e.g., Received: 3, Under Repair: 5). | S |
| FR-44 | The system shall generate a daily/monthly sales report based on payments received in the period. | S |
| FR-45 | The system shall list pending (unfinished) jobs. | S |
| FR-46 | Reports shall be exportable to a `.txt` or `.csv` file. | C |

### 3.9 Data Management
| ID | Requirement | Priority |
|---|---|---|
| FR-47 | The system shall save all records (users, customers, jobs, services, parts, payments) to local files. | M |
| FR-48 | The system shall load saved records automatically on startup. | M |
| FR-49 | The system shall create the data files/folders automatically if they do not exist (`os.path`, `os.mkdir`). | M |
| FR-50 | The system shall provide a backup option that copies data files to a backup folder. | C |

### 3.10 Validation & Error Handling
| ID | Requirement | Priority |
|---|---|---|
| FR-51 | The system shall validate inputs: required fields, contact number (digits, optional `+`, spaces, dashes), price (non-negative decimal), quantity (positive integer), valid email format, valid dates. | M |
| FR-52 | The system shall show errors through message boxes (`showerror`, `showwarning`, `showinfo`) instead of terminal output. | M |
| FR-53 | The system shall ask for confirmation before deleting or cancelling a record (`askyesno`). | M |
| FR-54 | The system shall handle file errors (missing/corrupted file, no permission) using `try/except` without crashing, and name the affected file in the message. Files shall be written to a temporary file then replaced, to avoid corruption. | M |
| FR-55 | IDs shall be auto-generated, unique, and never reused after deletion. Duplicate usernames and service names shall be rejected. | M |

### 3.11 GUI Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-56 | All features shall be operated through a Tkinter GUI; no `input()` or terminal prompts. | M |
| FR-57 | The main window shall have a menu bar or button panel: Customers, Job Orders, Services, Parts, Billing, Reports, Logout. Entries are shown per the user's role (2.1); Parts only if the module is implemented. | M |
| FR-58 | Forms shall use appropriate widgets (see table below). | M |
| FR-59 | Record lists shall be shown in a table (`ttk.Treeview`) with a scrollbar. | M |
| FR-60 | The interface shall use consistent layout, labels, and button names across all windows. | S |

**Widget mapping**

| Need | Tkinter widget |
|---|---|
| Text input (name, serial no.) | `Entry` |
| Long text (problem, diagnosis) | `Text` |
| Choose one (device type, payment method) | `Radiobutton` / `ttk.Combobox` |
| Choose many (accessories received) | `Checkbutton` |
| Pick a service | `Listbox` / `Combobox` |
| Number input (quantity) | `Spinbox` |
| Group form sections | `Frame` / `LabelFrame` |
| Static text | `Label` |
| Actions (Save, Delete, Search) | `Button` |
| Pop-up forms / receipts | `Toplevel` |
| Alerts and confirmations | `messagebox` |
| Record tables | `ttk.Treeview` + `Scrollbar` |

---

## 4. Repair Job Workflow

```
Customer brings device
        ↓
[Staff] Register customer (if new) → Create Job Order (Status: Received) → Print receipt
        ↓
[Staff] Assign technician          (status stays Received)
        ↓
[Technician] Diagnose              → Status: Diagnosing
        ↓
   Needs parts? ── yes → Status: Waiting for Parts
        ↓ no / parts arrived
[Technician] Repair                → Status: Under Repair
        ↓
[Technician] Mark done             → Status: Completed
        ↓
[Staff] Compute bill → Receive payment → Print official receipt
        ↓
[Staff] Release device             → Status: Released
```

Cancellation: Staff/Admin may cancel any job before Released (FR-28b).

---

## 5. Data Requirements

Each table is one CSV file in `data/` (header row = column names, UTF-8). Each row is loaded as a dictionary. Types are logical; CSV stores everything as text, so convert with `int()`, `float()`, or `datetime` on load.

### 5.1 Table definitions

#### 5.1.1 users

File: `data/users.csv` · PK: `user_id` · FK: none

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `user_id` | TEXT | No | PK | Format `U-001`. Auto-generated, never reused. |
| `username` | TEXT | No | UNIQUE | Login name, 3–20 characters, no spaces. |
| `password` | TEXT | No |  | Plain text, or `hashlib` hash if implemented. |
| `role` | TEXT | No |  | One of: `Admin`, `Staff`, `Technician`. |
| `full_name` | TEXT | No |  | Display name of the user. |

#### 5.1.2 customers

File: `data/customers.csv` · PK: `customer_id` · FK: none

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `customer_id` | TEXT | No | PK | Format `C-001`. Auto-generated, never reused. |
| `name` | TEXT | No |  | Customer's full name. |
| `contact_no` | TEXT | No |  | Digits, optional `+`, spaces, dashes. Stored as text to keep leading zeros. |
| `email` | TEXT | Yes |  | Valid email format if provided. |
| `address` | TEXT | Yes |  | Customer's address. |

#### 5.1.3 services

File: `data/services.csv` · PK: `service_id` · FK: none

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `service_id` | TEXT | No | PK | Format `S-001`. Auto-generated, never reused. |
| `name` | TEXT | No | UNIQUE | Service name, e.g. `OS Reinstallation`. |
| `description` | TEXT | Yes |  | What the service covers. |
| `price` | DECIMAL(10,2) | No |  | Default price in PHP, ≥ 0. Changing it does not affect existing jobs. |

#### 5.1.4 parts

File: `data/parts.csv` · PK: `part_id` · FK: none

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `part_id` | TEXT | No | PK | Format `P-001`. Auto-generated, never reused. |
| `name` | TEXT | No |  | Part name, e.g. `8GB DDR4 RAM`. |
| `quantity` | INTEGER | No |  | Stock on hand, ≥ 0. Decreased when a part is added to a job, restored on removal or cancellation. |
| `unit_price` | DECIMAL(10,2) | No |  | Current selling price per unit, ≥ 0. |
| `low_stock_threshold` | INTEGER | No |  | Warn when `quantity` ≤ this value. Default 0. |

#### 5.1.5 jobs

File: `data/jobs.csv` · PK: `job_id` · FK: `customer_id` → customers, `technician_id` → users, `received_by` → users

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `job_id` | TEXT | No | PK | Format `J-0001`. Auto-generated, never reused. |
| `customer_id` | TEXT | No | FK | Owner of the device. References `customers.customer_id`. |
| `technician_id` | TEXT | Yes | FK | Assigned technician. References `users.user_id`; user's role must be `Technician`. Empty until assigned. |
| `received_by` | TEXT | No | FK | Staff/Admin who created the job. References `users.user_id`. |
| `device_type` | TEXT | No |  | One of: `Laptop`, `Desktop`, `All-in-One`. |
| `brand` | TEXT | No |  | Device brand, e.g. `Lenovo`. |
| `model` | TEXT | No |  | Device model. |
| `serial_no` | TEXT | No |  | Serial number. Not unique (a device can return for another repair). |
| `problem` | TEXT | No |  | Customer's problem description. |
| `device_condition` | TEXT | Yes |  | Physical condition on arrival (scratches, cracks, etc.). |
| `priority` | TEXT | No |  | `Normal` or `Urgent`. Default `Normal`. |
| `date_received` | DATETIME | No |  | `YYYY-MM-DD HH:MM`. Set automatically at creation. |
| `est_completion` | DATE | Yes |  | `YYYY-MM-DD`. Must not be earlier than `date_received`. |
| `diagnosis` | TEXT | Yes |  | Technician's diagnosis. |
| `notes` | TEXT | Yes |  | Technician's repair notes. |
| `cancel_reason` | TEXT | Yes |  | Required when the job is cancelled, otherwise empty. |

#### 5.1.6 job_accessories

File: `data/job_accessories.csv` · PK: (`job_id`, `accessory`) · FK: `job_id` → jobs

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `job_id` | TEXT | No | PK, FK | References `jobs.job_id`. |
| `accessory` | TEXT | No | PK | One accessory received, e.g. `Charger`, `Bag`, `Battery`, `Mouse`. One row per accessory. |

#### 5.1.7 job_services

File: `data/job_services.csv` · PK: (`job_id`, `service_id`) · FK: `job_id` → jobs, `service_id` → services

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `job_id` | TEXT | No | PK, FK | References `jobs.job_id`. |
| `service_id` | TEXT | No | PK, FK | References `services.service_id`. A service appears once per job. |
| `price` | DECIMAL(10,2) | No |  | Price charged on this job, ≥ 0. Copied from `services.price` when added; may be adjusted (FR-24b). |

#### 5.1.8 job_parts

File: `data/job_parts.csv` · PK: (`job_id`, `part_id`) · FK: `job_id` → jobs, `part_id` → parts

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `job_id` | TEXT | No | PK, FK | References `jobs.job_id`. |
| `part_id` | TEXT | No | PK, FK | References `parts.part_id`. A part appears once per job. |
| `quantity_used` | INTEGER | No |  | Units used on this job, > 0. Cannot exceed `parts.quantity` when added. |
| `unit_price` | DECIMAL(10,2) | No |  | Price per unit at the time added, ≥ 0. Copied from `parts.unit_price`. |

#### 5.1.9 payments

File: `data/payments.csv` · PK: `payment_id` · FK: `job_id` → jobs, `received_by` → users

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `payment_id` | TEXT | No | PK | Format `PAY-0001`. Auto-generated, never reused. |
| `job_id` | TEXT | No | FK | References `jobs.job_id`. |
| `amount` | DECIMAL(10,2) | No |  | Amount applied to the job's bill, > 0. Cash change is not stored. |
| `method` | TEXT | No |  | One of: `Cash`, `GCash`, `Card`. |
| `payment_date` | DATETIME | No |  | `YYYY-MM-DD HH:MM`. Set automatically. |
| `received_by` | TEXT | No | FK | User who took the payment. References `users.user_id`. |

#### 5.1.10 status_log

File: `data/status_log.csv` · PK: `log_id` · FK: `job_id` → jobs, `changed_by` → users

| Column | Type | Null | Key | Constraint / Description |
|---|---|---|---|---|
| `log_id` | TEXT | No | PK | Format `L-00001`. Auto-generated, never reused. |
| `job_id` | TEXT | No | FK | References `jobs.job_id`. |
| `status` | TEXT | No |  | One of: `Received`, `Diagnosing`, `Waiting for Parts`, `Under Repair`, `Completed`, `Released`, `Cancelled`. |
| `changed_at` | DATETIME | No |  | `YYYY-MM-DD HH:MM`. Set automatically. |
| `changed_by` | TEXT | No | FK | User who made the change. References `users.user_id`. |

### 5.2 Relationships

- customers 1 — N jobs
- users (role Technician) 1 — N jobs (`technician_id`); users 1 — N jobs (`received_by`), payments, status_log
- jobs M — N services via job_services; jobs M — N parts via job_parts
- jobs 1 — N job_accessories, payments, status_log

### 5.3 Derived values (never stored)

Calculate these when needed:

| Value | How it is calculated |
|---|---|
| Current job status | `status` of the latest `status_log` row for the job |
| Date released / completed | `changed_at` of the matching `status_log` row |
| Services subtotal | Sum of `job_services.price` for the job |
| Parts subtotal | Sum of `job_parts.quantity_used × job_parts.unit_price` for the job |
| Total | Services subtotal + parts subtotal |
| Amount paid | Sum of `payments.amount` for the job |
| Balance | Total − amount paid |
| Change | Cash tendered − amount due (computed at payment time, not saved) |
| Payment status | Unpaid / Partial / Paid, from amount paid vs total |
| Refund due | Latest status is `Cancelled` and amount paid > 0 |
| Dashboard counts, sales reports, pending jobs | Counted/summed from the tables above |

Stored on purpose (facts, not calculations): `job_services.price` and `job_parts.unit_price` are price snapshots so later catalog changes do not alter past jobs. `parts.quantity` is the stock level, as restocks are not recorded as separate entries.

### 5.4 Normalization (3NF)

- **1NF:** all columns are atomic. Accessories are in `job_accessories`, one row each.
- **2NF:** in the composite-key tables every non-key column depends on the whole key: `price` on (job, service); `quantity_used` and `unit_price` on (job, part).
- **3NF:** no non-key column depends on another non-key column. Customer, technician, service, and part details live only in their own tables.

### 5.5 Rules

- IDs are auto-generated, prefixed, and never reused (FR-55).
- A referenced row cannot be deleted (NFR-06).
- Creating a job also writes its first `status_log` row (`Received`); every status change adds a row, and nothing in `status_log` is edited or deleted.

---

## 6. Suggested Screens

1. Login window
2. Main dashboard / menu
3. Customer management (form + table)
4. New job order form
5. Job order list (with status filter and search)
6. Job details / update status (Technician view)
7. Services management
8. Parts inventory
9. Billing & payment window
10. Receipt window
11. Reports window

---

## 7. Mapping to Course Lessons

| Lesson topic | Where it is used in the system |
|---|---|
| Variables, data types, casting | Converting price/quantity inputs (`float()`, `int()`, `str()`) |
| Operators | Computing totals, balance, change |
| `if / elif / else` | Role-based menu, status validation |
| `for` / `while` loops | Displaying records, searching lists |
| `break / continue / pass` | Search loops, skipped records |
| Strings | Formatting receipts, input cleaning (`strip()`, `upper()`, `format`) |
| Lists, tuples | Collections of jobs, fixed status list |
| Dictionaries | Individual customer, job, and service records |
| Functions | `add_customer()`, `compute_total()`, `save_data()` |
| Modules / packages | Splitting code into `gui`, `storage`, `models` |
| Date and time | Date received, status timestamps, daily reports |
| File I/O | Saving/loading all records, exporting receipts |
| `os` module | Create folders, check files, backups |
| Exception handling | File errors, invalid input, empty fields |
| Tkinter widgets | All screens (Entry, Button, Listbox, Frame, Toplevel, etc.) |

---

## 8. Non-Functional Requirements (Brief)

| ID | Requirement |
|---|---|
| NFR-01 | Usability: a new user can create a job order within 2 minutes without help. |
| NFR-02 | Reliability: the program shall not crash on invalid input or missing files. |
| NFR-03 | Performance: lists and searches shall respond within 2 seconds for up to 1,000 records. |
| NFR-04 | Portability: runs on Windows with standard Python 3 installed (no extra packages required). |
| NFR-05 | Maintainability: code shall be split into functions/modules with comments. |
| NFR-06 | Integrity: a record referenced by another record (customer, service, part, user) cannot be deleted. |

---

## 9. Out of Scope

- Online/web access or multi-computer networking
- Real SMS/email notifications
- Barcode/QR scanning
- Payment gateway integration
- Advanced password security (plain storage acceptable; hashing with `hashlib` recommended)

---

## 10. Suggested Development Priority

1. **Phase 1 (Core):** Login, Customers, Job Orders, Services, Status tracking, Search/filter, Job receipt, Validation, File storage
2. **Phase 2:** Billing/payment, Official receipt, Release gating (FR-42; Released stays disabled until billing exists)
3. **Phase 3 (if time allows):** Parts inventory, Reports, Backup, Export
