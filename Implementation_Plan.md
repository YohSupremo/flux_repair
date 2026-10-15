# Implementation Plan: Computer & Laptop Repair Service System

*ITEP310-T · Python 3 + Tkinter · CSV storage · Based on Functional\_Requirements.md (FR-01 to FR-60, NFR-01 to NFR-06)*

## 1. Approach

- **Stack:** Python 3.8+, standard library only: `tkinter`, `tkinter.ttk`, `tkinter.messagebox`, `csv`, `os`, `shutil`, `datetime`, `decimal`, `unittest`. Nothing to `pip install` (NFR-04).
- **Layers:** GUI → logic → storage. Each layer calls only the one below it.
  - `gui/` never reads or writes CSV and never calculates totals.
  - `logic/` never imports `tkinter`, so it can be unit tested without opening a window.
  - `storage.py` knows only tables, rows, and files. It knows nothing about repairs.
- **Data in memory:** load every CSV into a list of dictionaries at startup (FR-48). Change the lists, then write the affected file back (write-through).
- **Money:** use `decimal.Decimal`, never `float`. Format with 2 decimals.
- **Build order:** vertical slices. Finish one feature end to end (storage → logic → screen → test) before starting the next.
- **Errors:** logic raises `ValidationError`, `RuleError`, or `StorageError`. One decorator in the GUI catches them and shows a message box, so nothing prints to the terminal (FR-52, FR-56).

## 2. Project structure

```
repair_shop/
├── main.py                 # entry point: create App, run mainloop
├── config.py               # paths, date and currency formats
├── errors.py               # ValidationError, RuleError, StorageError
├── models.py               # table columns, constants, status transitions
├── utils.py                # validators, formatters, date helpers
├── storage.py              # CSV load/save, ID counters, backup
├── logic/
│   ├── auth.py             # login, roles, permissions, user accounts
│   ├── customers.py
│   ├── catalog.py          # repair service catalog
│   ├── jobs.py             # job orders, assignment, status
│   ├── parts.py
│   ├── billing.py          # bill calculation, payments, release rule
│   └── reports.py
├── gui/
│   ├── app.py              # App(Tk): current user, screen switching
│   ├── widgets.py          # make_table, guard decorator, form helpers
│   ├── login.py, main_menu.py
│   ├── users_ui.py, customers_ui.py, catalog_ui.py, parts_ui.py
│   ├── jobs_ui.py, job_form.py, job_details_ui.py
│   └── billing_ui.py, receipt_ui.py, reports_ui.py
├── tests/                  # unittest: storage and logic only
├── data/                   # auto-created CSV files
└── receipts/ exports/ backups/    # auto-created
```

The package is named `logic` (not `services`) to avoid confusion with the repair-service catalog table.

## 3. Core modules

### 3.1 config.py and errors.py

- `DATA_DIR`, `RECEIPT_DIR`, `EXPORT_DIR`, `BACKUP_DIR`: built with `os.path.join` from the program folder. Tests override `DATA_DIR` with a temp folder.
- `DATE_FMT = '%Y-%m-%d'`, `DATETIME_FMT = '%Y-%m-%d %H:%M'`, `CURRENCY = '₱'`.
- Three exception classes, nothing else.

### 3.2 models.py

The single source of truth for the schema in §5 of the requirements.

