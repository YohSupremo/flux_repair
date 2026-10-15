import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, RED, AMBER, AMBER_LIGHT, FONT_TITLE,
    FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.parts import list_parts, get_part, add_part, edit_part, delete_part, low_stock_parts
from logic.auth import can
from utils import money


class PartsView(tk.Frame):
    """
    Hardware Inventory & Replacement Parts (FR-33 - FR-36).
    Tracks stock quantities, per-part thresholds, and unit pricing.
    """
    def __init__(self, parent, acting_user):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.show_low_stock_only = False

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(title_box, text="Hardware Parts & Inventory", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Component stock, micro-ICs, replacement screens, batteries, and threshold tracking.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        if can(self.acting_user['role'], 'manage_parts'):
            add_btn = primary_button(btn_box, "+ Add Part to Stock", command=self._open_add_modal)
            add_btn.pack(side="left")

        # Filter Sub-Bar
        sub_bar = tk.Frame(self, bg=BG, padx=24, pady=12)
        sub_bar.pack(fill="x")

        self.low_stock_var = tk.BooleanVar(value=False)
        cb = tk.Checkbutton(
            sub_bar,
            text="Show Low Stock Items Only (Alerts)",
            variable=self.low_stock_var,
            font=FONT_SMALL_BOLD,
            fg=AMBER,
            bg=BG,
            activebackground=BG,
            command=self.refresh
        )
        cb.pack(side="left")

        # Bottom Bar (Packed side="bottom" first to guarantee it is NEVER pushed off screen)
        if can(self.acting_user['role'], 'manage_parts'):
            bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
            bottom_bar.pack(fill="x", side="bottom")

            edit_btn = secondary_button(bottom_bar, "Edit Part Details", command=self._open_edit_modal)
            edit_btn.pack(side="left", padx=(0, 8))

            del_btn = danger_button(bottom_bar, "Delete Part", command=self._handle_delete)
            del_btn.pack(side="left")

        # Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=20)
        table_wrap.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("part_id", "name", "quantity", "unit_price", "threshold", "status")
        heads = ("Part ID", "Component / Part Name", "In Stock", "Unit Price (₱)", "Min Threshold", "Inventory Health")
        widths = (100, 260, 100, 140, 120, 140)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

    def refresh(self):
        is_low_only = self.low_stock_var.get()
        raw = low_stock_parts() if is_low_only else list_parts()

        rows = []
        for p in raw:
            qty = int(p['quantity'])
            thresh = int(p['low_stock_threshold'])
            if qty <= 0:
                health = "Out of Stock"
            elif qty <= thresh:
                health = f"Low Stock (≤ {thresh})"
            else:
                health = "Nominal"

            rows.append({
                'part_id': p['part_id'],
                'name': p['name'],
                'quantity': str(qty),
                'unit_price': money(p['unit_price']),
                'threshold': str(thresh),
                'status': health
            })

        cols = ("part_id", "name", "quantity", "unit_price", "threshold", "status")
        fill_table(self.tree, rows, cols)

    def _get_selected_part(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a part from the inventory table.")
            return None
        pid = self.tree.item(sel[0], "values")[0]
        return get_part(pid)

    def _open_add_modal(self):
        PartFormModal(self, "Add Part to Inventory", self.acting_user, on_save_callback=self.refresh)

    def _open_edit_modal(self):
        p = self._get_selected_part()
        if p:
            PartFormModal(self, "Edit Inventory Part", self.acting_user, part=p, on_save_callback=self.refresh)

    @guard
    def _handle_delete(self):
        p = self._get_selected_part()
        if not p:
            return
        pid = p['part_id']
        name = p['name']

        if confirm("Confirm Deletion", f"Are you sure you want to delete component '{name}' ({pid})?"):
            delete_part(pid, self.acting_user)
            messagebox.showinfo("Deleted", f"Part {pid} removed from inventory.")
            self.refresh()


class PartFormModal(tk.Toplevel):
    """Modal for creating and updating inventory parts."""
    def __init__(self, parent, title_text, acting_user, part=None, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.part = part
        self.on_save_callback = on_save_callback

        self.title(title_text)
        self.geometry("460x420")
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

        f1, self.name_entry = labeled_field(card, "PART / COMPONENT NAME *", widget_class=tk.Entry)
        f1.pack(fill="x", pady=(0, 10))

        f2, self.qty_entry = labeled_field(card, "STOCK QUANTITY *", widget_class=tk.Entry)
        f2.pack(fill="x", pady=(0, 10))

        f3, self.price_entry = labeled_field(card, "UNIT PRICE (₱) *", widget_class=tk.Entry)
        f3.pack(fill="x", pady=(0, 10))

        f4, self.thresh_entry = labeled_field(card, "LOW STOCK ALERT THRESHOLD *", widget_class=tk.Entry)
        f4.pack(fill="x", pady=(0, 10))

        if self.part:
            self.name_entry.insert(0, self.part['name'])
            self.qty_entry.insert(0, self.part['quantity'])
            self.price_entry.insert(0, self.part['unit_price'])
            self.thresh_entry.insert(0, self.part['low_stock_threshold'])
        else:
            self.qty_entry.insert(0, "10")
            self.thresh_entry.insert(0, "3")

        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Save Component", command=self._save).pack(side="right")

    @guard
    def _save(self):
        name = self.name_entry.get()
        qty = self.qty_entry.get()
        price = self.price_entry.get()
        thresh = self.thresh_entry.get()

        if self.part:
            edit_part(self.part['part_id'], name, qty, price, thresh, self.acting_user)
            messagebox.showinfo("Part Updated", f"Part {self.part['part_id']} updated.")
        else:
            new_p = add_part(name, qty, price, thresh, self.acting_user)
            messagebox.showinfo("Part Created", f"Part registered as {new_p['part_id']}.")

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
