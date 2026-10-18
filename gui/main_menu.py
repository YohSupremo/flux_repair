import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED, AMBER, BLUE, PURPLE,
    SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_ACTIVE, SIDEBAR_INK, SIDEBAR_MUTED,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_SM
)
from gui.widgets import (
    primary_button, secondary_button, make_table, fill_table, status_badge
)
from logic.auth import can
from logic.reports import status_counts, pending_jobs
from logic.jobs import list_jobs
from logic.customers import list_customers
from gui.customers_ui import CustomersView
from gui.catalog_ui import CatalogView
from gui.parts_ui import PartsView
from gui.jobs_ui import JobsView
from gui.job_form import JobIntakeModal
from gui.job_details_ui import JobDetailsModal
from gui.reports_ui import ReportsView
from gui.users_ui import UsersView
from gui.landing_ui import LandingPageView
from gui.about_ui import AboutUsView
from gui.track_ui import TrackRepairView
from gui.faq_ui import FAQWarrantyView
from gui.profile_modal import AccountSettingsModal


class CustomerProfilePopup(tk.Toplevel):
    """
    Modern custom dropdown card popover for the client profile.
    Features user avatar badge, role pill, two-line interactive rows,
    smooth hover highlights, and click-outside dismissal.
    """
    def __init__(self, parent, user, callbacks, anchor_widget):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg="#0f172a", bd=0, highlightthickness=1, highlightbackground="#334155")

        # Top User Header Card
        hdr = tk.Frame(self, bg="#0f172a", padx=16, pady=14)
        hdr.pack(fill="x")

        # Avatar Initial
        av = tk.Canvas(hdr, width=36, height=36, bg="#0f172a", highlightthickness=0)
        av.pack(side="left", padx=(0, 10))
        av.create_oval(2, 2, 34, 34, fill=EMERALD, outline=EMERALD)
        initial = (user.get("full_name") or "U")[0].upper()
        av.create_text(18, 18, text=initial, fill="#ffffff", font=("Segoe UI", 12, "bold"))

        info = tk.Frame(hdr, bg="#0f172a")
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=user.get("full_name", "Customer"), font=("Segoe UI", 10, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w")

        r_row = tk.Frame(info, bg="#0f172a")
        r_row.pack(anchor="w", pady=(2, 0))
        role_title = f"{user.get('role', 'Customer').upper()} ACCOUNT"
        tk.Label(r_row, text=role_title, font=("Consolas", 8, "bold"), fg="#34d399", bg="#064e3b", padx=6, pady=1).pack(side="left")

        # Divider
        tk.Frame(self, bg="#1e293b", height=1).pack(fill="x")

        # Action Items
        for item in callbacks:
            if item is None:
                tk.Frame(self, bg="#1e293b", height=1).pack(fill="x", pady=2)
            else:
                title, subtitle, cmd = item
                self._add_row(title, subtitle, cmd)

        self._position(anchor_widget)
        self._bind_events()

    def _add_row(self, title, sub, cmd):
        row = tk.Frame(self, bg="#0f172a", padx=16, pady=8, cursor="hand2")
        row.pack(fill="x")

        is_signout = ("Sign Out" in title)
        fg_default = "#fca5a5" if is_signout else "#f8fafc"
        fg_hover = "#ef4444" if is_signout else "#34d399"

        t_lbl = tk.Label(row, text=title, font=("Segoe UI", 9, "bold"), fg=fg_default, bg="#0f172a", cursor="hand2")
        t_lbl.pack(anchor="w")
        s_lbl = tk.Label(row, text=sub, font=("Segoe UI", 8), fg="#64748b", bg="#0f172a", cursor="hand2")
        s_lbl.pack(anchor="w", pady=(1, 0))

        def _enter(e):
            row.configure(bg="#1e293b")
            t_lbl.configure(bg="#1e293b", fg=fg_hover)
            s_lbl.configure(bg="#1e293b", fg="#94a3b8")

        def _leave(e):
            row.configure(bg="#0f172a")
            t_lbl.configure(bg="#0f172a", fg=fg_default)
            s_lbl.configure(bg="#0f172a", fg=fg_default if is_signout else "#64748b")

        def _click(e):
            self.destroy()
            cmd()

        for w in (row, t_lbl, s_lbl):
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<Button-1>", _click)

    def _position(self, anchor_widget):
        self.update_idletasks()
        w = 280
        h = self.winfo_reqheight()
        bx = anchor_widget.winfo_rootx()
        by = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 6
        bw = anchor_widget.winfo_width()
        x = max(10, bx + bw - w)
        self.geometry(f"{w}x{h}+{x}+{by}")

    def _bind_events(self):
        self.bind("<Escape>", lambda e: self.destroy())

        def _on_click(event):
            try:
                x, y = self.winfo_pointerxy()
                bx, by = self.winfo_rootx(), self.winfo_rooty()
                bw, bh = self.winfo_width(), self.winfo_height()
                if not (bx <= x <= bx + bw and by <= y <= by + bh):
                    self.destroy()
            except Exception:
                pass

        self.bind_all("<Button-1>", _on_click, add="+")

    def destroy(self):
        try:
            self.unbind_all("<Button-1>")
        except Exception:
            pass
        super().destroy()


class MainMenuView(tk.Frame):
    """
    Main Application Shell (FR-03, FR-06, FR-57).
    Houses the role-aware navigation (horizontal website-style navbar with profile dropdown for Customer,
    workbench sidebar for Admin/Staff/Tech), live clock, and dynamically swapped module screens.
    """
    def __init__(self, parent, current_user, on_logout_callback):
        super().__init__(parent, bg=BG)
        try:
            self.winfo_toplevel().title("FLUX Repair Co.")
        except Exception:
            pass
        self.current_user = current_user
        self.on_logout_callback = on_logout_callback

        self.is_customer = (self.current_user['role'] == 'Customer')
        self.current_view_name = "dashboard"
        self.views = {}
        self.nav_buttons = {}
        self._active_profile_popup = None

        self._build_shell()
        self._show_view(self.current_view_name)
        self._update_clock()

    def _build_shell(self):
        role = self.current_user['role']

        if self.is_customer:
            # ---------------- CUSTOMER: HORIZONTAL TOP NAVBAR ----------------
            # ---------------- CUSTOMER: FULL-WIDTH TOP NAVIGATION BAR ----------------
            self.top_nav = tk.Frame(self, bg=SIDEBAR_BG, bd=0, highlightthickness=1, highlightbackground="#1e293b")
            self.top_nav.pack(side="top", fill="x")

            # Inner navigation container with generous horizontal and vertical padding
            nav_inner = tk.Frame(self.top_nav, bg=SIDEBAR_BG, padx=32, pady=12)
            nav_inner.pack(fill="x")

            # Brand Box on Left
            brand_box = tk.Frame(nav_inner, bg=SIDEBAR_BG, cursor="hand2")
            brand_box.pack(side="left")
            brand_box.bind("<Button-1>", lambda e: self._show_view("dashboard"))

            b_title = tk.Frame(brand_box, bg=SIDEBAR_BG)
            b_title.pack(anchor="w")

            l_flux = tk.Label(b_title, text="FLUX", font=("Segoe UI", 16, "bold"), fg=SIDEBAR_INK, bg=SIDEBAR_BG)
            l_flux.pack(side="left")
            l_flux.bind("<Button-1>", lambda e: self._show_view("dashboard"))

            l_sub = tk.Label(b_title, text=" REPAIR CO.", font=("Segoe UI", 10, "bold"), fg=SIDEBAR_ACTIVE, bg=SIDEBAR_BG)
            l_sub.pack(side="left", pady=(2, 0))
            l_sub.bind("<Button-1>", lambda e: self._show_view("dashboard"))

            tk.Label(brand_box, text="Client Portal", font=FONT_SMALL, fg=SIDEBAR_MUTED, bg=SIDEBAR_BG).pack(anchor="w", pady=(1, 0))

            # Horizontal Navigation Links
            self.nav_container = tk.Frame(nav_inner, bg=SIDEBAR_BG)
            self.nav_container.pack(side="left", padx=(36, 0))

            menu_items = [
                ("dashboard", "Dashboard", True),
                ("services", "Services", True),
                ("track", "Track Repair", True),
                ("faq", "FAQ & Warranty", True),
                ("about", "About Us", True),
            ]

            for view_key, label_text, allowed in menu_items:
                if allowed:
                    btn = self._create_horizontal_nav_button(self.nav_container, view_key, label_text)
                    btn.pack(side="left", padx=4, pady=2)
                    self.nav_buttons[view_key] = btn

            # Profile Dropdown, Clock, and Sign Out on Right
            right_box = tk.Frame(nav_inner, bg=SIDEBAR_BG)
            right_box.pack(side="right")

            self.clock_lbl = tk.Label(right_box, text="", font=FONT_MONO_SM, fg=SIDEBAR_MUTED, bg=SIDEBAR_BG)
            self.clock_lbl.pack(side="left", padx=(0, 20))

            # Profile Trigger Button with Avatar Chip
            self.profile_btn = tk.Frame(right_box, bg="#1e293b", padx=10, pady=5, cursor="hand2", bd=0, highlightthickness=1, highlightbackground="#334155")
            self.profile_btn.pack(side="left", padx=(0, 14))

            self.av_cv = tk.Canvas(self.profile_btn, width=24, height=24, bg="#1e293b", highlightthickness=0)
            self.av_cv.pack(side="left", padx=(2, 8))
            self.av_cv.create_oval(2, 2, 22, 22, fill=EMERALD, outline=EMERALD)
            initial = (self.current_user.get('full_name') or "U")[0].upper()
            self.av_txt_id = self.av_cv.create_text(12, 12, text=initial, fill="#ffffff", font=("Segoe UI", 9, "bold"))

            self.lbl_profile_name = tk.Label(self.profile_btn, text=self.current_user['full_name'], font=FONT_SMALL_BOLD, fg=SIDEBAR_INK, bg="#1e293b", cursor="hand2")
            self.lbl_profile_name.pack(side="left", padx=(0, 8))

            lbl_chev = tk.Label(self.profile_btn, text="v", font=("Segoe UI", 8, "bold"), fg=EMERALD, bg="#1e293b", cursor="hand2")
            lbl_chev.pack(side="left", padx=(0, 4))

            def _btn_enter(e):
                self.profile_btn.configure(bg=SIDEBAR_HOVER, highlightbackground=EMERALD)
                self.lbl_profile_name.configure(bg=SIDEBAR_HOVER)
                lbl_chev.configure(bg=SIDEBAR_HOVER)
                self.av_cv.configure(bg=SIDEBAR_HOVER)

            def _btn_leave(e):
                if not (self._active_profile_popup and self._active_profile_popup.winfo_exists()):
                    self.profile_btn.configure(bg="#1e293b", highlightbackground="#334155")
                    self.lbl_profile_name.configure(bg="#1e293b")
                    lbl_chev.configure(bg="#1e293b")
                    self.av_cv.configure(bg="#1e293b")

            for w in (self.profile_btn, self.av_cv, self.lbl_profile_name, lbl_chev):
                w.bind("<Enter>", _btn_enter)
                w.bind("<Leave>", _btn_leave)
                w.bind("<Button-1>", lambda e: self._popup_profile_menu())

            logout_btn = tk.Button(
                right_box,
                text="Sign Out",
                command=self.on_logout_callback,
                font=FONT_SMALL_BOLD,
                bg="#1e293b",
                fg=SIDEBAR_INK,
                activebackground=RED,
                activeforeground="#ffffff",
                bd=0,
                cursor="hand2",
                padx=14,
                pady=6
            )
            logout_btn.pack(side="left")

            # View Host Frame fills remaining window
            self.view_host = tk.Frame(self, bg=BG)
            self.view_host.pack(fill="both", expand=True)

        else:
            # ---------------- ADMIN / STAFF / TECH: WORKBENCH SIDEBAR ----------------
            self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=240)
            self.sidebar.pack(side="left", fill="y")
            self.sidebar.pack_propagate(False)

            # Brand Banner
            brand_box = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=20, pady=24)
            brand_box.pack(fill="x")

            b_title = tk.Frame(brand_box, bg=SIDEBAR_BG)
            b_title.pack(anchor="w")

            tk.Label(
                b_title,
                text="FLUX",
                font=("Segoe UI", 16, "bold"),
                fg=SIDEBAR_INK,
                bg=SIDEBAR_BG
            ).pack(side="left")

            tk.Label(
                b_title,
                text=" REPAIR CO.",
                font=("Segoe UI", 10, "bold"),
                fg=SIDEBAR_ACTIVE,
                bg=SIDEBAR_BG
            ).pack(side="left", pady=(3, 0))

            tk.Label(
                brand_box,
                text="Cleanroom Laboratory & Console",
                font=FONT_SMALL,
                fg=SIDEBAR_MUTED,
                bg=SIDEBAR_BG
            ).pack(anchor="w", pady=(3, 0))

            # Thin divider
            tk.Frame(self.sidebar, bg="#1e293b", height=1).pack(fill="x", pady=(0, 16))

            # Navigation Buttons Container
            self.nav_container = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=12)
            self.nav_container.pack(fill="both", expand=True)

            menu_items = [
                ("dashboard", "Dashboard", True),
                ("website", "Website", True),
                ("jobs", "Job Orders", True),
                ("track", "Track Repair", True),
                ("customers", "Customers", role in ('Admin', 'Staff')),
                ("catalog", "Service Catalog", True),
                ("faq", "FAQ & Warranty", True),
                ("parts", "Parts Inventory", role in ('Admin', 'Staff', 'Technician')),
                ("reports", "Reports & Sales", role in ('Admin', 'Staff')),
                ("users", "User Accounts", role == 'Admin'),
            ]

            for view_key, label_text, allowed in menu_items:
                if allowed:
                    btn = self._create_vertical_nav_button(self.nav_container, view_key, label_text)
                    btn.pack(fill="x", pady=2)
                    self.nav_buttons[view_key] = btn

            # Bottom Operator Profile & Logout Bar
            bot_box = tk.Frame(self.sidebar, bg="#0b1120", padx=16, pady=16)
            bot_box.pack(fill="x", side="bottom")

            op_row = tk.Frame(bot_box, bg="#0b1120")
            op_row.pack(fill="x", pady=(0, 10))

            self.op_name_lbl = tk.Label(
                op_row,
                text=self.current_user['full_name'],
                font=FONT_SMALL_BOLD,
                fg=SIDEBAR_INK,
                bg="#0b1120"
            )
            self.op_name_lbl.pack(anchor="w")

            r_chip = tk.Frame(op_row, bg=SIDEBAR_BG, padx=6, pady=1)
            r_chip.pack(anchor="w", pady=(2, 0))
            tk.Label(
                r_chip,
                text=self.current_user['role'].upper(),
                font=("Consolas", 8, "bold"),
                fg=SIDEBAR_ACTIVE,
                bg=SIDEBAR_BG
            ).pack()

            settings_btn = tk.Button(
                bot_box,
                text="Account Settings",
                command=self._open_account_settings_modal,
                font=FONT_SMALL,
                bg="#1e293b",
                fg=SIDEBAR_INK,
                activebackground=SIDEBAR_HOVER,
                activeforeground=EMERALD,
                bd=0,
                cursor="hand2",
                padx=12,
                pady=5
            )
            settings_btn.pack(fill="x", pady=(0, 6))

            logout_btn = tk.Button(
                bot_box,
                text="Sign Out",
                command=self.on_logout_callback,
                font=FONT_SMALL_BOLD,
                bg="#1e293b",
                fg=SIDEBAR_INK,
                activebackground=RED,
                activeforeground="#ffffff",
                bd=0,
                cursor="hand2",
                padx=12,
                pady=6
            )
            logout_btn.pack(fill="x")

            # Right Content Area
            self.right_container = tk.Frame(self, bg=BG)
            self.right_container.pack(side="right", fill="both", expand=True)

            # Top Live Telemetry Bar
            self.top_telemetry = tk.Frame(self.right_container, bg=BG_PANEL, padx=24, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
            self.top_telemetry.pack(fill="x")

            self.clock_lbl = tk.Label(
                self.top_telemetry,
                text="",
                font=FONT_MONO_SM,
                fg=DIM,
                bg=BG_PANEL
            )
            self.clock_lbl.pack(side="left")

            telemetry_chip = tk.Frame(self.top_telemetry, bg=EMERALD_LIGHT, padx=10, pady=3, bd=0, highlightthickness=1, highlightbackground="#a7f3d0")
            telemetry_chip.pack(side="right")

            tk.Label(
                telemetry_chip,
                text="ATELIER BENCH ONLINE",
                font=("Consolas", 8, "bold"),
                fg=EMERALD,
                bg=EMERALD_LIGHT
            ).pack()

            # View Host Frame
            self.view_host = tk.Frame(self.right_container, bg=BG)
            self.view_host.pack(fill="both", expand=True)

    def _create_horizontal_nav_button(self, parent, view_key, text):
        btn = tk.Button(
            parent,
            text=text,
            font=FONT_BODY,
            bg=SIDEBAR_BG,
            fg=SIDEBAR_MUTED,
            activebackground=SIDEBAR_HOVER,
            activeforeground=SIDEBAR_INK,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=6,
            command=lambda: self._show_view(view_key)
        )
        def _nav_enter(e):
            if self.current_view_name != view_key:
                btn.configure(bg=SIDEBAR_HOVER, fg=SIDEBAR_INK)
        def _nav_leave(e):
            if self.current_view_name != view_key:
                btn.configure(bg=SIDEBAR_BG, fg=SIDEBAR_MUTED)
        btn.bind("<Enter>", _nav_enter)
        btn.bind("<Leave>", _nav_leave)
        return btn

    def _create_vertical_nav_button(self, parent, view_key, text):
        btn = tk.Button(
            parent,
            text=f"  {text}",
            anchor="w",
            font=FONT_BODY,
            bg=SIDEBAR_BG,
            fg=SIDEBAR_MUTED,
            activebackground=SIDEBAR_HOVER,
            activeforeground=SIDEBAR_INK,
            bd=0,
            cursor="hand2",
            padx=12,
            pady=8,
            command=lambda: self._show_view(view_key)
        )
        def _nav_enter(e):
            if self.current_view_name != view_key:
                btn.configure(bg=SIDEBAR_HOVER, fg=SIDEBAR_INK)
        def _nav_leave(e):
            if self.current_view_name != view_key:
                btn.configure(bg=SIDEBAR_BG, fg=SIDEBAR_MUTED)
        btn.bind("<Enter>", _nav_enter)
        btn.bind("<Leave>", _nav_leave)
        return btn

    def _popup_profile_menu(self):
        if self._active_profile_popup and self._active_profile_popup.winfo_exists():
            self._active_profile_popup.destroy()
            self._active_profile_popup = None
            return

        callbacks = [
            ("Account Overview", "View repair telemetry and estimates", lambda: self._show_view("overview")),
            ("My Repairs", "Track active repair tickets on bench", lambda: self._show_view("jobs")),
            ("Request Device Repair", "Book hardware diagnostic intake slot", self._open_new_job_modal),
            ("Account Settings", "Update profile details and password", self._open_account_settings_modal),
            ("Atelier Contact Info", "Facility hours, telephone, and map", self._show_contact_info),
            None,
            ("Sign Out", "End your client portal session", self.on_logout_callback),
        ]
        self._active_profile_popup = CustomerProfilePopup(
            self,
            self.current_user,
            callbacks,
            self.profile_btn
        )

    def _open_account_settings_modal(self):
        AccountSettingsModal(
            self.winfo_toplevel(),
            self.current_user,
            on_profile_updated_callback=self._on_profile_updated
        )

    def _on_profile_updated(self, updated_user):
        self.current_user = updated_user
        if hasattr(self, 'lbl_profile_name') and self.lbl_profile_name.winfo_exists():
            self.lbl_profile_name.configure(text=updated_user.get('full_name', ''))
        if hasattr(self, 'av_cv') and hasattr(self, 'av_txt_id') and self.av_cv.winfo_exists():
            initial = (updated_user.get('full_name') or "U")[0].upper()
            self.av_cv.itemconfigure(self.av_txt_id, text=initial)
        if hasattr(self, 'op_name_lbl') and self.op_name_lbl.winfo_exists():
            self.op_name_lbl.configure(text=updated_user.get('full_name', ''))

    def _show_contact_info(self):
        messagebox.showinfo(
            "FLUX Repair Co.: Workshop Contact",
            "Atelier Facility:\n118 Beacon Works, Unit 3, Old Mill District\n\n"
            "Telephone: (555) 019-3350\n"
            "Email: bench@fluxrepair.co\n\n"
            "Hours of Operation:\n"
            "Mon - Fri: 9:00 AM - 7:00 PM\n"
            "Saturday: 10:00 AM - 5:00 PM\n"
            "Sunday: Closed"
        )

    def _open_new_job_modal(self):
        JobIntakeModal(self.winfo_toplevel(), self.current_user, on_job_created_callback=lambda: self._show_view("jobs"))

    def _show_view(self, view_key):
        # Update nav button appearances
        for k, btn in self.nav_buttons.items():
            if k == view_key:
                btn.configure(bg=SIDEBAR_HOVER, fg=SIDEBAR_ACTIVE, font=FONT_BODY_BOLD)
            else:
                btn.configure(bg=SIDEBAR_BG, fg=SIDEBAR_MUTED, font=FONT_BODY)

        if hasattr(self, 'profile_btn'):
            if view_key in ("overview", "jobs"):
                self.profile_btn.configure(highlightbackground=SIDEBAR_ACTIVE)
            else:
                self.profile_btn.configure(highlightbackground="#334155")

        # Clear existing view in host
        for child in self.view_host.winfo_children():
            child.destroy()

        # Instantiate or re-display view
        if view_key == "dashboard":
            if self.is_customer:
                view = LandingPageView(
                    self.view_host,
                    current_user=self.current_user,
                    on_open_intake_callback=self._open_new_job_modal
                )
            else:
                view = DashboardView(self.view_host, self.current_user, self._show_view)
        elif view_key == "website":
            view = LandingPageView(
                self.view_host,
                current_user=self.current_user,
                on_open_intake_callback=self._open_new_job_modal
            )
        elif view_key == "overview":
            view = DashboardView(self.view_host, self.current_user, self._show_view)
        elif view_key in ("services", "catalog"):
            view = CatalogView(self.view_host, self.current_user)
        elif view_key == "track":
            view = TrackRepairView(
                self.view_host,
                current_user=self.current_user,
                on_open_intake_callback=self._open_new_job_modal
            )
        elif view_key == "faq":
            view = FAQWarrantyView(
                self.view_host,
                acting_user=self.current_user,
                on_book_callback=self._open_new_job_modal
            )
        elif view_key == "about":
            view = AboutUsView(
                self.view_host,
                acting_user=self.current_user,
                on_book_callback=self._open_new_job_modal
            )
        elif view_key == "jobs":
            view = JobsView(self.view_host, self.current_user)
        elif view_key == "customers":
            view = CustomersView(self.view_host, self.current_user, on_open_job_callback=lambda: self._show_view("jobs"))
        elif view_key == "parts":
            view = PartsView(self.view_host, self.current_user)
        elif view_key == "reports":
            view = ReportsView(self.view_host, self.current_user)
        elif view_key == "users":
            view = UsersView(self.view_host, self.current_user)
        else:
            view = tk.Label(self.view_host, text=f"View {view_key} not found.", font=FONT_BODY, bg=BG)

        view.pack(fill="both", expand=True)
        self.current_view_name = view_key

    def _update_clock(self):
        if not self.winfo_exists():
            return
        now_str = datetime.datetime.now().strftime("%a, %b %d  %H:%M:%S")
        if hasattr(self, 'clock_lbl') and self.clock_lbl.winfo_exists():
            prefix = "" if self.is_customer else "System: "
            self.clock_lbl.configure(text=f"{prefix}{now_str}")
        self.after(1000, self._update_clock)


class DashboardView(tk.Frame):
    """Dashboard homepage view showing real-time workshop metrics or customer device status."""
    def __init__(self, parent, acting_user, nav_callback):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.nav_callback = nav_callback

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        is_customer = (self.acting_user['role'] == 'Customer')

        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text=f"Welcome, {self.acting_user['full_name']}",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w")

        sub_text = "Customer Service Portal: Track your registered hardware and service estimates" if is_customer else f"Workshop Console | Role: {self.acting_user['role']} | Active Station: Bench #1"

        tk.Label(
            title_box,
            text=sub_text,
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        if is_customer:
            primary_button(btn_box, "+ Request Repair", command=self._open_new_job_modal).pack(side="left")
        elif can(self.acting_user['role'], 'create_jobs'):
            primary_button(btn_box, "+ New Repair Job", command=self._open_new_job_modal).pack(side="left")

        # Scrollable content
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG, padx=24, pady=16)

        canvas_win = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_dash_frame_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_dash_canvas_cfg(e):
            canvas.itemconfig(canvas_win, width=e.width)

        scrollable_frame.bind("<Configure>", _on_dash_frame_cfg)
        canvas.bind("<Configure>", _on_dash_canvas_cfg)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _on_dash_wheel(e):
            if self.winfo_exists() and self.winfo_ismapped():
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_dash_wheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-2, "units") if (self.winfo_exists() and self.winfo_ismapped()) else None)
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(2, "units") if (self.winfo_exists() and self.winfo_ismapped()) else None)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Top Metric Cards Row
        m_row = tk.Frame(scrollable_frame, bg=BG)
        m_row.pack(fill="x", pady=(0, 20))

        def _metric_box(parent, title, accent_color=INK, is_highlight=False):
            card = tk.Frame(
                parent,
                bg=BG_PANEL,
                bd=0,
                highlightthickness=1,
                highlightbackground=EMERALD if is_highlight else LINE,
                padx=20,
                pady=16
            )
            card.pack(side="left", fill="both", expand=True, padx=6)

            tk.Label(
                card,
                text=title.upper(),
                font=("Segoe UI", 8, "bold"),
                fg=MUTED,
                bg=BG_PANEL
            ).pack(anchor="w")

            lbl = tk.Label(
                card,
                text="0",
                font=("Segoe UI", 24, "bold"),
                fg=accent_color,
                bg=BG_PANEL
            )
            lbl.pack(anchor="w", pady=(4, 0))
            return lbl

        if is_customer:
            self.metric_active = _metric_box(m_row, "Devices Under Repair", INK)
            self.metric_pickup = _metric_box(m_row, "Ready for Pickup", EMERALD, is_highlight=True)
            self.metric_past = _metric_box(m_row, "Past Completed Repairs", DIM)
        else:
            self.metric_under_repair = _metric_box(m_row, "Under Bench Repair", INK)
            self.metric_waiting_parts = _metric_box(m_row, "Waiting for Parts", MUTED)
            self.metric_received = _metric_box(m_row, "New Intake Received", INK)
            self.metric_completed = _metric_box(m_row, "Ready for Release", EMERALD, is_highlight=True)

        # Quick Shortcuts Banner
        act_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=16)
        act_card.pack(fill="x", pady=(0, 20))

        shortcuts_title = "Quick Actions" if is_customer else "Quick Operations"
        tk.Label(act_card, text=shortcuts_title, font=FONT_HEADING, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 12))

        act_row = tk.Frame(act_card, bg=BG_PANEL)
        act_row.pack(fill="x")

        if is_customer:
            primary_button(act_row, "+ Request Repair", command=self._open_new_job_modal).pack(side="left", padx=(0, 8))
            secondary_button(act_row, "View My Repairs", command=lambda: self.nav_callback("jobs")).pack(side="left", padx=(0, 8))
            secondary_button(act_row, "Service Pricing Catalog", command=lambda: self.nav_callback("catalog")).pack(side="left", padx=(0, 8))
            secondary_button(act_row, "Workshop Contact & Hours", command=self._show_contact_info).pack(side="left")
        else:
            secondary_button(act_row, "Browse Active Tickets", command=lambda: self.nav_callback("jobs")).pack(side="left", padx=(0, 8))
            if can(self.acting_user['role'], 'customers'):
                secondary_button(act_row, "Open Customer Directory", command=lambda: self.nav_callback("customers")).pack(side="left", padx=(0, 8))
            if can(self.acting_user['role'], 'manage_parts'):
                secondary_button(act_row, "Hardware Parts Stock", command=lambda: self.nav_callback("parts")).pack(side="left", padx=(0, 8))
            secondary_button(act_row, "Service Pricing Catalog", command=lambda: self.nav_callback("catalog")).pack(side="left")

        # Recent Tickets Table
        r_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=16)
        r_card.pack(fill="x")

        table_title = "Registered Devices and Tickets" if is_customer else "Recent Repair Orders on Bench"
        tk.Label(r_card, text=table_title, font=FONT_HEADING, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 12))

        cols = ("job_id", "customer", "device", "priority", "status", "date")
        heads = ("Job ID", "Account Name", "Device Specification", "Priority", "Status", "Date Received")
        self.r_frame, self.r_tree = make_table(r_card, cols, heads, (80, 180, 240, 80, 120, 140))
        self.r_tree.configure(height=7)
        self.r_frame.pack(fill="x")

        self.r_tree.bind("<Double-1>", lambda e: self._open_selected_job())

    def refresh(self):
        is_customer = (self.acting_user['role'] == 'Customer')
        if is_customer:
            c_name = self.acting_user['full_name']
            my_jobs = list_jobs(customer_name_filter=c_name)
            active_count = sum(1 for j in my_jobs if j['status'] not in ('Completed', 'Released', 'Cancelled'))
            pickup_count = sum(1 for j in my_jobs if j['status'] == 'Completed')
            past_count = sum(1 for j in my_jobs if j['status'] == 'Released')

            self.metric_active.configure(text=str(active_count))
            self.metric_pickup.configure(text=str(pickup_count))
            self.metric_past.configure(text=str(past_count))

            rows = [
                {
                    'job_id': j['job_id'],
                    'customer': j['customer_name'],
                    'device': f"{j['device_type']} {j['brand']} {j['model']}",
                    'priority': j['priority'],
                    'status': j['status'],
                    'date': j['date_received']
                }
                for j in my_jobs
            ]
            fill_table(self.r_tree, rows, ("job_id", "customer", "device", "priority", "status", "date"))
        else:
            counts = status_counts()
            self.metric_under_repair.configure(text=str(counts.get("Under Repair", 0)))
            self.metric_waiting_parts.configure(text=str(counts.get("Waiting for Parts", 0)))
            self.metric_received.configure(text=str(counts.get("Received", 0)))
            self.metric_completed.configure(text=str(counts.get("Completed", 0)))

            all_j = list_jobs()[:8]
            rows = [
                {
                    'job_id': j['job_id'],
                    'customer': j['customer_name'],
                    'device': f"{j['device_type']} {j['brand']} {j['model']}",
                    'priority': j['priority'],
                    'status': j['status'],
                    'date': j['date_received']
                }
                for j in all_j
            ]
            fill_table(self.r_tree, rows, ("job_id", "customer", "device", "priority", "status", "date"))

    def _show_contact_info(self):
        messagebox.showinfo(
            "FLUX Repair Co.: Workshop Contact",
            "Atelier Facility:\n118 Beacon Works, Unit 3, Old Mill District\n\n"
            "Telephone: (555) 019-3350\n"
            "Email: bench@fluxrepair.co\n\n"
            "Hours of Operation:\n"
            "Mon - Fri: 9:00 AM - 7:00 PM\n"
            "Saturday: 10:00 AM - 5:00 PM\n"
            "Sunday: Closed"
        )

    def _open_new_job_modal(self):
        JobIntakeModal(self, self.acting_user, on_job_created_callback=self.refresh)

    def _open_selected_job(self):
        sel = self.r_tree.selection()
        if not sel:
            return
        jid = self.r_tree.item(sel[0], "values")[0]
        JobDetailsModal(self, jid, self.acting_user, on_refresh_callback=self.refresh)
