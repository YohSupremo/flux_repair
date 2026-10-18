import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED, RED_LIGHT, AMBER,
    BLUE, PURPLE, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_BOLD
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, status_badge,
    make_table, fill_table, labeled_field, guard, confirm
)
from logic.jobs import (
    job_details, change_status, assign_technician, record_diagnosis,
    add_service_to_job, remove_service_from_job, intake_receipt_text
)
from logic.parts import add_part_to_job, remove_part_from_job, list_parts
from logic.catalog import list_services
from logic.auth import get_technicians, can
from logic.billing import official_receipt_text
from models import TRANSITIONS
from utils import money
from gui.billing_ui import PaymentModal
from gui.receipt_ui import ReceiptViewerModal


class JobDetailsModal(tk.Toplevel):
    """
    Comprehensive Repair Dossier & Workbench (FR-25 - FR-31a, FR-34, FR-37 - FR-42).
    Complete control panel for diagnostics, technician assignment, status transitions,
    itemized services, inventory parts, and financial checkout.
    """
    def __init__(self, parent, job_id, acting_user, on_refresh_callback=None):
        super().__init__(parent)
        self.job_id = job_id
        self.acting_user = acting_user
        self.on_refresh_callback = on_refresh_callback

        self.title(f"Repair Dossier: Job {job_id}")
        self.geometry("1180x680")
        self.minsize(980, 500)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._load_data()
        self._build_ui()

        # Center on screen
        self.update_idletasks()
        try:
            mw = parent.winfo_width()
            mh = parent.winfo_height()
            mx = parent.winfo_rootx()
            my = parent.winfo_rooty()
            w = min(1180, parent.winfo_screenwidth() - 30)
            h = min(700, parent.winfo_screenheight() - 70)
            x = max(10, mx + (mw - w) // 2)
            y = max(10, my + (mh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            self.geometry("1180x680")

    def _load_data(self):
        self.details = job_details(self.job_id)
        self.job = self.details['job']
        self.cust = self.details['customer'] or {}
        self.tech = self.details['technician']
        self.status = self.details['status']
        self.bill = self.details['bill']

    def refresh(self):
        self._load_data()
        self._repopulate_ui()
        if self.on_refresh_callback:
            self.on_refresh_callback()

    def _build_ui(self):
        # Header Bar
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        # Left Info
        t_left = tk.Frame(top_bar, bg=BG_PANEL)
        t_left.pack(side="left")

        h_row = tk.Frame(t_left, bg=BG_PANEL)
        h_row.pack(anchor="w")

        tk.Label(h_row, text=f"Job Order {self.job_id}", font=("Segoe UI", 16, "bold"), fg=INK, bg=BG_PANEL).pack(side="left")

        # Priority badge
        prio_fg = RED if self.job['priority'] == 'Urgent' else MUTED
        prio_bg = RED_LIGHT if self.job['priority'] == 'Urgent' else BG_HOVER
        tk.Label(
            h_row,
            text=f"Priority: {self.job['priority']}",
            font=FONT_SMALL_BOLD,
            fg=prio_fg,
            bg=prio_bg,
            padx=8,
            pady=2,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE
        ).pack(side="left", padx=10)

        # Status badge
        self.status_pill = status_badge(h_row, self.status)
        self.status_pill.pack(side="left")

        # Subtitle
        dev_desc = f"{self.job['device_type']}, {self.job['brand']} {self.job['model']} (S/N: {self.job['serial_no']})"
        tk.Label(
            t_left,
            text=f"Client: {self.cust.get('name', 'N/A')} ({self.cust.get('contact_no', 'N/A')})   |   Device: {dev_desc}",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(4, 0))

        # Right Header Actions
        t_right = tk.Frame(top_bar, bg=BG_PANEL)
        t_right.pack(side="right")

        secondary_button(t_right, "Intake Receipt", command=self._show_intake_receipt).pack(side="left", padx=(0, 8))
        secondary_button(t_right, "Official Invoice", command=self._show_official_receipt).pack(side="left", padx=(0, 8))

        if can(self.acting_user['role'], 'billing') or (self.acting_user['role'] == 'Customer' and self.bill['balance'] > 0):
            pay_lbl = "Pay / Downpayment" if self.acting_user['role'] == 'Customer' else "Process Payment"
            primary_button(t_right, pay_lbl, command=self._open_payment_modal).pack(side="left")

        # Two-Column Scrollable Body Container
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg=BG, padx=16, pady=12)

        canvas_win = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_body_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_cfg(e):
            canvas.itemconfig(canvas_win, width=e.width)

        body.bind("<Configure>", _on_body_cfg)
        canvas.bind("<Configure>", _on_canvas_cfg)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_wheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Left Column (Device Info, Status Stepper, Tech Assignment, Diagnosis & Notes)
        left_col = tk.Frame(body, bg=BG)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Right Column (Services, Parts, Billing, Status History)
        right_col = tk.Frame(body, bg=BG)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- LEFT: Device & Symptom Card ---
        d_card = tk.Frame(left_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)
        d_card.pack(fill="x", pady=(0, 14))

        tk.Label(d_card, text="HARDWARE SYMPTOMS & INTAKE CONDITION", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))

        def _info_line(p, label, text):
            row = tk.Frame(p, bg=BG_PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL, width=16, anchor="w").pack(side="left")
            tk.Label(row, text=text, font=FONT_BODY, fg=INK, bg=BG_PANEL, anchor="w").pack(side="left")

        _info_line(d_card, "Reported Fault:", self.job['problem'])
        _info_line(d_card, "Arrival Condition:", self.job['device_condition'])
        _info_line(d_card, "Accessories:", ", ".join(self.details['accessories']) if self.details['accessories'] else "None")
        _info_line(d_card, "Date Received:", self.job['date_received'])
        _info_line(d_card, "Est. Completion:", self.job['est_completion'] or "N/A")

        # --- LEFT: Workflow Status Stepper (Staff / Admin / Tech only) ---
        if can(self.acting_user['role'], 'update_status'):
            st_card = tk.Frame(left_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)
            st_card.pack(fill="x", pady=(0, 14))

            tk.Label(st_card, text="WORKFLOW STATUS PROGRESSION", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))

            st_row = tk.Frame(st_card, bg=BG_PANEL)
            st_row.pack(fill="x")

            tk.Label(st_row, text="NEXT STATUS:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(0, 8))

            self.next_status_combo = ttk.Combobox(st_row, state="readonly", font=FONT_BODY, width=20)
            self.next_status_combo.pack(side="left", padx=(0, 8))

            primary_button(st_row, "Advance Status →", command=self._handle_status_change, padx=12, pady=4).pack(side="left")
        else:
            self.next_status_combo = None

        # --- LEFT: Technician Assignment ---
        if can(self.acting_user['role'], 'assign_tech'):
            tech_card = tk.Frame(left_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)
            tech_card.pack(fill="x", pady=(0, 14))

            tk.Label(tech_card, text="ASSIGNED BENCH TECHNICIAN", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))

            t_row = tk.Frame(tech_card, bg=BG_PANEL)
            t_row.pack(fill="x")

            self.all_techs = get_technicians()
            self.tech_combo = ttk.Combobox(t_row, state="readonly", font=FONT_BODY, width=24)
            tech_names = ["Unassigned"] + [f"{t['user_id']}: {t['full_name']}" for t in self.all_techs]
            self.tech_combo['values'] = tech_names

            # Set current tech
            current_tech_str = "Unassigned"
            if self.tech:
                current_tech_str = f"{self.tech['user_id']}: {self.tech['full_name']}"
            self.tech_combo.set(current_tech_str)
            self.tech_combo.pack(side="left", padx=(0, 8))

            secondary_button(t_row, "Update Assignment", command=self._handle_assign_tech, padx=10, pady=4).pack(side="left")

        # --- LEFT: Diagnosis & Technical Notes ---
        can_diag = can(self.acting_user['role'], 'record_diagnosis')
        diag_card = tk.Frame(left_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)
        diag_card.pack(fill="both", expand=True)

        tk.Label(diag_card, text="DIAGNOSTIC VERDICT & BENCH NOTES", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

        tk.Label(diag_card, text="Root Cause Diagnosis:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(2, 2))
        self.diag_entry = tk.Entry(diag_card, font=FONT_BODY, bg=BG_INPUT if can_diag else BG_HOVER, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.diag_entry.insert(0, self.job['diagnosis'])
        if not can_diag:
            self.diag_entry.configure(state="readonly")
        self.diag_entry.pack(fill="x", pady=(0, 8))

        tk.Label(diag_card, text="Detailed Repair & Rework Notes:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(2, 2))
        self.notes_text = tk.Text(diag_card, height=4, font=FONT_BODY, bg=BG_INPUT if can_diag else BG_HOVER, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.notes_text.insert("1.0", self.job['notes'])
        if not can_diag:
            self.notes_text.configure(state="disabled")
        self.notes_text.pack(fill="both", expand=True, pady=(0, 8))

        if can_diag:
            secondary_button(diag_card, "Save Diagnostic Notes", command=self._handle_save_notes, padx=12, pady=5).pack(anchor="e")

        # --- RIGHT: Services Attached ---
        s_card = tk.Frame(right_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s_card.pack(fill="x", pady=(0, 12))

        s_head = tk.Frame(s_card, bg=BG_PANEL)
        s_head.pack(fill="x", pady=(0, 6))
        tk.Label(s_head, text="LABOR & REPAIR SERVICES", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(side="left")

        can_modify_job = (self.acting_user['role'] in ('Admin', 'Staff', 'Technician')) and (self.status not in ('Completed', 'Released', 'Cancelled'))
        if can_modify_job:
            s_btns = tk.Frame(s_head, bg=BG_PANEL)
            s_btns.pack(side="right")
            secondary_button(s_btns, "+ Add Service", command=self._add_service_dialog, padx=8, pady=2).pack(side="left", padx=(0, 4))
            secondary_button(s_btns, "Remove", command=self._remove_selected_service, padx=8, pady=2).pack(side="left")

        s_cols = ("service_id", "name", "price")
        s_heads = ("ID", "Service Scope", "Price")
        self.s_table_frame, self.s_tree = make_table(s_card, s_cols, s_heads, (60, 240, 90))
        self.s_tree.configure(height=3)
        self.s_table_frame.pack(fill="x")

        # --- RIGHT: Hardware Parts Used ---
        p_card = tk.Frame(right_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        p_card.pack(fill="x", pady=(0, 12))

        p_head = tk.Frame(p_card, bg=BG_PANEL)
        p_head.pack(fill="x", pady=(0, 6))
        tk.Label(p_head, text="HARDWARE PARTS & COMPONENTS", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(side="left")

        if can_modify_job:
            p_btns = tk.Frame(p_head, bg=BG_PANEL)
            p_btns.pack(side="right")
            secondary_button(p_btns, "+ Add Part", command=self._add_part_dialog, padx=8, pady=2).pack(side="left", padx=(0, 4))
            secondary_button(p_btns, "Remove", command=self._remove_selected_part, padx=8, pady=2).pack(side="left")

        p_cols = ("part_id", "name", "qty", "price", "total")
        p_heads = ("ID", "Component", "Qty", "Unit Price", "Total")
        self.p_table_frame, self.p_tree = make_table(p_card, p_cols, p_heads, (55, 170, 45, 80, 80))
        self.p_tree.configure(height=3)
        self.p_table_frame.pack(fill="x")

        # --- RIGHT: Financial Ledger ---
        fin_card = tk.Frame(right_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        fin_card.pack(fill="x", pady=(0, 12))

        tk.Label(fin_card, text="ACCOUNT LEDGER & BALANCE DUE", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

        fin_grid = tk.Frame(fin_card, bg=BG_PANEL)
        fin_grid.pack(fill="x")

        self.lbl_srv_total = tk.Label(fin_grid, text="Services: ₱0.00", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL)
        self.lbl_srv_total.pack(side="left", padx=(0, 16))

        self.lbl_part_total = tk.Label(fin_grid, text="Parts: ₱0.00", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL)
        self.lbl_part_total.pack(side="left", padx=(0, 16))

        self.lbl_grand_total = tk.Label(fin_grid, text="Total: ₱0.00", font=FONT_SMALL_BOLD, fg=INK, bg=BG_PANEL)
        self.lbl_grand_total.pack(side="left", padx=(0, 16))

        self.lbl_paid_total = tk.Label(fin_grid, text="Paid: ₱0.00", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL)
        self.lbl_paid_total.pack(side="left", padx=(0, 16))

        self.lbl_bal_total = tk.Label(fin_grid, text="Balance: ₱0.00", font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_PANEL)
        self.lbl_bal_total.pack(side="right")

        # --- RIGHT: Status History Audit Trail ---
        h_card = tk.Frame(right_col, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        h_card.pack(fill="both", expand=True)

        tk.Label(h_card, text="STATUS AUDIT TRAIL", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

        h_cols = ("log_id", "status", "changed_at", "actor_name")
        h_heads = ("Log ID", "Status", "Timestamp", "Staff / Tech")
        self.h_table_frame, self.h_tree = make_table(h_card, h_cols, h_heads, (70, 120, 130, 140))
        self.h_tree.configure(height=3)
        self.h_table_frame.pack(fill="both", expand=True)

        self._repopulate_ui()

    def _repopulate_ui(self):
        # Update allowed transitions in combobox
        if self.next_status_combo:
            allowed = TRANSITIONS.get(self.status, [])
            self.next_status_combo['values'] = allowed
            if allowed:
                self.next_status_combo.current(0)
            else:
                self.next_status_combo.set("No further transitions (Final)")

        # Services table
        s_rows = [
            {'service_id': s['service_id'], 'name': s['name'], 'price': money(s['price'])}
            for s in self.details['services']
        ]
        fill_table(self.s_tree, s_rows, ("service_id", "name", "price"))

        # Parts table
        p_rows = [
            {
                'part_id': p['part_id'],
                'name': p['name'],
                'qty': p['quantity_used'],
                'price': money(p['unit_price']),
                'total': money(p['line_total'])
            }
            for p in self.details['parts']
        ]
        fill_table(self.p_tree, p_rows, ("part_id", "name", "qty", "price", "total"))

        # Financial totals
        b = self.bill
        self.lbl_srv_total.configure(text=f"Services: {money(b['services'])}")
        self.lbl_part_total.configure(text=f"Parts: {money(b['parts'])}")
        self.lbl_grand_total.configure(text=f"Total: {money(b['total'])}")
        self.lbl_paid_total.configure(text=f"Paid: {money(b['paid'])}")

        bal_fg = EMERALD if b['balance'] == Decimal('0.00') else RED
        self.lbl_bal_total.configure(text=f"Balance: {money(b['balance'])}", fg=bal_fg)

        # Audit history
        h_rows = [
            {
                'log_id': h['log_id'],
                'status': h['status'],
                'changed_at': h['changed_at'],
                'actor_name': h['actor_name']
            }
            for h in self.details['history']
        ]
        fill_table(self.h_tree, h_rows, ("log_id", "status", "changed_at", "actor_name"))

    @guard
    def _handle_status_change(self):
        new_st = self.next_status_combo.get()
        if not new_st or "Final" in new_st:
            return

        cancel_reason = None
        if new_st == 'Cancelled':
            cancel_reason = simpledialog.askstring("Cancellation Reason", "Please state why this job is being cancelled:")
            if not cancel_reason:
                messagebox.showwarning("Notice", "Cancellation reason is required.")
                return

        change_status(self.job_id, new_st, self.acting_user, cancel_reason=cancel_reason)
        messagebox.showinfo("Status Updated", f"Job {self.job_id} transitioned to '{new_st}'.")

        # FR-32 Completion prompt
        if new_st == 'Completed':
            c_name = self.cust.get('name', 'the customer')
            c_phone = self.cust.get('contact_no', '')
            messagebox.showinfo(
                "Customer Completion Notice (FR-32)",
                f"Repair is complete!\n\nPlease contact {c_name} at {c_phone} to notify them that their device is ready for pickup."
            )

        self.refresh()

    @guard
    def _handle_assign_tech(self):
        sel_idx = self.tech_combo.current()
        tech_id = ""
        if sel_idx > 0 and (sel_idx - 1) < len(self.all_techs):
            tech_id = self.all_techs[sel_idx - 1]['user_id']

        assign_technician(self.job_id, tech_id, self.acting_user)
        messagebox.showinfo("Assigned", "Technician assignment updated.")
        self.refresh()

    @guard
    def _handle_save_notes(self):
        diag = self.diag_entry.get()
        notes = self.notes_text.get("1.0", "end")
        record_diagnosis(self.job_id, diag, notes, self.acting_user)
        messagebox.showinfo("Saved", "Diagnostic notes updated.")
        self.refresh()

    def _add_service_dialog(self):
        all_s = list_services()
        SelectServiceModal(self, all_s, self._on_service_selected)

    @guard
    def _on_service_selected(self, service_id):
        add_service_to_job(self.job_id, service_id, self.acting_user)
        self.refresh()

    @guard
    def _remove_selected_service(self):
        sel = self.s_tree.selection()
        if not sel:
            messagebox.showwarning("Notice", "Select a service to remove.")
            return
        sid = self.s_tree.item(sel[0], "values")[0]
        if confirm("Confirm", f"Remove service {sid} from this job?"):
            remove_service_from_job(self.job_id, sid, self.acting_user)
            self.refresh()

    def _add_part_dialog(self):
        all_p = list_parts()
        SelectPartModal(self, all_p, self._on_part_selected)

    @guard
    def _on_part_selected(self, part_id, qty):
        add_part_to_job(self.job_id, part_id, qty, self.acting_user)
        self.refresh()

    @guard
    def _remove_selected_part(self):
        sel = self.p_tree.selection()
        if not sel:
            messagebox.showwarning("Notice", "Select a part to remove.")
            return
        pid = self.p_tree.item(sel[0], "values")[0]
        if confirm("Confirm", f"Remove component {pid} from this job and restore stock?"):
            remove_part_from_job(self.job_id, pid, self.acting_user)
            self.refresh()

    def _open_payment_modal(self):
        PaymentModal(self, self.job_id, self.acting_user, on_payment_recorded=self.refresh)

    def _show_intake_receipt(self):
        text = intake_receipt_text(self.job_id)
        ReceiptViewerModal(self, f"Intake Ticket: {self.job_id}", text, f"{self.job_id}_intake.txt")

    def _show_official_receipt(self):
        text = official_receipt_text(self.job_id)
        ReceiptViewerModal(self, f"Official Invoice: {self.job_id}", text, f"{self.job_id}_official.txt")


class SelectServiceModal(tk.Toplevel):
    """Picker dialog to attach an item from the service catalog to a job."""
    def __init__(self, parent, services, on_select_callback):
        super().__init__(parent)
        self.services = services
        self.on_select_callback = on_select_callback

        self.title("Select Service from Catalog")
        self.geometry("540x420")
        self.minsize(480, 320)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=16, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="Attach Repair Service", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        # Pin bottom action bar first so buttons are never cut off
        bot = tk.Frame(self, bg=BG_PANEL, padx=16, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Attach Service", command=self._confirm_select).pack(side="right")

        body = tk.Frame(self, bg=BG, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        cols = ("service_id", "name", "price")
        heads = ("ID", "Service Name", "Default Price")
        self.t_frame, self.tree = make_table(body, cols, heads, (70, 260, 110))
        self.t_frame.pack(fill="both", expand=True)

        rows = [{'service_id': s['service_id'], 'name': s['name'], 'price': money(s['price'])} for s in self.services]
        fill_table(self.tree, rows, cols)

    def _confirm_select(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Notice", "Please select a service.")
            return
        sid = self.tree.item(sel[0], "values")[0]
        self.on_select_callback(sid)
        self.destroy()


class SelectPartModal(tk.Toplevel):
    """Picker dialog to allocate parts from inventory to a job."""
    def __init__(self, parent, parts, on_select_callback):
        super().__init__(parent)
        self.parts = parts
        self.on_select_callback = on_select_callback

        self.title("Allocate Hardware Part from Stock")
        self.geometry("560x480")
        self.minsize(500, 380)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=16, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="Allocate Component from Inventory", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        # 1. Pin bottom action bar first so buttons can NEVER be clipped
        bot = tk.Frame(self, bg=BG_PANEL, padx=16, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Add Component to Job", command=self._confirm_select).pack(side="right")

        # 2. Pin quantity control above the bottom bar
        q_box = tk.Frame(self, bg=BG, padx=16, pady=8)
        q_box.pack(fill="x", side="bottom")
        tk.Label(q_box, text="Quantity to Use on Job:", font=FONT_SMALL_BOLD, fg=INK, bg=BG).pack(side="left", padx=(0, 8))
        self.qty_spin = tk.Spinbox(q_box, from_=1, to=100, font=FONT_BODY, width=6)
        self.qty_spin.pack(side="left")

        # 3. Middle area expands to fill remaining space
        body = tk.Frame(self, bg=BG, padx=16, pady=8)
        body.pack(fill="both", expand=True, pady=(4, 0))

        cols = ("part_id", "name", "qty", "price")
        heads = ("ID", "Component", "Stock Available", "Unit Price")
        self.t_frame, self.tree = make_table(body, cols, heads, (70, 220, 110, 100))
        self.t_frame.pack(fill="both", expand=True)

        rows = [
            {'part_id': p['part_id'], 'name': p['name'], 'qty': p['quantity'], 'price': money(p['unit_price'])}
            for p in self.parts
        ]
        fill_table(self.tree, rows, cols)

    def _confirm_select(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Notice", "Please select a component.")
            return
        pid = self.tree.item(sel[0], "values")[0]
        qty = self.qty_spin.get()
        self.on_select_callback(pid, qty)
        self.destroy()
