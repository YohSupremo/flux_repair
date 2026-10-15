import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, RED, AMBER, BLUE, FONT_TITLE, FONT_HEADING,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, make_table, fill_table, guard
)
from logic.reports import status_counts, pending_jobs, sales_report, export_rows_to_csv, export_text_report
from storage import backup_data
from logic.auth import can
from utils import money
from gui.job_details_ui import JobDetailsModal


class ReportsView(tk.Frame):
    """
    Analytics, Sales Reports, and System Maintenance (FR-43 - FR-46, FR-50).
    Features status counters, revenue aggregations, pending jobs monitor, and CSV exports.
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

        tk.Label(title_box, text="Reports & Financial Analytics", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Workshop status breakdown, financial revenue reports, pending tickets, and system backups.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        if can(self.acting_user['role'], 'backup'):
            backup_btn = secondary_button(btn_box, "Backup System Data", command=self._handle_backup)
            backup_btn.pack(side="left", padx=(0, 8))

        # Main scrollable canvas container
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG, padx=20, pady=12)

        canvas_win = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_cfg(e):
            canvas.itemconfig(canvas_win, width=e.width)

        scrollable_frame.bind("<Configure>", _on_frame_cfg)
        canvas.bind("<Configure>", _on_canvas_cfg)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_wheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # --- Section 1: Real-time Status Metric Cards ---
        tk.Label(scrollable_frame, text="WORKSHOP STATUS DISTRIBUTION", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG).pack(anchor="w", pady=(0, 8))

        self.cards_row = tk.Frame(scrollable_frame, bg=BG)
        self.cards_row.pack(fill="x", pady=(0, 16))

        self.metric_labels = {}
        statuses = ["Received", "Diagnosing", "Waiting for Parts", "Under Repair", "Completed", "Released", "Cancelled"]
        for st in statuses:
            card = tk.Frame(self.cards_row, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=12, pady=10)
            card.pack(side="left", fill="both", expand=True, padx=4)

            tk.Label(card, text=st.upper(), font=("Segoe UI", 8, "bold"), fg=MUTED, bg=BG_PANEL).pack(anchor="w")
            lbl = tk.Label(card, text="0", font=("Segoe UI", 16, "bold"), fg=INK, bg=BG_PANEL)
            lbl.pack(anchor="w", pady=(2, 0))
            self.metric_labels[st] = lbl

        # --- Section 2: Sales Revenue Report ---
        sales_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=16)
        sales_card.pack(fill="x", pady=(0, 16))

        s_head = tk.Frame(sales_card, bg=BG_PANEL)
        s_head.pack(fill="x", pady=(0, 12))

        tk.Label(s_head, text="REVENUE & PAYMENT LOGS", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(side="left")

        # Date Filters
        f_box = tk.Frame(s_head, bg=BG_PANEL)
        f_box.pack(side="right")

        tk.Label(f_box, text="From:", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(0, 4))
        self.start_date_entry = tk.Entry(f_box, width=11, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        today = datetime.date.today()
        first_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        self.start_date_entry.insert(0, first_of_month)
        self.start_date_entry.pack(side="left", padx=(0, 8))

        tk.Label(f_box, text="To:", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(0, 4))
        self.end_date_entry = tk.Entry(f_box, width=11, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.end_date_entry.insert(0, today.strftime("%Y-%m-%d"))
        self.end_date_entry.pack(side="left", padx=(0, 8))

        secondary_button(f_box, "Filter", command=self._refresh_sales, padx=10, pady=3).pack(side="left")

        # Payments table
        pay_cols = ("payment_id", "job_id", "customer_name", "amount", "method", "payment_date")
        pay_heads = ("Payment ID", "Job ID", "Customer Name", "Amount (₱)", "Method", "Date & Time")
        self.pay_table_frame, self.pay_tree = make_table(sales_card, pay_cols, pay_heads, (90, 80, 200, 110, 80, 140))
        self.pay_tree.configure(height=5)
        self.pay_table_frame.pack(fill="x", pady=(0, 10))

        # Revenue Readout
        rev_bar = tk.Frame(sales_card, bg=BG_HOVER, padx=14, pady=10)
        rev_bar.pack(fill="x")

        self.rev_lbl = tk.Label(rev_bar, text="Total Revenue: ₱0.00", font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_HOVER)
        self.rev_lbl.pack(side="left")

        self.tx_count_lbl = tk.Label(rev_bar, text="Transactions: 0", font=FONT_SMALL, fg=MUTED, bg=BG_HOVER)
        self.tx_count_lbl.pack(side="left", padx=(16, 0))

        export_csv_btn = secondary_button(rev_bar, "Export CSV", command=self._export_sales_csv, padx=10, pady=2)
        export_csv_btn.pack(side="right")

        # --- Section 3: Pending Jobs Monitor ---
        pend_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=16)
        pend_card.pack(fill="x", pady=(0, 16))

        p_head = tk.Frame(pend_card, bg=BG_PANEL)
        p_head.pack(fill="x", pady=(0, 12))

        tk.Label(p_head, text="PENDING & UNFINISHED TICKETS (FR-45)", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(side="left")

        export_pend_btn = secondary_button(p_head, "Export Pending CSV", command=self._export_pending_csv, padx=10, pady=2)
        export_pend_btn.pack(side="right")

        p_cols = ("job_id", "customer", "device", "priority", "status", "date_received")
        p_heads = ("Job ID", "Customer", "Device Specification", "Priority", "Status", "Date Received")
        self.pend_table_frame, self.pend_tree = make_table(pend_card, p_cols, p_heads, (80, 180, 220, 80, 120, 130))
        self.pend_tree.configure(height=5)
        self.pend_table_frame.pack(fill="x")

        # Open job on double click
        self.pend_tree.bind("<Double-1>", lambda e: self._open_selected_pending_job())

    def refresh(self):
        # Update status counters
        counts = status_counts()
        for st, lbl in self.metric_labels.items():
            lbl.configure(text=str(counts.get(st, 0)))

        self._refresh_sales()
        self._refresh_pending()

    @guard
    def _refresh_sales(self):
        s_date = self.start_date_entry.get().strip() or None
        e_date = self.end_date_entry.get().strip() or None

        self.current_sales = sales_report(s_date, e_date)
        rows = [
            {
                'payment_id': p['payment_id'],
                'job_id': p['job_id'],
                'customer_name': p['customer_name'],
                'amount': money(p['amount']),
                'method': p['method'],
                'payment_date': p['payment_date']
            }
            for p in self.current_sales['payments']
        ]
        fill_table(self.pay_tree, rows, ("payment_id", "job_id", "customer_name", "amount", "method", "payment_date"))

        self.rev_lbl.configure(text=f"Total Revenue: {money(self.current_sales['total_revenue'])}")
        self.tx_count_lbl.configure(text=f"Transactions: {self.current_sales['payment_count']}")

    def _refresh_pending(self):
        p_jobs = pending_jobs()
        rows = [
            {
                'job_id': j['job_id'],
                'customer': j['customer_name'],
                'device': f"{j['device_type']} {j['brand']} {j['model']}",
                'priority': j['priority'],
                'status': j['status'],
                'date_received': j['date_received']
            }
            for j in p_jobs
        ]
        fill_table(self.pend_tree, rows, ("job_id", "customer", "device", "priority", "status", "date_received"))

    def _open_selected_pending_job(self):
        sel = self.pend_tree.selection()
        if not sel:
            return
        jid = self.pend_tree.item(sel[0], "values")[0]
        JobDetailsModal(self, jid, self.acting_user, on_refresh_callback=self.refresh)

    @guard
    def _export_sales_csv(self):
        if not hasattr(self, 'current_sales') or not self.current_sales['payments']:
            messagebox.showinfo("Export", "No sales records to export for this period.")
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"sales_report_{ts}.csv"
        cols = ['payment_id', 'job_id', 'customer_name', 'amount', 'method', 'payment_date', 'received_by']
        path = export_rows_to_csv(self.current_sales['payments'], cols, fn)
        messagebox.showinfo("Export Successful", f"Sales report exported to:\n{path}")

    @guard
    def _export_pending_csv(self):
        p_jobs = pending_jobs()
        if not p_jobs:
            messagebox.showinfo("Export", "No pending job orders found.")
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"pending_jobs_{ts}.csv"
        cols = ['job_id', 'customer_name', 'device_type', 'brand', 'model', 'serial_no', 'priority', 'status', 'date_received']
        path = export_rows_to_csv(p_jobs, cols, fn)
        messagebox.showinfo("Export Successful", f"Pending jobs exported to:\n{path}")

    @guard
    def _handle_backup(self):
        dest = backup_data()
        messagebox.showinfo("Backup Completed", f"All database files successfully backed up to:\n{dest}")
