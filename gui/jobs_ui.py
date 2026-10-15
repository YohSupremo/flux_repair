import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, RED, AMBER, FONT_TITLE, FONT_HEADING,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, make_table, fill_table, guard
)
from logic.jobs import list_jobs, get_rows
from logic.auth import can
from models import STATUSES
from gui.job_form import JobIntakeModal
from gui.job_details_ui import JobDetailsModal
from gui.billing_ui import PaymentModal
from utils import money


class JobsView(tk.Frame):
    """
    Job Orders Management & Registry (FR-26, FR-30, FR-31).
    Displays tickets table, status filter tabs, search filter, and dossier launcher.
    """
    def __init__(self, parent, acting_user):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        is_customer = (self.acting_user['role'] == 'Customer')
        main_title = "My Repair Orders" if is_customer else "Repair Job Orders"
        tk.Label(title_box, text=main_title, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        if is_customer:
            sub_text = "Real-time tracking of your registered hardware, diagnostic assessments, repair progress, and receipts."
        elif self.acting_user['role'] == 'Technician':
            sub_text = f"Showing assigned repair jobs for Technician: {self.acting_user['full_name']} (FR-26)."
        else:
            sub_text = "Master ticket registry: tracking device intake, technician assignment, status progression, and billing."
        tk.Label(title_box, text=sub_text, font=FONT_SMALL, fg=DIM, bg=BG_PANEL).pack(anchor="w")

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        if is_customer:
            primary_button(btn_box, "+ Request Repair", command=self._open_intake_modal).pack(side="left")
        elif can(self.acting_user['role'], 'create_jobs'):
            primary_button(btn_box, "+ New Job Order", command=self._open_intake_modal).pack(side="left")

        # Filters Bar
        filter_bar = tk.Frame(self, bg=BG, padx=24, pady=12)
        filter_bar.pack(fill="x")

        # Status filter
        st_box = tk.Frame(filter_bar, bg=BG)
        st_box.pack(side="left", padx=(0, 16))
        tk.Label(st_box, text="Status Filter:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG).pack(side="left", padx=(0, 6))

        self.status_combo = ttk.Combobox(st_box, state="readonly", font=FONT_BODY, width=16)
        self.status_combo['values'] = ["All"] + list(STATUSES)
        self.status_combo.set("All")
        self.status_combo.pack(side="left")
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Search Bar
        s_box = tk.Frame(filter_bar, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=8, pady=4)
        s_box.pack(side="left", fill="x", expand=True)

        tk.Label(s_box, text="Search Tickets:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(4, 8))
        self.search_entry = tk.Entry(s_box, font=FONT_BODY, bg=BG_PANEL, fg=INK, bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        clear_btn = secondary_button(filter_bar, "Clear", command=self._clear_filters, padx=10, pady=4)
        clear_btn.pack(side="left", padx=(8, 0))

        # Bottom Action Bar (Packed side="bottom" first to guarantee it is NEVER pushed off screen)
        bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
        bottom_bar.pack(fill="x", side="bottom")

        details_btn_text = "View Repair Details / Status" if is_customer else "Open Job Dossier / Workbench"
        secondary_button(bottom_bar, details_btn_text, command=self._open_details_modal).pack(side="left", padx=(0, 8))

        if can(self.acting_user['role'], 'billing') or is_customer:
            btn_txt = "Pay / Downpayment" if is_customer else "Process Payment"
            secondary_button(bottom_bar, btn_txt, command=self._open_payment_modal).pack(side="left", padx=(0, 8))

        secondary_button(bottom_bar, "Refresh List", command=self.refresh).pack(side="right")

        # Main Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=20)
        table_wrap.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("job_id", "date_received", "customer", "device", "priority", "status", "payment", "technician")
        heads = ("Job ID", "Date", "Account Name" if is_customer else "Customer", "Device Specification", "Priority", "Status", "Payment / Balance Due", "Tech")
        widths = (80, 110, 140, 190, 70, 110, 150, 110)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

        # Double click to open dossier
        self.tree.bind("<Double-1>", lambda e: self._open_details_modal())

    def refresh(self):
        st_filter = self.status_combo.get()
        q = self.search_entry.get().strip()

        # Technician role filter & Customer role filter
        tech_id = self.acting_user['user_id'] if self.acting_user['role'] == 'Technician' else None
        cust_filter = self.acting_user['full_name'] if self.acting_user['role'] == 'Customer' else None

        jobs = list_jobs(status_filter=st_filter, search_text=q, technician_id=tech_id, customer_name_filter=cust_filter)
        users_map = {u['user_id']: u['full_name'] for u in get_rows('users')}
        from logic.billing import compute_bill

        rows = []
        for j in jobs:
            t_name = users_map.get(j.get('technician_id'), "Unassigned")
            b = compute_bill(j['job_id'])
            if b['total'] == Decimal('0.00'):
                pay_str = "Pending Diagnosis Quote"
            elif b['balance'] == Decimal('0.00'):
                pay_str = "Paid in Full (₱0.00 due)"
            elif b['paid'] > Decimal('0.00'):
                pay_str = f"Partial ({money(b['balance'])} due)"
            else:
                pay_str = f"Unpaid ({money(b['balance'])} due)"

            rows.append({
                'job_id': j['job_id'],
                'date_received': j['date_received'],
                'customer': j['customer_name'],
                'device': f"{j['device_type']} {j['brand']} {j['model']}",
                'priority': j['priority'],
                'status': j['status'],
                'payment': pay_str,
                'technician': t_name
            })

        cols = ("job_id", "date_received", "customer", "device", "priority", "status", "payment", "technician")
        fill_table(self.tree, rows, cols)

    def _clear_filters(self):
        self.status_combo.set("All")
        self.search_entry.delete(0, "end")
        self.refresh()

    def _get_selected_job_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a job order from the table.")
            return None
        return self.tree.item(sel[0], "values")[0]

    def _open_intake_modal(self):
        JobIntakeModal(self, self.acting_user, on_job_created_callback=self.refresh)

    def _open_details_modal(self, job_id=None):
        jid = job_id or self._get_selected_job_id()
        if jid:
            JobDetailsModal(self, jid, self.acting_user, on_refresh_callback=self.refresh)

    def _open_payment_modal(self):
        jid = self._get_selected_job_id()
        if jid:
            PaymentModal(self, jid, self.acting_user, on_payment_recorded=self.refresh)
