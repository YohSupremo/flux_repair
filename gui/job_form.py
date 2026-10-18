import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, FONT_TITLE, FONT_HEADING,
    FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import primary_button, secondary_button, labeled_field, guard
from logic.customers import list_customers
from logic.catalog import list_services
from logic.auth import get_technicians
from logic.jobs import create_job, intake_receipt_text
from models import DEVICE_TYPES, PRIORITIES
from utils import money
from gui.receipt_ui import ReceiptViewerModal


class JobIntakeModal(tk.Toplevel):
    """
    Job Order Intake Window (FR-13 - FR-20, FR-23, FR-24).
    Handles customer selection, hardware attributes, accessory logging, and initial service scoping.
    """
    def __init__(self, parent, acting_user, on_job_created_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.on_job_created_callback = on_job_created_callback
        self.is_customer = (self.acting_user['role'] == 'Customer')

        win_title = "Request Device Repair : FLUX Atelier" if self.is_customer else "New Repair Job Intake : FLUX Atelier"
        self.title(win_title)
        self.geometry("780x820")
        self.minsize(680, 720)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self.customers_list = list_customers()
        self.services_list = list_services()
        self.technicians_list = get_technicians()

        self._build_ui()

        # Center dialog nicely on screen
        self.update_idletasks()
        try:
            mw = parent.winfo_width()
            mh = parent.winfo_height()
            mx = parent.winfo_rootx()
            my = parent.winfo_rooty()
            w = 720
            h = min(580, max(460, mh - 50))
            x = max(30, mx + (mw - w) // 2)
            y = max(20, my + (mh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            self.geometry("720x580")

    def _build_ui(self):
        # Header
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        head_title = "Request Device Repair" if self.is_customer else "Intake Device: New Job Order"
        head_sub = "Submit your device specifications and reported symptoms to request workshop repair." if self.is_customer else "Initial ticket logging: record physical condition, customer symptoms, and preliminary catalog scope."

        tk.Label(top_bar, text=head_title, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            top_bar,
            text=head_sub,
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(1, 0))

        # Bottom Action Bar (Packed first at bottom to ensure it is NEVER obscured!)
        bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bottom_bar.pack(fill="x", side="bottom")

        secondary_button(bottom_bar, "Cancel", command=self.destroy).pack(side="left")
        submit_btn_txt = "Submit Repair Request →" if self.is_customer else "Generate Ticket & Print Receipt →"
        primary_button(bottom_bar, submit_btn_txt, command=self._submit_job).pack(side="right")

        # Main Scrollable Body
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG, padx=18, pady=12)

        canvas_win = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_config(e):
            canvas.itemconfig(canvas_win, width=e.width)

        scrollable_frame.bind("<Configure>", _on_frame_config)
        canvas.bind("<Configure>", _on_canvas_config)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Mouse wheel support
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Section 1: Customer & Priority
        s1 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s1.pack(fill="x", pady=(0, 10))

        tk.Label(s1, text="1. CLIENT & PRIORITY LEVEL", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))

        c_row = tk.Frame(s1, bg=BG_PANEL)
        c_row.pack(fill="x")

        # Customer column
        c_box = tk.Frame(c_row, bg=BG_PANEL)
        c_box.pack(side="left", fill="x", expand=True, padx=(0, 14))

        if self.is_customer:
            tk.Label(c_box, text="CUSTOMER ACCOUNT", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w")
            tk.Label(c_box, text=f"{self.acting_user['full_name']} (You)", font=FONT_BODY_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(1, 4))

            tk.Label(c_box, text="CONTACT NUMBER *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(2, 2))
            self.phone_entry = tk.Entry(c_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
            c_rec = next((c for c in self.customers_list if c['name'].strip().lower() == self.acting_user['full_name'].strip().lower()), None)
            if c_rec and c_rec.get('contact_no'):
                self.phone_entry.insert(0, c_rec['contact_no'])
            self.phone_entry.pack(fill="x")
        else:
            tk.Label(c_box, text="SELECT CUSTOMER *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
            self.cust_combo = ttk.Combobox(c_box, state="readonly", font=FONT_BODY)
            c_display = [f"{c['customer_id']}: {c['name']} ({c['contact_no']})" for c in self.customers_list]
            self.cust_combo['values'] = c_display
            if c_display:
                self.cust_combo.current(0)
            self.cust_combo.pack(fill="x")

        # Priority column
        p_box = tk.Frame(c_row, bg=BG_PANEL, width=160)
        p_box.pack(side="right")
        tk.Label(p_box, text="REPAIR PRIORITY", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))

        self.prio_combo = ttk.Combobox(p_box, state="readonly", font=FONT_BODY, values=list(PRIORITIES), width=14)
        self.prio_combo.set("Normal")
        self.prio_combo.pack(fill="x")

        # Section 2: Hardware Specifications (2-column neat grid)
        s2 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s2.pack(fill="x", pady=(0, 10))

        tk.Label(s2, text="2. HARDWARE SPECIFICATIONS", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))

        # Row 1: Device Type & Brand
        r1 = tk.Frame(s2, bg=BG_PANEL)
        r1.pack(fill="x", pady=(0, 8))

        dt_box = tk.Frame(r1, bg=BG_PANEL)
        dt_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(dt_box, text="DEVICE TYPE *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
        self.type_combo = ttk.Combobox(dt_box, state="readonly", font=FONT_BODY, values=list(DEVICE_TYPES))
        self.type_combo.set("Laptop")
        self.type_combo.pack(fill="x")

        b_box = tk.Frame(r1, bg=BG_PANEL)
        b_box.pack(side="left", fill="x", expand=True)
        tk.Label(b_box, text="BRAND * (e.g. Apple, Dell, Lenovo)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
        self.brand_entry = tk.Entry(b_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.brand_entry.pack(fill="x")

        # Row 2: Model & Serial Number
        r2 = tk.Frame(s2, bg=BG_PANEL)
        r2.pack(fill="x", pady=(0, 8))

        m_box = tk.Frame(r2, bg=BG_PANEL)
        m_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(m_box, text="MODEL * (e.g. MacBook Pro, ThinkPad T480)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
        self.model_entry = tk.Entry(m_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.model_entry.pack(fill="x")

        sn_box = tk.Frame(r2, bg=BG_PANEL)
        sn_box.pack(side="left", fill="x", expand=True)
        tk.Label(sn_box, text="SERIAL NUMBER *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
        self.sn_entry = tk.Entry(sn_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.sn_entry.pack(fill="x")

        # Row 3: Est. Completion (Staff only) & Physical Condition
        if not self.is_customer:
            r3 = tk.Frame(s2, bg=BG_PANEL)
            r3.pack(fill="x", pady=(0, 8))

            est_box = tk.Frame(r3, bg=BG_PANEL)
            est_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(est_box, text="ESTIMATED COMPLETION (YYYY-MM-DD)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
            self.est_entry = tk.Entry(est_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
            default_est = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            self.est_entry.insert(0, default_est)
            self.est_entry.pack(fill="x")

            cond_box = tk.Frame(r3, bg=BG_PANEL)
            cond_box.pack(side="left", fill="x", expand=True)
            tk.Label(cond_box, text="PHYSICAL CONDITION (Scratches, dents)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
            self.cond_entry = tk.Entry(cond_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
            self.cond_entry.insert(0, "Normal cosmetic wear")
            self.cond_entry.pack(fill="x")
        else:
            self.est_entry = None
            cond_box = tk.Frame(s2, bg=BG_PANEL)
            cond_box.pack(fill="x")
            tk.Label(cond_box, text="PHYSICAL CONDITION ON ARRIVAL (Scratches, cracks, dents)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 2))
            self.cond_entry = tk.Entry(cond_box, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
            self.cond_entry.insert(0, "Normal cosmetic wear, no major chassis cracks")
            self.cond_entry.pack(fill="x")

        # Section 3: Accessories Received (2-Row Wrapped Layout)
        s3 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s3.pack(fill="x", pady=(0, 10))

        tk.Label(s3, text="3. ACCESSORIES DELIVERED WITH DEVICE", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

        self.acc_vars = {}
        standard_accs_row1 = ["OEM Charger / Power Adapter", "Sleeve / Bag", "Power Cable"]
        standard_accs_row2 = ["External Mouse / Dongle", "USB / Storage Media", "Original Box"]

        acc_r1 = tk.Frame(s3, bg=BG_PANEL)
        acc_r1.pack(fill="x", pady=(0, 4))
        for acc in standard_accs_row1:
            v = tk.BooleanVar(value=False)
            self.acc_vars[acc] = v
            tk.Checkbutton(acc_r1, text=acc, variable=v, font=FONT_SMALL, fg=INK, bg=BG_PANEL, activebackground=BG_PANEL).pack(side="left", padx=(0, 14))

        acc_r2 = tk.Frame(s3, bg=BG_PANEL)
        acc_r2.pack(fill="x")
        for acc in standard_accs_row2:
            v = tk.BooleanVar(value=False)
            self.acc_vars[acc] = v
            tk.Checkbutton(acc_r2, text=acc, variable=v, font=FONT_SMALL, fg=INK, bg=BG_PANEL, activebackground=BG_PANEL).pack(side="left", padx=(0, 14))

        # Section 4: Problem Description
        s4 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s4.pack(fill="x", pady=(0, 10))

        tk.Label(s4, text="4. REPORTED FAULT & SYMPTOM DESCRIPTION *", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

        self.problem_text = tk.Text(s4, height=3, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.problem_text.pack(fill="x")

        # Section 5: Initial Services Selection (Compact Listbox)
        s5 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        s5.pack(fill="x", pady=(0, 10))

        tk.Label(
            s5,
            text="5. PRELIMINARY SERVICES (Select one or more from catalog)",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            s5,
            text="Hold Ctrl to select multiple services.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 6))

        srv_wrap = tk.Frame(s5, bg=BG_PANEL)
        srv_wrap.pack(fill="x")

        self.srv_listbox = tk.Listbox(
            srv_wrap,
            selectmode="multiple",
            font=FONT_BODY,
            height=3,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            exportselection=False
        )
        srv_vsb = ttk.Scrollbar(srv_wrap, orient="vertical", command=self.srv_listbox.yview)
        self.srv_listbox.configure(yscrollcommand=srv_vsb.set)

        for s in self.services_list:
            self.srv_listbox.insert("end", f"[{s['service_id']}] {s['name']}: {money(s['price'])}")

        self.srv_listbox.pack(side="left", fill="both", expand=True)
        srv_vsb.pack(side="right", fill="y")

        if self.services_list:
            self.srv_listbox.select_set(0)

        # Section 6: Payment Option & Downpayment (Customer) or Technician Assignment (Staff)
        if self.is_customer:
            s6 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
            s6.pack(fill="x", pady=(0, 14))

            tk.Label(s6, text="6. SETTLEMENT PREFERENCE & OPTIONAL DOWNPAYMENT", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

            m_box, self.pay_pref_combo = labeled_field(s6, "PAYMENT METHOD", widget_class=ttk.Combobox)
            self.pay_pref_combo['values'] = [
                "Pay Onsite (Upon hardware drop-off at workshop)",
                "GCash (Online Downpayment / Settlement)",
                "Card (Debit / Credit Online)"
            ]
            self.pay_pref_combo.set("Pay Onsite (Upon hardware drop-off at workshop)")
            m_box.pack(fill="x", pady=(0, 6))

            self.dp_container = tk.Frame(s6, bg=BG_PANEL)

            dp_box, self.dp_entry = labeled_field(self.dp_container, "DOWNPAYMENT AMOUNT (₱)", widget_class=tk.Entry)
            self.dp_entry.insert(0, "500.00")
            dp_box.pack(fill="x", pady=(0, 6))

            ref_box, self.intake_ref_entry = labeled_field(self.dp_container, "TRANSACTION / REFERENCE NO. (OPTIONAL)", widget_class=tk.Entry)
            ref_box.pack(fill="x")

            def _toggle_dp(e=None):
                val = self.pay_pref_combo.get()
                if "Pay Onsite" in val:
                    self.dp_container.pack_forget()
                else:
                    self.dp_container.pack(fill="x")

            self.pay_pref_combo.bind("<<ComboboxSelected>>", _toggle_dp)
            _toggle_dp()
            self.tech_combo = None
        else:
            s6 = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
            s6.pack(fill="x", pady=(0, 14))

            tk.Label(s6, text="6. BENCH TECHNICIAN ASSIGNMENT (OPTIONAL)", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 6))

            self.tech_combo = ttk.Combobox(s6, state="readonly", font=FONT_BODY)
            tech_opts = ["Unassigned"] + [f"{t['user_id']}: {t['full_name']}" for t in self.technicians_list]
            self.tech_combo['values'] = tech_opts
            self.tech_combo.current(0)
            self.tech_combo.pack(fill="x")

    @guard
    def _submit_job(self):
        # Resolve customer
        if self.is_customer:
            c_phone = self.phone_entry.get().strip()
            if not c_phone:
                messagebox.showwarning("Notice", "Please enter a contact number so we can notify you about your repair.")
                return
            from logic.customers import ensure_customer_record
            cust_rec = ensure_customer_record(self.acting_user['full_name'], contact_no=c_phone)
            cid = cust_rec['customer_id']
            tech_id = ""
        else:
            sel_c_idx = self.cust_combo.current()
            if sel_c_idx < 0 or sel_c_idx >= len(self.customers_list):
                messagebox.showwarning("Notice", "Please select a valid customer.")
                return
            cid = self.customers_list[sel_c_idx]['customer_id']

            tech_id = ""
            if self.tech_combo:
                tech_idx = self.tech_combo.current()
                if tech_idx > 0 and (tech_idx - 1) < len(self.technicians_list):
                    tech_id = self.technicians_list[tech_idx - 1]['user_id']

        dtype = self.type_combo.get()
        brand = self.brand_entry.get().strip()
        model = self.model_entry.get().strip()
        serial_no = self.sn_entry.get().strip()
        est_completion = self.est_entry.get().strip() if self.est_entry else ""
        condition = self.cond_entry.get().strip()
        priority = self.prio_combo.get()
        problem = self.problem_text.get("1.0", "end").strip()

        # Selected accessories
        accessories = [name for name, var in self.acc_vars.items() if var.get()]

        # Selected services
        sel_srv_indices = self.srv_listbox.curselection()
        service_ids = [self.services_list[i]['service_id'] for i in sel_srv_indices]

        data = {
            'customer_id': cid,
            'device_type': dtype,
            'brand': brand,
            'model': model,
            'serial_no': serial_no,
            'problem': problem,
            'device_condition': condition,
            'priority': priority,
            'est_completion': est_completion,
            'technician_id': tech_id
        }

        # Save to database
        jid = create_job(data, accessories, service_ids, self.acting_user)

        # Process initial downpayment if customer opted for online payment
        dp_credited = None
        if self.is_customer:
            pay_opt = self.pay_pref_combo.get()
            if "Pay Onsite" in pay_opt:
                # Counter settlement: no online downpayment credited
                dp_credited = None
            elif "GCash" in pay_opt or "Card" in pay_opt:
                clean_method = "GCash" if "GCash" in pay_opt else "Card"
                dp_val = self.dp_entry.get().replace(",", "").strip()
                if dp_val:
                    try:
                        from logic.billing import record_payment
                        res = record_payment(jid, dp_val, clean_method, self.acting_user)
                        dp_credited = res['applied']
                    except Exception as e:
                        messagebox.showwarning("Payment Notice", f"Job ticket {jid} was created, but downpayment could not be processed: {e}")

        if self.is_customer:
            if dp_credited:
                success_msg = (
                    f"Repair Request Submitted with Downpayment!\n\n"
                    f"Tracking Ticket: {jid}\n"
                    f"Downpayment Credited: {money(dp_credited)}\n"
                    f"Method: {clean_method}\n\n"
                    "Our atelier technicians will inspect your device upon arrival."
                )
            else:
                success_msg = (
                    f"Repair Request Submitted!\n\n"
                    f"Tracking Ticket: {jid}\n"
                    f"Settlement: Pay on-site upon hardware delivery.\n\n"
                    "Our atelier technicians will inspect your device upon arrival."
                )
        else:
            success_msg = f"Job Order {jid} successfully recorded in Received status."

        messagebox.showinfo("Ticket Created", success_msg)

        if self.on_job_created_callback:
            self.on_job_created_callback()

        self.destroy()

        # Pop up intake receipt
        receipt_text = intake_receipt_text(jid)
        ReceiptViewerModal(
            self.master,
            f"Intake Ticket: {jid}",
            receipt_text,
            f"{jid}_intake.txt"
        )