```python
TABLES = {
    'users': ['user_id', 'username', 'password', 'role', 'full_name'],
    'customers': ['customer_id', 'name', 'contact_no', 'email', 'address'],
    'services': ['service_id', 'name', 'description', 'price'],
    'parts': ['part_id', 'name', 'quantity', 'unit_price', 'low_stock_threshold'],
    'jobs': ['job_id', 'customer_id', 'technician_id', 'received_by', 'device_type',
             'brand', 'model', 'serial_no', 'problem', 'device_condition', 'priority',
             'date_received', 'est_completion', 'diagnosis', 'notes', 'cancel_reason'],
    'job_accessories': ['job_id', 'accessory'],
    'job_services': ['job_id', 'service_id', 'price'],
    'job_parts': ['job_id', 'part_id', 'quantity_used', 'unit_price'],
    'payments': ['payment_id', 'job_id', 'amount', 'method', 'payment_date', 'received_by'],
    'status_log': ['log_id', 'job_id', 'status', 'changed_at', 'changed_by'],
}
ROLES = ('Admin', 'Staff', 'Technician')
DEVICE_TYPES = ('Laptop', 'Desktop', 'All-in-One')
PRIORITIES = ('Normal', 'Urgent')
PAYMENT_METHODS = ('Cash', 'GCash', 'Card')
STATUSES = ('Received', 'Diagnosing', 'Waiting for Parts', 'Under Repair',
            'Completed', 'Released', 'Cancelled')
TRANSITIONS = {
    'Received': ['Diagnosing', 'Cancelled'],
    'Diagnosing': ['Waiting for Parts', 'Under Repair', 'Completed', 'Cancelled'],
    'Waiting for Parts': ['Under Repair', 'Cancelled'],
    'Under Repair': ['Waiting for Parts', 'Completed', 'Cancelled'],
    'Completed': ['Released', 'Cancelled'],
    'Released': [],
    'Cancelled': [],
}
ID_PREFIXES = {'users': ('U', 3), 'customers': ('C', 3), 'services': ('S', 3),
               'parts': ('P', 3), 'jobs': ('J', 4), 'payments': ('PAY', 4),
               'status_log': ('L', 5)}
```

`TRANSITIONS` implements FR-28a. Do not scatter status rules anywhere else.

### 3.3 utils.py

| Function | Purpose |
| --- | --- |
| `require_text(value, label)` | strip, reject empty (FR-20, FR-51) |
| `valid_contact(value)` | digits, optional `+`, spaces, dashes |
| `valid_email(value)` | simple check: one `@`, a dot after it |
| `parse_money(text)` | text → `Decimal`, must be ≥ 0 |
| `parse_positive_int(text)` | text → int > 0 |
| `parse_date(text)` | `YYYY-MM-DD` → `date`, else ValidationError |
| `now_str()` | current time in `DATETIME_FMT` |
| `money(value)` | format as `₱1,234.50` |

Every validator raises `ValidationError` with a message the user can read.

### 3.4 storage.py

| Function | Purpose |
| --- | --- |
| `init_storage()` | create `data/` and any missing CSV with its header (FR-49), then load all tables (FR-48) |
| `get_rows(table)` | the in-memory list of dicts |
| `insert(table, row)` | append, then `save_table` |
| `update(table, key_col, key, changes)` | change matching row, then `save_table` |
| `delete(table, key_col, key)` | remove matching row, then `save_table` |
| `save_table(table)` | atomic write (below) |
| `next_id(prefix, width)` | ID generator that never reuses numbers |
| `backup_data()` | copy `data/` to `backups/YYYYMMDD_HHMMSS/` (FR-50) |

**Atomic write** (FR-54): write to a temp file, then replace. A crash mid-write cannot corrupt the real file.

```python
def save_table(name):
    path = table_path(name)
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=TABLES[name])
            w.writeheader()
            w.writerows(db[name])
        os.replace(tmp, path)
    except OSError as e:
        raise StorageError('Cannot save ' + name + '.csv: ' + str(e))
```

**Loading:** read with `csv.DictReader`. If the header does not match `TABLES[name]` or a row has the wrong number of fields, raise `StorageError` naming the file. Do not overwrite a corrupted file.

**Never-reused IDs** (FR-55): `max + 1` would reuse a number after the newest row is deleted. Keep a small metadata file `data/counters.csv` (`prefix,last_number`). It is not an entity table; add one line about it to §5 of the requirements.

