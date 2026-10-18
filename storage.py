import os
import csv
import shutil
import datetime
import config
from models import TABLES
from errors import StorageError

# In-memory database cache
db = {}
counters = {}


def table_path(table_name):
    """Return absolute path for a table CSV file."""
    return os.path.join(config.DATA_DIR, f"{table_name}.csv")


def counters_path():
    """Return absolute path for ID counters CSV file."""
    return os.path.join(config.DATA_DIR, "counters.csv")


def init_storage():
    """Create data directories and missing tables, then load all records."""
    global db, counters
    db = {}
    counters = {}
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        os.makedirs(config.BACKUP_DIR, exist_ok=True)
    except OSError as e:
        raise StorageError(f"Cannot initialize storage directory: {e}")

    # Initialize counters file if missing
    cpath = counters_path()
    if not os.path.exists(cpath):
        try:
            with open(cpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["prefix", "last_number"])
        except OSError as e:
            raise StorageError(f"Cannot initialize counters file: {e}")

    # Load counters
    load_counters()

    # Initialize and load each table
    for name, fields in TABLES.items():
        tpath = table_path(name)
        if not os.path.exists(tpath):
            try:
                with open(tpath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
            except OSError as e:
                raise StorageError(f"Cannot create table {name}.csv: {e}")
        load_table(name)

    # Reconcile counters with highest IDs found in loaded tables
    sync_counters_with_db()


def load_counters():
    """Load counters from counters.csv into memory."""
    global counters
    counters = {}
    cpath = counters_path()
    if not os.path.exists(cpath):
        return
    try:
        with open(cpath, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    counters[row[0].strip()] = row[1].strip()
    except OSError as e:
        raise StorageError(f"Cannot load counters: {e}")


def sync_counters_with_db():
    """Ensure in-memory and on-disk counters match or exceed max IDs in tables."""
    changed = False
    for rows in db.values():
        for r in rows:
            for val in r.values():
                val_str = str(val).strip()
                if '-' in val_str:
                    prefix, num_part = val_str.rsplit('-', 1)
                    if num_part.isdigit():
                        num = int(num_part)
                        curr = int(counters.get(prefix, "0"))
                        if num > curr:
                            counters[prefix] = str(num)
                            changed = True
    if changed:
        save_counters()


def save_counters():
    """Atomically save counters to counters.csv."""
    cpath = counters_path()
    tmp = cpath + ".tmp"
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["prefix", "last_number"])
            for prefix, val in counters.items():
                writer.writerow([prefix, val])
        os.replace(tmp, cpath)
    except OSError as e:
        raise StorageError(f"Cannot save counters: {e}")


def next_id(prefix, width=4):
    """Generate the next unique ID that is never reused (FR-55)."""
    existing_nums = set()
    for rows in db.values():
        for r in rows:
            for val in r.values():
                val_str = str(val).strip()
                if val_str.startswith(f"{prefix}-"):
                    num_part = val_str[len(prefix)+1:]
                    if num_part.isdigit():
                        existing_nums.add(int(num_part))

    current = int(counters.get(prefix, "0"))
    if existing_nums:
        current = max(current, max(existing_nums))

    nxt = current + 1
    while nxt in existing_nums:
        nxt += 1

    counters[prefix] = str(nxt)
    save_counters()
    return f"{prefix}-{str(nxt).zfill(width)}"


def load_table(name):
    """Load records for table from CSV file into memory."""
    tpath = table_path(name)
    expected_fields = TABLES[name]
    try:
        with open(tpath, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or list(reader.fieldnames) != expected_fields:
                raise StorageError(f"Corrupted or invalid header in {name}.csv.")
            rows = []
            for line_no, row in enumerate(reader, start=2):
                if len(row) != len(expected_fields):
                    raise StorageError(f"Row {line_no} in {name}.csv has incorrect column count.")
                rows.append({k: (v if v is not None else "") for k, v in row.items()})
            db[name] = rows
    except OSError as e:
        raise StorageError(f"Cannot read {name}.csv: {e}")


def save_table(name):
    """Atomically write table from memory to CSV file (FR-54)."""
    if name not in TABLES:
        raise StorageError(f"Unknown table: {name}")
    tpath = table_path(name)
    tmp = tpath + ".tmp"
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=TABLES[name])
            writer.writeheader()
            writer.writerows(db.get(name, []))
        os.replace(tmp, tpath)
    except OSError as e:
        raise StorageError(f"Cannot save {name}.csv: {e}")


def get_rows(table_name):
    """Return in-memory list of dicts for given table."""
    if table_name not in db:
        load_table(table_name)
    return db[table_name]


def insert(table_name, row):
    """Append row and persist table."""
    if table_name not in db:
        db[table_name] = []
    # Make sure all fields present
    clean_row = {f: str(row.get(f, "")) for f in TABLES[table_name]}
    db[table_name].append(clean_row)
    save_table(table_name)
    return clean_row


def update(table_name, key_col, key_val, changes):
    """Update row matching key_col == key_val and persist."""
    rows = get_rows(table_name)
    found = False
    for r in rows:
        if str(r.get(key_col)) == str(key_val):
            for k, v in changes.items():
                if k in TABLES[table_name]:
                    r[k] = str(v)
            found = True
            break
    if not found:
        raise StorageError(f"Record with {key_col}={key_val} not found in {table_name}.")
    save_table(table_name)


def delete(table_name, key_col, key_val):
    """Delete row matching key_col == key_val and persist."""
    rows = get_rows(table_name)
    initial_len = len(rows)
    db[table_name] = [r for r in rows if str(r.get(key_col)) != str(key_val)]
    if len(db[table_name]) == initial_len:
        raise StorageError(f"Record with {key_col}={key_val} not found in {table_name}.")
    save_table(table_name)


def backup_data():
    """Copy entire data/ folder to backups/YYYYMMDD_HHMMSS/ (FR-50)."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(config.BACKUP_DIR, f"backup_{ts}")
    try:
        shutil.copytree(config.DATA_DIR, dest_dir)
        return dest_dir
    except OSError as e:
        raise StorageError(f"Backup failed: {e}")
