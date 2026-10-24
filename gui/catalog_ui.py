import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageOps, ImageTk

import config
from gui.theme import (
    BG, BG_PANEL, BG_CARD, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT,
    INK, MUTED, DIM, EMERALD, EMERALD_HOVER, EMERALD_LIGHT, EMERALD_BORDER,
    RED, RED_LIGHT, RED_BORDER, FONT_FAMILY, FONT_DISPLAY, FONT_TITLE,
    FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD,
    FONT_MONO, FONT_MONO_SM
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.catalog import list_services, get_service, add_service, edit_service, delete_service
from logic.auth import can
from utils import money


# Mapping from standard service ID to bundled showcase image in images/
SERVICE_IMAGE_MAP = {
    'S-001': 'diagnosticImage.jpg',
    'S-002': 'osInstallation.jpg',
    'S-003': 'virusRemoval.jpg',
    'S-004': 'screenReplacement.jpg',
    'S-005': 'batteryReplacement.jpeg',
    'S-006': 'keyboardReplacement.jpg',
    'S-007': 'hardwareUpgrade.jpg',
    'S-008': 'dataBackup.jpg',
    'S-009': 'cleaningThermalPaste.png',
}

# Fallback keyword matchers if service ID differs or new custom services are added
NAME_IMAGE_KEYWORDS = [
    (('battery', 'power', 'cell', 'charging'), 'batteryReplacement.jpeg'),
    (('clean', 'thermal', 'paste', 'dust', 'overheat', 'fan'), 'cleaningThermalPaste.png'),
    (('backup', 'recovery', 'data', 'clone', 'drive'), 'dataBackup.jpg'),
    (('diag', 'inspection', 'fault', 'check', 'bench'), 'diagnosticImage.jpg'),
    (('hardware', 'upgrade', 'ram', 'ssd', 'nvme', 'memory'), 'hardwareUpgrade.jpg'),
    (('keyboard', 'keycap', 'keys', 'flex'), 'keyboardReplacement.jpg'),
    (('os', 'install', 'reinstall', 'windows', 'system', 'format'), 'osInstallation.jpg'),
    (('screen', 'display', 'panel', 'lcd', 'oled', 'glass'), 'screenReplacement.jpg'),
    (('virus', 'malware', 'spyware', 'adware', 'trojan'), 'virusRemoval.jpg'),
]


def resolve_service_image_path(service):
    """Find corresponding image file path for a service from the images/ directory."""
    images_dir = getattr(config, 'IMAGES_DIR', os.path.join(config.BASE_DIR, 'images'))
    if not os.path.isdir(images_dir):
        return None

    sid = str(service.get('service_id', '')).strip().upper()
    name = str(service.get('name', '')).strip().lower()
    desc = str(service.get('description', '')).strip().lower()

    # 1. Exact ID mapping
    if sid in SERVICE_IMAGE_MAP:
        candidate = os.path.join(images_dir, SERVICE_IMAGE_MAP[sid])
        if os.path.isfile(candidate):
            return candidate

    # 2. Keyword heuristic on service name and description
    for keywords, filename in NAME_IMAGE_KEYWORDS:
        if any(kw in name or kw in desc for kw in keywords):
            candidate = os.path.join(images_dir, filename)
            if os.path.isfile(candidate):
                return candidate

    return None


class CatalogView(tk.Frame):
    """
    Repair Service Catalog Interface (FR-21 - FR-24b).
    Provides both an interactive visual Card Grid (optimized for customers)
    and an administrative Table Registry (for staff/admin management).
    """
    def __init__(self, parent, acting_user, on_book_callback=None):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.on_book_callback = on_book_callback
        self.is_customer = (self.acting_user.get('role') == 'Customer')

        # View mode: customers default to cards, staff/admins default to table
        self.current_mode = "cards" if self.is_customer else "table"

        self._photo_cache = {}
        self.card_widgets = []
        self._current_cols = 0
        self._raw_services = []

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Top Header Banner
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(title_box, text="Repair Service Catalog", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        subtitle_text = (
            "Explore certified repair offerings, diagnostic scope, transparent pricing, and warranty coverage."
            if self.is_customer else
            "Standard diagnostic, micro-soldering, and board restoration service rates."
        )
        tk.Label(
            title_box,
            text=subtitle_text,
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Right Action & Mode Switcher Controls
        controls_box = tk.Frame(header, bg=BG_PANEL)
        controls_box.pack(side="right")

        # Customer "+ Request Repair" quick action in header
        if self.is_customer and self.on_book_callback:
            btn_req = primary_button(controls_box, "+ Request Repair", command=lambda: self._handle_book(None))
            btn_req.pack(side="left", padx=(0, 14))

        # Admin "+ Add Service" button
        if can(self.acting_user['role'], 'manage_services'):
            add_btn = primary_button(controls_box, "+ Add Service", command=self._open_add_modal)
            add_btn.pack(side="left", padx=(0, 14))

        # View Mode Pill Switcher (Cards vs Table)
        mode_pill = tk.Frame(controls_box, bg="#f1f5f9", padx=3, pady=3, bd=0, highlightthickness=1, highlightbackground=LINE)
        mode_pill.pack(side="left")

        self.btn_cards_mode = tk.Button(
            mode_pill,
            text="⊞ Cards View",
            command=lambda: self._set_mode("cards"),
            font=FONT_SMALL_BOLD,
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4
        )
        self.btn_cards_mode.pack(side="left")

        self.btn_table_mode = tk.Button(
            mode_pill,
            text="☰ Table View",
            command=lambda: self._set_mode("table"),
            font=FONT_SMALL_BOLD,
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4
        )
        self.btn_table_mode.pack(side="left")

        # Main Content Container
        self.content_area = tk.Frame(self, bg=BG)
        self.content_area.pack(fill="both", expand=True)

        # 1. Table View Frame
        self.table_view_frame = tk.Frame(self.content_area, bg=BG)

        # Bottom Bar for Table Management (Admin only)
        if can(self.acting_user['role'], 'manage_services'):
            self.bottom_bar = tk.Frame(self.table_view_frame, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
            self.bottom_bar.pack(fill="x", side="bottom")

            edit_btn = secondary_button(self.bottom_bar, "Edit Service", command=self._open_edit_modal)
            edit_btn.pack(side="left", padx=(0, 8))

            del_btn = danger_button(self.bottom_bar, "Delete Service", command=self._handle_delete)
            del_btn.pack(side="left")

        table_wrap = tk.Frame(self.table_view_frame, bg=BG, padx=20, pady=12)
        table_wrap.pack(fill="both", expand=True)

        cols = ("service_id", "name", "description", "price")
        heads = ("Service ID", "Service Name", "Description & Atelier Scope", "Default Price (₱)")
        widths = (110, 240, 420, 140)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

        # 2. Cards View Frame (Scrollable Canvas Grid)
        self.cards_view_frame = tk.Frame(self.content_area, bg=BG)

        self.card_canvas = tk.Canvas(self.cards_view_frame, bg=BG, bd=0, highlightthickness=0)
        self.card_scrollbar = ttk.Scrollbar(self.cards_view_frame, orient="vertical", command=self.card_canvas.yview)
        self.card_canvas.configure(yscrollcommand=self.card_scrollbar.set)

        self.card_scrollable = tk.Frame(self.card_canvas, bg=BG, padx=20, pady=16)
        self.card_win_id = self.card_canvas.create_window((0, 0), window=self.card_scrollable, anchor="nw")

        self.card_scrollable.bind("<Configure>", self._on_scrollable_configure)
        self.card_canvas.bind("<Configure>", self._on_canvas_configure)

        self.card_canvas.pack(side="left", fill="both", expand=True)
        self.card_scrollbar.pack(side="right", fill="y")

        self._bind_mousewheel()
        self._update_mode_buttons()

    def _set_mode(self, mode):
        if self.current_mode == mode:
            return
        self.current_mode = mode
        self._update_mode_buttons()
        self._show_active_frame()

    def _update_mode_buttons(self):
        if self.current_mode == "cards":
            self.btn_cards_mode.configure(bg=EMERALD, fg="#ffffff", activebackground=EMERALD_HOVER, activeforeground="#ffffff")
            self.btn_table_mode.configure(bg="#f1f5f9", fg=MUTED, activebackground="#e2e8f0", activeforeground=INK)
        else:
            self.btn_table_mode.configure(bg=EMERALD, fg="#ffffff", activebackground=EMERALD_HOVER, activeforeground="#ffffff")
            self.btn_cards_mode.configure(bg="#f1f5f9", fg=MUTED, activebackground="#e2e8f0", activeforeground=INK)

    def _show_active_frame(self):
        if self.current_mode == "cards":
            self.table_view_frame.pack_forget()
            self.cards_view_frame.pack(fill="both", expand=True)
            self._render_cards()
        else:
            self.cards_view_frame.pack_forget()
            self.table_view_frame.pack(fill="both", expand=True)

    def _on_scrollable_configure(self, event):
        self.card_canvas.configure(scrollregion=self.card_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.card_canvas.itemconfig(self.card_win_id, width=canvas_width)
        if self.current_mode == "cards":
            self._regrid_cards(canvas_width)

    def _bind_mousewheel(self):
        def _on_mousewheel(event):
            if not self.winfo_exists():
                return
            try:
                if self.winfo_ismapped() and self.current_mode == "cards" and hasattr(self, "card_canvas") and self.card_canvas.winfo_exists():
                    delta = event.delta
                    step = int(-1 * (delta / 120))
                    self.card_canvas.yview_scroll(step, "units")
            except Exception:
                pass

        self.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind_all("<Button-4>", lambda e: self.card_canvas.yview_scroll(-2, "units") if (self.winfo_exists() and self.winfo_ismapped() and self.current_mode == "cards") else None)
        self.bind_all("<Button-5>", lambda e: self.card_canvas.yview_scroll(2, "units") if (self.winfo_exists() and self.winfo_ismapped() and self.current_mode == "cards") else None)

        def _cleanup(e):
            if e.widget == self:
                try:
                    self.unbind_all("<MouseWheel>")
                    self.unbind_all("<Button-4>")
                    self.unbind_all("<Button-5>")
                except Exception:
                    pass
        self.bind("<Destroy>", _cleanup)

    def refresh(self):
        """Fetch latest service catalog records and synchronize both views."""
        self._raw_services = list_services()

        # Update Table records
        rows = [
            {
                'service_id': s['service_id'],
                'name': s['name'],
                'description': s['description'],
                'price': money(s['price'])
            }
            for s in self._raw_services
        ]
        fill_table(self.tree, rows, ("service_id", "name", "description", "price"))

        # Synchronize Cards View
        self._render_cards()
        self._show_active_frame()

    def _get_scaled_image(self, img_path, target_width=340, target_height=180):
        """Load and cache PIL image fitted to exact dimensions."""
        if not img_path or not os.path.isfile(img_path):
            return None

        cache_key = (img_path, target_width, target_height)
        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]

        try:
            with Image.open(img_path) as im:
                fitted = ImageOps.fit(im, (target_width, target_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(fitted)
                self._photo_cache[cache_key] = photo
                return photo
        except Exception:
            return None

    def _render_cards(self):
        """Construct individual card widgets for all services."""
        # Clear existing cards
        for w in self.card_scrollable.winfo_children():
            w.destroy()
        self.card_widgets.clear()
        self._current_cols = 0

        card_width = 340
        card_img_height = 180

        for s in self._raw_services:
            sid = s['service_id']
            sname = s['name']
            sdesc = s['description']
            sprice = s['price']

            # Outer Card Container
            card = tk.Frame(
                self.card_scrollable,
                bg=BG_PANEL,
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE
            )

            # Top Image Section
            img_path = resolve_service_image_path(s)
            photo = self._get_scaled_image(img_path, card_width, card_img_height)

            if photo:
                img_lbl = tk.Label(card, image=photo, bg=BG_PANEL, bd=0)
                img_lbl.image = photo  # Keep reference
                img_lbl.pack(fill="x", side="top")
            else:
                # Sleek modern fallback header if image is not present
                fb_frame = tk.Frame(card, bg="#0f172a", height=130)
                fb_frame.pack(fill="x", side="top")
                fb_frame.pack_propagate(False)

                tk.Label(
                    fb_frame,
                    text="⚡ FLUX ATELIER SERVICE",
                    font=FONT_SMALL_BOLD,
                    fg=EMERALD,
                    bg="#0f172a"
                ).pack(expand=True, pady=(16, 0))
                tk.Label(
                    fb_frame,
                    text=sid,
                    font=FONT_TITLE,
                    fg="#ffffff",
                    bg="#0f172a"
                ).pack(expand=True, pady=(0, 16))

            # Card Body
            body = tk.Frame(card, bg=BG_PANEL, padx=18, pady=16)
            body.pack(fill="both", expand=True)

            # Row 1: Service ID Pill + Price Badge
            meta_row = tk.Frame(body, bg=BG_PANEL)
            meta_row.pack(fill="x", pady=(0, 8))

            id_pill = tk.Label(
                meta_row,
                text=f"  {sid}  ",
                font=FONT_MONO_SM,
                fg=DIM,
                bg="#f1f5f9",
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE,
                pady=2
            )
            id_pill.pack(side="left")

            # Rate Badge
            try:
                val = float(sprice)
            except (ValueError, TypeError):
                val = 0.0

            if val == 0.0:
                rate_text = "FREE DIAGNOSTIC"
                rate_fg = EMERALD
                rate_bg = EMERALD_LIGHT
                rate_bd = EMERALD_BORDER
            else:
                rate_text = money(sprice)
                rate_fg = EMERALD
                rate_bg = EMERALD_LIGHT
                rate_bd = EMERALD_BORDER

            price_badge = tk.Label(
                meta_row,
                text=f" {rate_text} ",
                font=FONT_SMALL_BOLD,
                fg=rate_fg,
                bg=rate_bg,
                bd=0,
                highlightthickness=1,
                highlightbackground=rate_bd,
                pady=2
            )
            price_badge.pack(side="right")

            # Row 2: Service Title
            title_lbl = tk.Label(
                body,
                text=sname,
                font=(FONT_FAMILY, 12, "bold"),
                fg=INK,
                bg=BG_PANEL,
                anchor="w",
                justify="left"
            )
            title_lbl.pack(fill="x", pady=(0, 6))

            # Row 3: Description with minimum visual height
            desc_lbl = tk.Label(
                body,
                text=sdesc,
                font=FONT_SMALL,
                fg=MUTED,
                bg=BG_PANEL,
                anchor="nw",
                justify="left",
                wraplength=300,
                height=3
            )
            desc_lbl.pack(fill="x", pady=(0, 12))

            # Row 4: Hairline Separator
            sep = tk.Frame(body, bg=LINE, height=1)
            sep.pack(fill="x", pady=(0, 12))

            # Row 5: Action & Pricing Footer
            foot_row = tk.Frame(body, bg=BG_PANEL)
            foot_row.pack(fill="x", side="bottom")

            left_cost = tk.Frame(foot_row, bg=BG_PANEL)
            left_cost.pack(side="left", anchor="w")

            cost_caption = "DIAGNOSTIC CHARGE" if val == 0.0 else "BASELINE BENCH FEE"
            tk.Label(
                left_cost,
                text=cost_caption,
                font=("Segoe UI", 7, "bold"),
                fg=DIM,
                bg=BG_PANEL
            ).pack(anchor="w")

            cost_val_str = "₱0.00 (No Fix, No Fee)" if val == 0.0 else money(sprice)
            tk.Label(
                left_cost,
                text=cost_val_str,
                font=FONT_HEADING,
                fg=INK,
                bg=BG_PANEL
            ).pack(anchor="w")

            # Book / Request Repair Action Button
            if self.is_customer or self.on_book_callback:
                action_btn = primary_button(
                    foot_row,
                    "+ Request Repair",
                    command=lambda target_sid=sid: self._handle_book(target_sid),
                    padx=12,
                    pady=5
                )
                action_btn.pack(side="right")
            elif can(self.acting_user['role'], 'manage_services'):
                action_btn = secondary_button(
                    foot_row,
                    "Edit Rate",
                    command=lambda target_s=s: self._open_edit_modal_for(target_s),
                    padx=10,
                    pady=4
                )
                action_btn.pack(side="right")

            # Tactile hover effect on card
            def _on_enter(e, c=card):
                c.configure(highlightbackground=EMERALD_BORDER, highlightthickness=1)

            def _on_leave(e, c=card):
                c.configure(highlightbackground=LINE, highlightthickness=1)

            card.bind("<Enter>", _on_enter)
            card.bind("<Leave>", _on_leave)

            self.card_widgets.append(card)

        # Trigger grid layout
        cur_w = self.card_canvas.winfo_width()
        self._regrid_cards(cur_w if cur_w > 100 else 1200)

    def _regrid_cards(self, available_width):
        """Adaptively organize cards into 1, 2, or 3 responsive columns."""
        if available_width > 1150:
            cols = 3
        elif available_width > 750:
            cols = 2
        else:
            cols = 1

        if self._current_cols == cols and len(self.card_widgets) > 0:
            return

        self._current_cols = cols

        for i, card in enumerate(self.card_widgets):
            r = i // cols
            c = i % cols
            card.grid(row=r, column=c, padx=12, pady=12, sticky="nsew")

        for c in range(3):
            if c < cols:
                self.card_scrollable.grid_columnconfigure(c, weight=1, uniform="svc_card")
            else:
                self.card_scrollable.grid_columnconfigure(c, weight=0)

        self.card_scrollable.update_idletasks()
        self.card_canvas.configure(scrollregion=self.card_canvas.bbox("all"))

    def _handle_book(self, service_id=None):
        """Open the repair intake booking modal with optional preselected service."""
        if self.on_book_callback:
            try:
                self.on_book_callback(service_id)
            except TypeError:
                self.on_book_callback()
        else:
            messagebox.showinfo("Request Repair", "Please proceed to the 'Track Repair' or 'Dashboard' tab to submit an intake request.")

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

    def _open_edit_modal_for(self, service):
        if service:
            ServiceFormModal(self, "Edit Service", self.acting_user, service=service, on_save_callback=self.refresh)

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