```python
def next_id(prefix, width):
    n = int(counters.get(prefix, '0')) + 1
    counters[prefix] = str(n)
    save_counters()          # save the counter BEFORE the row
    return prefix + '-' + str(n).zfill(width)
```

### 3.5 logic package

**auth.py**

- `login(username, password)` → user dict, or `ValidationError('Invalid username or password')` (FR-02).
- `can(role, action)` → bool, from a dict that mirrors the permission matrix in §2.1.
- `seed_default_admin()`: if `users` is empty, create an Admin and return a message telling the user to change the password (FR-05a).
- `add_user`, `edit_user`, `delete_user` (blocks the last Admin and any user referenced by a job, payment, or log).

**customers.py**

- `add_customer`, `edit_customer`, `delete_customer` (blocked if any job exists, FR-09).
- `search_customers(text)`: case-insensitive match on name, ID, or contact number (FR-11).
- `customer_history(customer_id)`: that customer's jobs (FR-12).

**catalog.py**

- `add_service`, `edit_service`, `delete_service` (blocked if used in `job_services`).
- `seed_sample_services()`: the nine services from FR-22 on first run.

**jobs.py**

- `create_job(data, accessories, service_ids, user)`: validate, then write `jobs`, `job_accessories`, `job_services` (copy current prices), and the first `status_log` row (`Received`).
- `edit_job` (until Completed), `add_service_to_job`, `remove_service_from_job`, `set_service_price` (FR-24a/b).
- `assign_technician(job_id, tech_id, user)`: the user must have role Technician.
- `record_diagnosis(job_id, diagnosis, notes, user)`.
- `change_status(job_id, new_status, user)`: see §4.
- `current_status(job_id)` and `status_map()`: see §4.
- `list_jobs(status=None, text=None, technician_id=None)`: filter and search by Job ID, customer name, or serial number (FR-30, FR-31).
- `job_details(job_id)` and `status_history(job_id)` (FR-31a).
- `intake_receipt_text(job_id)` (FR-19).

**parts.py**

- `add_part`, `edit_part`, `delete_part` (blocked if used by a job).
- `add_part_to_job(job_id, part_id, qty, user)`: reject if `qty` exceeds stock (FR-36), otherwise reduce stock and copy the unit price (FR-34).
- `remove_part_from_job`: restore stock.
- `low_stock_parts()` (FR-35).

**billing.py**

- `compute_bill(job_id)`: see §4.
- `record_payment(job_id, amount, method, user)`: amount > 0 and not more than the balance. For cash, the GUI passes the amount due; change is shown, not stored.
- `official_receipt_text(job_id)` (FR-41).

**reports.py**

- `status_counts()` (FR-43), `pending_jobs()` (FR-45), `sales_report(start, end)` from `payments` (FR-44), `export_rows(rows, columns, path)` for `.csv` or `.txt` (FR-46).

### 3.6 GUI design

- **One `Tk` root.** `App(tk.Tk)` holds `current_user`. The login screen and the main screen are `Frame`s swapped in the root; logout destroys the main frame and shows login (FR-06).
- **Main screen:** a button panel on the left (Dashboard, Customers, Job Orders, Services, Parts, Billing, Reports, Logout), content area on the right. Buttons are built from the user's role (FR-03, FR-57).
- **Pop-ups** (job form, job details, payment, receipt) are `Toplevel` windows with `grab_set()` so the user finishes them first.
- **Refresh pattern:** each screen has a `refresh()` that re-reads from `logic` and refills the table. Call it after every change.
- **Reusable helpers in widgets.py:**
  - `make_table(parent, columns, widths)` → a `ttk.Treeview` plus vertical `Scrollbar` (FR-59).
  - `fill_table(tree, rows)`.
  - `labeled_entry(parent, text, row)` for consistent forms (FR-60).
  - `confirm(message)` wrapping `askyesno` (FR-53).
  - `guard`, the error decorator below.

