import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED, AMBER, BLUE,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_BOLD
)
from gui.widgets import primary_button, secondary_button, labeled_field, guard
from logic.billing import compute_bill, record_payment, official_receipt_text
from logic.jobs import job_details
from utils import money
from gui.receipt_ui import ReceiptViewerModal


class PaymentModal(tk.Toplevel):
    """
    Payment & Downpayment Processing Window (FR-38 - FR-42).
    Supports partial payments, downpayment presets, online GCash / Card settlements,
    and on-site counter settlement upon hardware drop-off.
    """
    def __init__(self, parent, job_id, acting_user, on_payment_recorded=None):
        super().__init__(parent)
        self.job_id = job_id
        self.acting_user = acting_user
        self.on_payment_recorded = on_payment_recorded
        self.is_customer = (self.acting_user['role'] == 'Customer')

        self.title(f"Payment & Downpayment — Job {job_id}")
        self.geometry("560x620")
        self.minsize(480, 520)
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
            w = 560
            h = min(620, max(500, mh - 50))
            x = max(40, mx + (mw - w) // 2)
            y = max(30, my + (mh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            self.geometry("560x620")

    def _load_data(self):
        self.details = job_details(self.job_id)
        self.bill = self.details['bill']

    def _build_ui(self):
        # Header
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=22, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        header_title = f"Process Payment / Downpayment: Job {self.job_id}"
        tk.Label(top_bar, text=header_title, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        cust_name = self.details['customer']['name'] if self.details['customer'] else "N/A"
        dev_info = f"{self.details['job']['device_type']} ({self.details['job']['brand']} {self.details['job']['model']})"
        tk.Label(
            top_bar,
            text=f"Customer: {cust_name}   •   Device: {dev_info}",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # Bottom Buttons Bar (packed side="bottom" first to guarantee it is NEVER clipped)
        btn_row = tk.Frame(self, bg=BG_PANEL, padx=22, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        btn_row.pack(fill="x", side="bottom")

        secondary_button(btn_row, "Cancel", command=self.destroy).pack(side="left")
        self.submit_btn = primary_button(btn_row, "Confirm & Record Payment →", command=self._submit_payment)
        self.submit_btn.pack(side="right")

        # Scrollable Main Body
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG, padx=20, pady=12)

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

        # 1. Financial Ledger Summary Card
        card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        card.pack(fill="x", pady=(0, 12))

        def _row(parent, lbl_text, val_text, is_bold=False, is_highlight=False):
            r = tk.Frame(parent, bg=BG_PANEL)
            r.pack(fill="x", pady=2)
            f = FONT_BODY_BOLD if is_bold else FONT_BODY
            val_fg = EMERALD if is_highlight else (INK if is_bold else MUTED)
            tk.Label(r, text=lbl_text, font=f, fg=MUTED, bg=BG_PANEL).pack(side="left")
            tk.Label(r, text=val_text, font=f, fg=val_fg, bg=BG_PANEL).pack(side="right")

        _row(card, "Total Labor & Services", money(self.bill['services']))
        _row(card, "Total Hardware & Parts", money(self.bill['parts']))
        _row(card, "Total Repair Amount", money(self.bill['total']), is_bold=True)
        _row(card, "Previously Paid / Credited", money(self.bill['paid']))

        tk.Frame(card, bg=LINE, height=1).pack(fill="x", pady=6)

        # Outstanding Balance Box
        bal_box = tk.Frame(card, bg=EMERALD_LIGHT, padx=12, pady=8, bd=0, highlightthickness=1, highlightbackground="#a7f3d0")
        bal_box.pack(fill="x")
        tk.Label(bal_box, text="OUTSTANDING BALANCE DUE", font=FONT_SMALL_BOLD, fg=EMERALD, bg=EMERALD_LIGHT).pack(anchor="w")
        self.bal_display = tk.Label(
            bal_box,
            text=money(self.bill['balance']),
            font=("Segoe UI", 18, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT
        )
        self.bal_display.pack(anchor="w")

        # 2. Payment & Downpayment Entry Form
        form_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=12)
        form_card.pack(fill="x")

        # Method selector
        if self.is_customer:
            note_box = tk.Frame(form_card, bg="#fef3c7", padx=10, pady=8, bd=0, highlightthickness=1, highlightbackground="#fde68a")
            note_box.pack(fill="x", pady=(0, 10))
            tk.Label(
                note_box,
                text="Prefer paying on-site upon drop-off? You do NOT need to submit anything here. Simply bring your device to our workshop counter and pay in Cash or Card at intake.",
                font=FONT_SMALL,
                fg="#92400e",
                bg="#fef3c7",
                wraplength=460,
                justify="left"
            ).pack(anchor="w")

        m_box, self.method_combo = labeled_field(form_card, "PAYMENT METHOD", widget_class=ttk.Combobox)
        if self.is_customer:
            self.method_combo['values'] = [
                "GCash (Digital Payment)",
                "Card (Debit / Credit Online)"
            ]
            self.method_combo.set("GCash (Digital Payment)")
        else:
            self.method_combo['values'] = ["Cash", "GCash", "Card"]
            self.method_combo.set("Cash")

        m_box.pack(fill="x", pady=(0, 10))
        self.method_combo.bind("<<ComboboxSelected>>", lambda e: self._on_method_selected())

        # Amount Tendered Container
        self.amt_container = tk.Frame(form_card, bg=BG_PANEL)
        self.amt_container.pack(fill="x")

        a_box, self.amount_entry = labeled_field(self.amt_container, "AMOUNT TENDERED / DOWNPAYMENT (₱)", widget_class=tk.Entry)
        self.amount_entry.insert(0, f"{self.bill['balance']:.2f}")
        a_box.pack(fill="x", pady=(0, 6))
        self.amount_entry.bind("<KeyRelease>", lambda e: self._on_input_changed())

        # Quick Downpayment Preset Buttons
        p_box = tk.Frame(self.amt_container, bg=BG_PANEL)
        p_box.pack(fill="x", pady=(0, 10))

        tk.Label(p_box, text="Quick Downpayment Options:", font=FONT_SMALL, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        p_row = tk.Frame(p_box, bg=BG_PANEL)
        p_row.pack(fill="x")

        def _apply_preset(multiplier):
            val = (self.bill['balance'] * Decimal(str(multiplier))).quantize(Decimal('0.01'))
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{val:.2f}")
            self._on_input_changed()

        secondary_button(p_row, "20% Deposit", command=lambda: _apply_preset(0.20), padx=8, pady=3).pack(side="left", padx=(0, 6))
        secondary_button(p_row, "50% Downpayment", command=lambda: _apply_preset(0.50), padx=8, pady=3).pack(side="left", padx=(0, 6))
        secondary_button(p_row, "Full Balance", command=lambda: _apply_preset(1.00), padx=8, pady=3).pack(side="left")

        # Reference No. field for GCash / Card
        self.ref_box, self.ref_entry = labeled_field(self.amt_container, "ONLINE TRANSACTION / REFERENCE NO. (OPTIONAL)", widget_class=tk.Entry)
        self.ref_box.pack(fill="x", pady=(0, 10))

        # Dynamic Ledger Live Readout
        self.readout_box = tk.Frame(self.amt_container, bg=BG_HOVER, padx=12, pady=10)
        self.readout_box.pack(fill="x")

        r1 = tk.Frame(self.readout_box, bg=BG_HOVER)
        r1.pack(fill="x")
        tk.Label(r1, text="Payment Classification:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_HOVER).pack(side="left")
        self.pay_type_lbl = tk.Label(r1, text="Full Settlement", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_HOVER)
        self.pay_type_lbl.pack(side="right")

        r2 = tk.Frame(self.readout_box, bg=BG_HOVER)
        r2.pack(fill="x", pady=(4, 0))
        self.lbl_rem_title = tk.Label(r2, text="Remaining Balance After Payment:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_HOVER)
        self.lbl_rem_title.pack(side="left")
        self.lbl_rem_val = tk.Label(r2, text="₱0.00", font=FONT_BODY_BOLD, fg=INK, bg=BG_HOVER)
        self.lbl_rem_val.pack(side="right")

        self.change_row = tk.Frame(self.readout_box, bg=BG_HOVER)
        self.change_row.pack(fill="x", pady=(4, 0))
        tk.Label(self.change_row, text="Calculated Cash Change:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_HOVER).pack(side="left")
        self.change_lbl = tk.Label(self.change_row, text="₱0.00", font=FONT_BODY_BOLD, fg=INK, bg=BG_HOVER)
        self.change_lbl.pack(side="right")

        self._on_method_selected()

    def _get_clean_method(self):
        raw = self.method_combo.get()
        if "GCash" in raw:
            return "GCash"
        elif "Card" in raw:
            return "Card"
        return "Cash"

    def _on_method_selected(self):
        method = self._get_clean_method()
        self.submit_btn.configure(text="Confirm & Record Payment →")

        if method in ("GCash", "Card"):
            self.ref_box.pack(fill="x", pady=(0, 10))
            self.change_row.pack_forget()
        else:
            self.ref_box.pack_forget()
            self.change_row.pack(fill="x", pady=(4, 0))

        self._on_input_changed()

    def _on_input_changed(self):
        method = self._get_clean_method()
        if method == "Onsite":
            return

        raw = self.amount_entry.get().replace(",", "").strip()
        balance = self.bill['balance']

        try:
            amt = Decimal(raw) if raw else Decimal('0.00')
        except InvalidOperation:
            amt = Decimal('0.00')

        if amt <= Decimal('0.00'):
            self.pay_type_lbl.configure(text="Invalid Amount", fg=RED)
            self.lbl_rem_val.configure(text=money(balance), fg=RED)
            return

        if amt < balance:
            # Partial payment / Downpayment
            pct = int((amt / balance) * 100) if balance > 0 else 0
            self.pay_type_lbl.configure(text=f"Downpayment / Deposit ({pct}%)", fg=BLUE)
            rem = balance - amt
            self.lbl_rem_val.configure(text=money(rem), fg=INK)
            self.change_lbl.configure(text="₱0.00", fg=INK)
        elif amt == balance:
            self.pay_type_lbl.configure(text="Full Balance Settlement", fg=EMERALD)
            self.lbl_rem_val.configure(text="₱0.00", fg=EMERALD)
            self.change_lbl.configure(text="₱0.00", fg=INK)
        else:
            # amt > balance
            if method == "Cash":
                change = amt - balance
                self.pay_type_lbl.configure(text="Full Settlement (Cash Overpaid)", fg=EMERALD)
                self.lbl_rem_val.configure(text="₱0.00", fg=EMERALD)
                self.change_lbl.configure(text=money(change), fg=EMERALD)
            else:
                self.pay_type_lbl.configure(text=f"Exceeds Balance Due ({money(balance)})", fg=RED)
                self.lbl_rem_val.configure(text="₱0.00", fg=RED)
                self.change_lbl.configure(text="N/A", fg=DIM)

    @guard
    def _submit_payment(self):
        method = self._get_clean_method()

        amount_str = self.amount_entry.get().strip()

        result = record_payment(self.job_id, amount_str, method, self.acting_user)

        # Check if downpayment or full
        if result['balance'] > Decimal('0.00'):
            msg = (
                f"Downpayment / Deposit Recorded!\n\n"
                f"Amount Credited: {money(result['applied'])}\n"
                f"Payment Method: {method}\n"
                f"Remaining Balance: {money(result['balance'])}\n\n"
                "You can settle the remaining balance upon pickup or final release."
            )
        else:
            msg = (
                f"Full Settlement Recorded!\n\n"
                f"Amount Paid: {money(result['applied'])}\n"
                f"Payment Method: {method}\n"
                f"Remaining Balance: ₱0.00\n\n"
                "Job order is fully settled and cleared for release."
            )

        if result['change'] > Decimal('0.00'):
            msg += f"\n\nCash change to return: {money(result['change'])}"

        messagebox.showinfo("Payment Successful", msg)

        if self.on_payment_recorded:
            self.on_payment_recorded()

        self.destroy()

        # Open official receipt viewer
        receipt_text = official_receipt_text(self.job_id)
        ReceiptViewerModal(
            self.master,
            f"Official Invoice — {self.job_id}",
            receipt_text,
            f"{self.job_id}_official.txt"
        )
