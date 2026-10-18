import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.customers import (
    list_customers, search_customers, add_customer, edit_customer,
    delete_customer, customer_history, get_customer
)
from logic.jobs import status_map


class CustomersView(tk.Frame):
    """
    Customer Management Interface (FR-07 - FR-12).
    Features customer table, live search, add/edit modal, delete protection, and repair history.
    """
    def __init__(self, parent, acting_user, on_open_job_callback=None):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.on_open_job_callback = on_open_job_callback

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header Bar
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(title_box, text="Customer Registry", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Manage customer profiles, contact directories, and historical device tickets.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Top Actions
        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        add_btn = primary_button(btn_box, "+ Add Customer", command=self._open_add_modal)
        add_btn.pack(side="left")

        # Search Bar Bar
        search_bar = tk.Frame(self, bg=BG, padx=24, pady=12)
        search_bar.pack(fill="x")

        s_box = tk.Frame(search_bar, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=8, pady=4)
        s_box.pack(side="left", fill="x", expand=True)

        tk.Label(s_box, text="Search Directory:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(4, 8))
        self.search_entry = tk.Entry(s_box, font=FONT_BODY, bg=BG_PANEL, fg=INK, bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._handle_search())

        clear_btn = secondary_button(search_bar, "Clear", command=self._clear_search, padx=10, pady=4)
        clear_btn.pack(side="left", padx=(8, 0))

        # Bottom Action Bar (Packed side="bottom" first to guarantee it is NEVER pushed off screen)
        bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
        bottom_bar.pack(fill="x", side="bottom")

        hist_btn = secondary_button(bottom_bar, "View Repair History", command=self._view_history)
        hist_btn.pack(side="left", padx=(0, 8))

        edit_btn = secondary_button(bottom_bar, "Edit Details", command=self._open_edit_modal)
        edit_btn.pack(side="left", padx=(0, 8))

        del_btn = danger_button(bottom_bar, "Delete Customer", command=self._handle_delete)
        del_btn.pack(side="left")

        # Main Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=20)
        table_wrap.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("customer_id", "name", "contact_no", "email", "address")
        heads = ("Customer ID", "Full Name", "Contact Number", "Email Address", "Address")
        widths = (110, 200, 150, 220, 260)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

        # Double click to view history
        self.tree.bind("<Double-1>", lambda e: self._view_history())

    def refresh(self):
        """Reload customer table from storage."""
        query = self.search_entry.get().strip()
        rows = search_customers(query) if query else list_customers()
        cols = ("customer_id", "name", "contact_no", "email", "address")
        fill_table(self.tree, rows, cols)

    def _handle_search(self):
        self.refresh()

    def _clear_search(self):
        self.search_entry.delete(0, "end")
        self.refresh()

    def _get_selected_customer(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a customer from the table.")
            return None
        vals = self.tree.item(sel[0], "values")
        cid = vals[0]
        return get_customer(cid)

    def _open_add_modal(self):
        CustomerFormModal(self, "Add Customer", self.acting_user, on_save_callback=self.refresh)

    def _open_edit_modal(self):
        c = self._get_selected_customer()
        if c:
            CustomerFormModal(self, "Edit Customer", self.acting_user, customer=c, on_save_callback=self.refresh)

    @guard
    def _handle_delete(self):
        c = self._get_selected_customer()
        if not c:
            return
        cid = c['customer_id']
        name = c['name']

        if confirm("Confirm Deletion", f"Are you sure you want to delete customer {cid} ({name})?"):
            delete_customer(cid, self.acting_user)
            messagebox.showinfo("Deleted", f"Customer {cid} has been removed.")
            self.refresh()

    def _view_history(self):
        c = self._get_selected_customer()
        if c:
            CustomerHistoryModal(self, c, self.on_open_job_callback)


class CustomerFormModal(tk.Toplevel):
    """Modal dialog for creating and editing customer profiles."""
    def __init__(self, parent, title_text, acting_user, customer=None, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.customer = customer
        self.on_save_callback = on_save_callback

        self.title(title_text)
        self.geometry("480x440")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui(title_text)

    def _build_ui(self, title_text):
        # Header
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text=title_text, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        # Form body
        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        card = tk.Frame(body, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=16)
        card.pack(fill="both", expand=True)

        # Fields
        f1, self.name_entry = labeled_field(card, "FULL NAME *", widget_class=tk.Entry)
        f1.pack(fill="x", pady=(0, 10))

        f2, self.contact_entry = labeled_field(card, "CONTACT NUMBER * (e.g. 0917-123-4567)", widget_class=tk.Entry)
        vcmd = (self.register(lambda act, p, char: not (act == '1' and any(c.isalpha() for c in char))), '%d', '%P', '%S')
        self.contact_entry.configure(validate="key", validatecommand=vcmd)
        f2.pack(fill="x", pady=(0, 10))

        f3, self.email_entry = labeled_field(card, "EMAIL ADDRESS *", widget_class=tk.Entry)
        f3.pack(fill="x", pady=(0, 10))

        f4, self.addr_entry = labeled_field(card, "PHYSICAL ADDRESS *", widget_class=tk.Entry)
        f4.pack(fill="x", pady=(0, 10))

        # Populate if editing
        if self.customer:
            self.name_entry.insert(0, self.customer['name'])
            self.contact_entry.insert(0, self.customer['contact_no'])
            self.email_entry.insert(0, self.customer['email'])
            self.addr_entry.insert(0, self.customer['address'])

        # Bottom Bar
        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Save Customer Profile", command=self._save).pack(side="right")

    @guard
    def _save(self):
        name = self.name_entry.get()
        contact = self.contact_entry.get()
        email = self.email_entry.get()
        addr = self.addr_entry.get()

        if self.customer:
            edit_customer(self.customer['customer_id'], name, contact, email, addr, self.acting_user)
            messagebox.showinfo("Profile Updated", f"Customer {self.customer['customer_id']} details saved.")
        else:
            new_c = add_customer(name, contact, email, addr, self.acting_user)
            messagebox.showinfo("Customer Created", f"Customer registered as {new_c['customer_id']}.")

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()


class CustomerHistoryModal(tk.Toplevel):
    """Displays customer's historical job tickets (FR-12)."""
    def __init__(self, parent, customer, on_open_job_callback=None):
        super().__init__(parent)
        self.customer = customer
        self.on_open_job_callback = on_open_job_callback

        self.title(f"Repair History: {customer['name']} ({customer['customer_id']})")
        self.geometry("720x460")
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        tk.Label(
            top_bar,
            text=f"Repair Dossier: {self.customer['name']}",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            top_bar,
            text=f"Customer ID: {self.customer['customer_id']}   |   Contact: {self.customer['contact_no']}",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")
        secondary_button(bot, "Close", command=self.destroy).pack(side="right")

        content = tk.Frame(self, bg=BG, padx=20, pady=16)
        content.pack(fill="both", expand=True)

        cols = ("job_id", "date_received", "device", "problem", "status")
        heads = ("Job ID", "Date Received", "Device Specs", "Reported Problem", "Current Status")
        widths = (90, 130, 160, 200, 110)

        t_frame, tree = make_table(content, cols, heads, widths)
        t_frame.pack(fill="both", expand=True)

        jobs = customer_history(self.customer['customer_id'])
        s_map = status_map()

        rows = []
        for j in jobs:
            rows.append({
                'job_id': j['job_id'],
                'date_received': j['date_received'],
                'device': f"{j['device_type']} {j['brand']} {j['model']}",
                'problem': j['problem'],
                'status': s_map.get(j['job_id'], 'Received')
            })

        fill_table(tree, rows, cols)