```python
def guard(fn):
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except (ValidationError, RuleError) as e:
            messagebox.showwarning('Cannot continue', str(e))
        except StorageError as e:
            messagebox.showerror('File error', str(e))
    return wrapper
```

Put `@guard` on every button handler.

| Screen | File | Main widgets |
| --- | --- | --- |
| Login | `login.py` | `Entry` (password `show='*'`), `Button` |
| Main / Dashboard | `main_menu.py` | `Button` panel, `LabelFrame` with status counts |
| Users | `users_ui.py` | `Treeview`, `Entry`, `ttk.Combobox` (role) |
| Customers | `customers_ui.py` | `Entry`, `Treeview`, search `Entry` + `Button` |
| New job order | `job_form.py` | `Radiobutton` (device type), `Checkbutton` (accessories), `Text` (problem, condition), `Combobox` (priority, customer), `Listbox` multi-select (services) |
| Job list | `jobs_ui.py` | `Combobox` status filter, search `Entry`, `Treeview` |
| Job details | `job_details_ui.py` | `Text` (diagnosis, notes), `Combobox` (technician, next status), `Treeview` (services, parts, history, payments) |
| Services | `catalog_ui.py` | `Entry`, `Treeview` |
| Parts | `parts_ui.py` | `Entry`, `Spinbox` (quantity), `Treeview` |
| Billing | `billing_ui.py` | `Label` (total, paid, balance), `Entry`, `Radiobutton` (method) |
| Receipt | `receipt_ui.py` | read-only `Text`, Save `Button` |
| Reports | `reports_ui.py` | `Treeview`, date `Entry`, Export `Button` |

## 4. Key logic

**Current status** is never stored. It is the latest `status_log` row. Timestamps only have minute precision, so order by `log_id`, not by time.

```python
def current_status(job_id):
    logs = [l for l in get_rows('status_log') if l['job_id'] == job_id]
    return max(logs, key=lambda l: int(l['log_id'][2:]))['status']

def status_map():            # one pass for the whole job list (NFR-03)
    latest = {}
    for l in get_rows('status_log'):
        n = int(l['log_id'][2:])
        if l['job_id'] not in latest or n > latest[l['job_id']][0]:
            latest[l['job_id']] = (n, l['status'])
    return {j: v[1] for j, v in latest.items()}
```

**Bill calculation** (nothing is saved):

```python
def compute_bill(job_id):
    zero = Decimal('0')
    services = sum((Decimal(r['price']) for r in get_rows('job_services')
                    if r['job_id'] == job_id), zero)
    parts = sum((Decimal(r['unit_price']) * int(r['quantity_used'])
                 for r in get_rows('job_parts') if r['job_id'] == job_id), zero)
    paid = sum((Decimal(r['amount']) for r in get_rows('payments')
                if r['job_id'] == job_id), zero)
    total = services + parts
    return {'services': services, 'parts': parts, 'total': total,
            'paid': paid, 'balance': total - paid}
```

**Status change** is the one gate for every rule (FR-28a/b, FR-42, §2.1):

```python
def change_status(job_id, new_status, user):
    current = current_status(job_id)
    if new_status not in TRANSITIONS[current]:
        raise RuleError('Cannot change from ' + current + ' to ' + new_status)
    if user['role'] == 'Technician':
        job = find_job(job_id)
        if job['technician_id'] != user['user_id'] or new_status in ('Released', 'Cancelled'):
            raise RuleError('You cannot make this change')
    if new_status == 'Released' and compute_bill(job_id)['balance'] != 0:
        raise RuleError('Balance must be fully paid before release')
    if new_status == 'Cancelled':
        restore_stock(job_id)             # FR-28b
    insert('status_log', {'log_id': next_id('L', 5), 'job_id': job_id,
                          'status': new_status, 'changed_at': now_str(),
                          'changed_by': user['user_id']})
```

The GUI only lists allowed next statuses in the `Combobox`, but this function enforces the rules even if the GUI is wrong.

