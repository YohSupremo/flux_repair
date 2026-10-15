import os
import csv
from decimal import Decimal
from datetime import datetime
from storage import get_rows
from models import STATUSES
from config import EXPORT_DIR, DATE_FMT
from utils import money, parse_date


def status_counts():
    """Count job orders grouped by current status (FR-43)."""
    from logic.jobs import status_map
    s_map = status_map()
    counts = {s: 0 for s in STATUSES}
    for st in s_map.values():
        if st in counts:
            counts[st] += 1
    return counts


def pending_jobs():
    """Return all unfinished/active jobs (FR-45)."""
    from logic.jobs import list_jobs
    all_j = list_jobs()
    return [j for j in all_j if j['status'] not in ('Released', 'Cancelled')]


def sales_report(start_date=None, end_date=None):
    """
    Generate sales revenue report from recorded payments within date range (FR-44).
    Dates should be 'YYYY-MM-DD' strings or None.
    """
    payments = get_rows('payments')
    customers = {c['customer_id']: c['name'] for c in get_rows('customers')}
    jobs = {j['job_id']: j for j in get_rows('jobs')}

    s_dt = parse_date(start_date, "Start date") if start_date else None
    e_dt = parse_date(end_date, "End date") if end_date else None

    filtered = []
    total_revenue = Decimal('0.00')

    for p in payments:
        p_date_str = p['payment_date'].split(' ')[0]
        try:
            p_dt = datetime.strptime(p_date_str, DATE_FMT).date()
        except ValueError:
            continue

        if s_dt and p_dt < s_dt:
            continue
        if e_dt and p_dt > e_dt:
            continue

        amt = Decimal(p['amount'])
        total_revenue += amt

        job = jobs.get(p['job_id'], {})
        cust_name = customers.get(job.get('customer_id'), 'Unknown')

        filtered.append({
            'payment_id': p['payment_id'],
            'job_id': p['job_id'],
            'customer_name': cust_name,
            'amount': p['amount'],
            'method': p['method'],
            'payment_date': p['payment_date'],
            'received_by': p['received_by']
        })

    filtered.sort(key=lambda x: x['payment_date'], reverse=True)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'payment_count': len(filtered),
        'payments': filtered
    }


def export_rows_to_csv(rows, columns, filename):
    """Export tabular rows to CSV file in exports/ folder (FR-46)."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    fpath = os.path.join(EXPORT_DIR, filename)
    with open(fpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in rows:
            clean_r = {c: r.get(c, "") for c in columns}
            writer.writerow(clean_r)
    return fpath


def export_text_report(content, filename):
    """Export formatted text report in exports/ folder."""
    os.makedirs(EXPORT_DIR, exist_ok=True)
    fpath = os.path.join(EXPORT_DIR, filename)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return fpath
