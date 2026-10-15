import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, RED, FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.catalog import list_services, get_service, add_service, edit_service, delete_service
from logic.auth import can
from utils import money


class CatalogView(tk.Frame):
    """
    Repair Service Catalog Interface (FR-21 - FR-24b).
    Enables viewing catalog rates, modifying baseline prices, and registering repair offerings.
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

        tk.Label(title_box, text="Repair Service Catalog", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Standard diagnostic, micro-soldering, and board restoration service rates.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        if can(self.acting_user['role'], 'manage_services'):
            add_btn = primary_button(btn_box, "+ Add Service", command=self._open_add_modal)
            add_btn.pack(side="left")

        # Bottom Bar (Packed side="bottom" first to guarantee it is NEVER pushed off screen)
        if can(self.acting_user['role'], 'manage_services'):
            bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
            bottom_bar.pack(fill="x", side="bottom")

            edit_btn = secondary_button(bottom_bar, "Edit Service", command=self._open_edit_modal)
            edit_btn.pack(side="left", padx=(0, 8))

            del_btn = danger_button(bottom_bar, "Delete Service", command=self._handle_delete)
            del_btn.pack(side="left")

        # Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=20, pady=10)
        table_wrap.pack(fill="both", expand=True)

        cols = ("service_id", "name", "description", "price")
        heads = ("Service ID", "Service Name", "Description & Atelier Scope", "Default Price (₱)")
        widths = (110, 240, 420, 140)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

    def refresh(self):
        raw = list_services()
        rows = [
            {
                'service_id': s['service_id'],
                'name': s['name'],
                'description': s['description'],
                'price': money(s['price'])
            }
            for s in raw
        ]
        cols = ("service_id", "name", "description", "price")
        fill_table(self.tree, rows, cols)

    def _get_selected_service(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a service from the catalog.")
            return None
        sid = self.tree.item(sel[0], "values")[0]
        return get_service(sid)

    def _open_add_modal(self):
        ServiceFormModal(self, "Add Service", self.acting_user, on_save_callback=self.refresh)

    def _open_edit_modal(self):
        s = self._get_selected_service()
        if s:
            ServiceFormModal(self, "Edit Service", self.acting_user, service=s, on_save_callback=self.refresh)

    @guard
    def _handle_delete(self):
        s = self._get_selected_service()
        if not s:
            return
        sid = s['service_id']
        name = s['name']

        if confirm("Confirm Deletion", f"Are you sure you want to delete service '{name}' ({sid})?"):
            delete_service(sid, self.acting_user)
            messagebox.showinfo("Deleted", f"Service {sid} deleted successfully.")
            self.refresh()


class ServiceFormModal(tk.Toplevel):
    """Modal for registering or updating catalog repair services."""
    def __init__(self, parent, title_text, acting_user, service=None, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.service = service
        self.on_save_callback = on_save_callback

        self.title(title_text)
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui(title_text)

    def _build_ui(self, title_text):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text=title_text, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        card = tk.Frame(body, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=16)
        card.pack(fill="both", expand=True)

        f1, self.name_entry = labeled_field(card, "SERVICE NAME *", widget_class=tk.Entry)
        f1.pack(fill="x", pady=(0, 10))

        f2, self.desc_entry = labeled_field(card, "DESCRIPTION *", widget_class=tk.Entry)
        f2.pack(fill="x", pady=(0, 10))

        f3, self.price_entry = labeled_field(card, "BASE PRICE (₱) *", widget_class=tk.Entry)
        f3.pack(fill="x", pady=(0, 10))

        if self.service:
            self.name_entry.insert(0, self.service['name'])
            self.desc_entry.insert(0, self.service['description'])
            self.price_entry.insert(0, self.service['price'])

        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Save Service", command=self._save).pack(side="right")

    @guard
    def _save(self):
        name = self.name_entry.get()
        desc = self.desc_entry.get()
        price = self.price_entry.get()

        if self.service:
            edit_service(self.service['service_id'], name, desc, price, self.acting_user)
            messagebox.showinfo("Service Updated", f"Service {self.service['service_id']} updated.")
        else:
            new_s = add_service(name, desc, price, self.acting_user)
            messagebox.showinfo("Service Created", f"Service registered as {new_s['service_id']}.")

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