**Multi-file saves** (job creation touches four files): validate everything first, then save in a fixed order: `jobs`, `job_accessories`, `job_services`, `status_log`. On startup, run a quick integrity check and warn about rows whose foreign key points nowhere.

**Receipts:** build text with `str.ljust` / `str.rjust` into a fixed-width layout. Show it in a `Toplevel` with a read-only `Text`, and save it as `receipts/J-0001_intake.txt` or `J-0001_official.txt`.

## 5. Build steps

Effort: S ≈ half a day, M ≈ 1 day, L ≈ 2 days. Steps 0–6 are Phase 1, step 7 is Phase 2, steps 8–9 are Phase 3.

### Step 0: Setup (S)

- Create the folder tree, `config.py`, `errors.py`, `models.py`.
- `main.py` opens an empty `Tk` window.
- **Done when:** `python main.py` opens a window and closes cleanly.

### Step 1: Storage and utils (M) · FR-47–49, 51, 54, 55

- Write `storage.py` and `utils.py` with all validators.
- Unit tests: round trip, missing folder and files get created, bad header raises `StorageError`, IDs are never reused after delete.
- **Done when:** `python -m unittest` passes.

### Step 2: Login, roles, main window (M) · FR-01–04, 05a, 06, 03, 57

- `auth.py`, `login.py`, `app.py`, `main_menu.py`.
- Seed the default Admin on first run.
- Role-based button panel and Logout.
- **Done when:** each of the three roles logs in, sees only its own buttons, and logs out. A wrong password shows a message box.

### Step 3: Users and customers (M) · FR-05, 07–11

- Customers: form + `Treeview` + search + delete guard.
- Users screen for Admin.
- **Done when:** add, edit, search, and delete work, and delete is blocked when a user or customer is referenced.

### Step 4: Service catalog (S) · FR-21–22

- `catalog.py`, `catalog_ui.py`, seed the nine sample services.
- **Done when:** Admin can manage services, and Staff cannot open the screen.

### Step 5: Job order intake (L) · FR-13–20a, 23, 24, 24a, 24b, 19

- `job_form.py`: customer picker (with search), device fields, accessories, problem, condition, priority, estimated date, service `Listbox`.
- `create_job` saves in the fixed order from §4.
- Intake receipt window + `.txt` file.
- **Done when:** a job with two services and three accessories saves, the receipt shows correctly, and empty required fields are blocked.

### Step 6: Assignment, tracking, technician view (L) · FR-25–31a, 28a

- Job list with status filter and search, using `status_map()`.
- Job details window: assign technician, change status, diagnosis and notes, history.
- Technician sees only their own jobs.
- **Done when:** a job travels Received → Completed with correct logs, and illegal moves are refused. Released is disabled until step 7.
- **Milestone:** Phase 1 complete. Demo-ready.

### Step 7: Billing and release (L) · FR-37–42, 28b

- `billing.py`, `billing_ui.py`, official receipt.
- Multiple payments, change for cash, balance display.
- Enable Released (needs balance 0). Cancellation with reason and refund flag.
- **Done when:** a partially paid job cannot be released and a fully paid one can. Totals match a hand calculation.

### Step 8: Parts inventory (M) · FR-33–36

- `parts.py`, `parts_ui.py`, add and remove parts on a job, low-stock warning.
- **Done when:** stock drops on use, comes back on removal or cancellation, and over-use is blocked.

### Step 9: Reports, export, backup (M) · FR-43–46, 50, 12, 32

- Dashboard counts, pending jobs, daily and monthly sales, export to `.csv` / `.txt`.
- Backup button, customer history, completion prompt (on-screen reminder to contact the customer).
- **Done when:** report numbers match the data and the backup folder contains all CSVs.

### Step 10: Hardening (M) · all M requirements, NFR-01–05

- Sweep every screen: validation, message boxes, confirm before delete or cancel (FR-53).
- Generate 1,000 jobs and confirm lists load in under 2 seconds (NFR-03).
- Run the full manual test list in §7. Add comments and a short README (NFR-05).
- **Done when:** the final checklist in §9 is ticked.

## 6. Requirement traceability

| Requirements | Where |
| --- | --- |
| FR-01–06a Authentication, users | `logic/auth.py`, `gui/login.py`, `gui/users_ui.py`, `gui/app.py` |
| FR-07–12 Customers | `logic/customers.py`, `gui/customers_ui.py` |
| FR-13–20a Job intake | `logic/jobs.py`, `gui/job_form.py`, `gui/receipt_ui.py` |
| FR-21–24b Service catalog | `logic/catalog.py`, `gui/catalog_ui.py`, `gui/job_form.py` |
| FR-25–32 Assignment, tracking | `logic/jobs.py`, `gui/jobs_ui.py`, `gui/job_details_ui.py` |
| FR-33–36 Parts | `logic/parts.py`, `gui/parts_ui.py` |
| FR-37–42 Billing | `logic/billing.py`, `gui/billing_ui.py`, `gui/receipt_ui.py` |
| FR-43–46 Reports | `logic/reports.py`, `gui/reports_ui.py` |
| FR-47–50 Data management | `storage.py` |
| FR-51–55 Validation, errors | `utils.py`, `errors.py`, `gui/widgets.py` (`guard`, `confirm`) |
| FR-56–60 GUI | `gui/*` |

## 7. Testing

**Unit tests** (`unittest`, run with `python -m unittest`). Point `config.DATA_DIR` at a temp folder in `setUp`.

- Storage: round trip, missing files created, corrupted file raises `StorageError` and is not overwritten, IDs never reused.
- Validators: empty, bad email, bad contact, negative price, zero quantity, bad date.
- Status: every allowed transition works, every other one raises `RuleError`.
- Billing: totals with decimals (for example 0.10 + 0.20 equals 0.30), partial payment, overpayment rejected, release blocked until balance is 0.
- Parts: over-use blocked, stock drops on add, returns on remove and on cancel.
- Deletes: customer, service, part, and user are blocked when referenced.

**Manual tests** (run once per role):

1. Full workflow from the requirements §4: register customer, create job, assign, diagnose, wait for parts, repair, complete, pay, release.
2. Cancel a job mid-repair and check stock and the refund flag.
3. Delete or rename `data/`: the program recreates it and does not crash.
4. Damage a CSV by hand: a message box names the file, no crash.
5. Open `jobs.csv` in Excel (Windows locks it) and save from the app: a message box, no crash.
6. Leave every form empty, then enter letters in number fields.
7. Time NFR-01: a new person creates a job order within 2 minutes.

## 8. Risks

| Risk | Mitigation |
| --- | --- |
| Business rules creep into GUI code | Rule of §1: GUI calls `logic` only; review each screen against it |
| Half-saved job (crash between files) | Fixed save order, validate first, startup integrity check |
| Float rounding in money | `Decimal` everywhere, tests for it |
| Excel opens or edits CSVs (lock, lost leading zeros) | Handle `PermissionError`; tell users to edit data through the app only |
| Same-minute status changes mis-ordered | Order by `log_id`, never by `changed_at` |
| Time runs out | Steps 8–9 are optional; steps 0–7 are a complete system |
| Lesson code is Python 2 | Use `tkinter` (not `Tkinter`) and `print(x)`; test on Python 3 only |

## 9. Final checklist

- [ ] Every M requirement works through the GUI, with no `input()` or terminal output.
- [ ] All three roles tested; menus and permissions match §2.1.
- [ ] No computed value (total, balance, status) is saved to any CSV.
- [ ] Deleting a referenced record is blocked everywhere.
- [ ] A missing, empty, or corrupted data file never crashes the program.
- [ ] `python -m unittest` passes.
- [ ] Code split into modules, with comments (NFR-05).
- [ ] README: how to run (`python main.py`), default admin login, folder layout.
