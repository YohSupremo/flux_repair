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


class MainMenuView(tk.Frame):
    """
    Main Application Shell (FR-03, FR-06, FR-57).
    Houses the role-aware sidebar navigation, operator telemetry pill, live clock,
    and dynamically swapped module screens.
    """
    def __init__(self, parent, current_user, on_logout_callback):
        super().__init__(parent, bg=BG)
        self.current_user = current_user
        self.on_logout_callback = on_logout_callback

        self.current_view_name = "dashboard"
        self.views = {}

        self._build_shell()
        self._show_view("dashboard")
        self._update_clock()

    def _build_shell(self):
        # Left Sidebar (Midnight Slate Atelier)
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

        sub_brand = "Customer Service Portal" if self.current_user['role'] == 'Customer' else "Cleanroom Laboratory & Console"
        tk.Label(
            brand_box,
            text=sub_brand,
            font=FONT_SMALL,
            fg=SIDEBAR_MUTED,
            bg=SIDEBAR_BG
        ).pack(anchor="w", pady=(3, 0))

        # Thin divider
        tk.Frame(self.sidebar, bg="#1e293b", height=1).pack(fill="x", pady=(0, 16))

        # Navigation Buttons Container
        self.nav_container = tk.Frame(self.sidebar, bg=SIDEBAR_BG, padx=12)
        self.nav_container.pack(fill="both", expand=True)

        self.nav_buttons = {}
        role = self.current_user['role']

        # Role-based menu items (FR-03, FR-57)
        jobs_label = "My Repairs" if role == 'Customer' else "Job Orders"
        dash_label = "Overview" if role == 'Customer' else "Dashboard"
        menu_items = [
            ("dashboard", dash_label, True),
            ("jobs", jobs_label, True),
            ("customers", "Customers", role in ('Admin', 'Staff')),
            ("catalog", "Service Catalog", True),
            ("parts", "Parts Inventory", role in ('Admin', 'Staff', 'Technician')),
            ("reports", "Reports & Sales", role in ('Admin', 'Staff')),
            ("users", "User Accounts", role == 'Admin'),
        ]

        for view_key, label_text, allowed in menu_items:
            if allowed:
                btn = self._create_nav_button(self.nav_container, view_key, label_text)
                btn.pack(fill="x", pady=2)
                self.nav_buttons[view_key] = btn

        # Bottom Operator Profile & Logout Bar
        bot_box = tk.Frame(self.sidebar, bg="#0b1120", padx=16, pady=16)
        bot_box.pack(fill="x", side="bottom")

        # Operator info
        op_row = tk.Frame(bot_box, bg="#0b1120")
        op_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            op_row,
            text=self.current_user['full_name'],
            font=FONT_SMALL_BOLD,
            fg=SIDEBAR_INK,
            bg="#0b1120"
        ).pack(anchor="w")

        r_chip = tk.Frame(op_row, bg=SIDEBAR_BG, padx=6, pady=1)
        r_chip.pack(anchor="w", pady=(2, 0))
        tk.Label(
            r_chip,
            text=self.current_user['role'].upper(),
            font=("Consolas", 8, "bold"),
            fg=SIDEBAR_ACTIVE,
            bg=SIDEBAR_BG
        ).pack()

        # Logout button (FR-06)
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

        telemetry_text = "CLIENT PORTAL ONLINE" if self.current_user['role'] == 'Customer' else "ATELIER BENCH ONLINE"
        tk.Label(
            telemetry_chip,
            text=telemetry_text,
            font=("Consolas", 8, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT
        ).pack()

        # View Host Frame
        self.view_host = tk.Frame(self.right_container, bg=BG)
        self.view_host.pack(fill="both", expand=True)

    def _create_nav_button(self, parent, view_key, text):
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

    def _show_view(self, view_key):
        # Update nav button appearances
        for k, btn in self.nav_buttons.items():
            if k == view_key:
                btn.configure(bg=SIDEBAR_HOVER, fg=SIDEBAR_ACTIVE, font=FONT_BODY_BOLD)
            else:
                btn.configure(bg=SIDEBAR_BG, fg=SIDEBAR_MUTED, font=FONT_BODY)

        # Clear existing view in host
        for child in self.view_host.winfo_children():
            child.pack_forget()

        # Instantiate or re-display view
        if view_key == "dashboard":
            view = DashboardView(self.view_host, self.current_user, self._show_view)
        elif view_key == "jobs":
            view = JobsView(self.view_host, self.current_user)
        elif view_key == "customers":
            view = CustomersView(self.view_host, self.current_user, on_open_job_callback=lambda: self._show_view("jobs"))
        elif view_key == "catalog":
            view = CatalogView(self.view_host, self.current_user)
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
        now_str = datetime.datetime.now().strftime("%A, %B %d, %Y  •  %H:%M:%S")
        self.clock_lbl.configure(text=f"System Time: {now_str}")
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

        sub_text = "Customer Service Portal  •  Track your registered hardware and service estimates" if is_customer else f"Workshop Console  •  Role: {self.acting_user['role']}  •  Active Station: Bench #1"

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
        scrollable_frame = tk.Frame(canvas, bg=BG, padx=20, pady=12)

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
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_dash_wheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Top Metric Cards Row
        m_row = tk.Frame(scrollable_frame, bg=BG)
        m_row.pack(fill="x", pady=(0, 20))

        def _metric_box(parent, title, accent_color=EMERALD):
            card = tk.Frame(parent, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)
            card.pack(side="left", fill="both", expand=True, padx=4)

            tk.Label(card, text=title.upper(), font=("Segoe UI", 9, "bold"), fg=MUTED, bg=BG_PANEL).pack(anchor="w")
            lbl = tk.Label(card, text="0", font=("Segoe UI", 22, "bold"), fg=accent_color, bg=BG_PANEL)
            lbl.pack(anchor="w", pady=(4, 0))
            return lbl

        if is_customer:
            self.metric_active = _metric_box(m_row, "Devices Under Repair", BLUE)
            self.metric_pickup = _metric_box(m_row, "Ready for Pickup", EMERALD)
            self.metric_past = _metric_box(m_row, "Past Completed Repairs", DIM)
        else:
            self.metric_under_repair = _metric_box(m_row, "Under Bench Repair", BLUE)
            self.metric_waiting_parts = _metric_box(m_row, "Waiting for Parts", PURPLE)
            self.metric_received = _metric_box(m_row, "New Intake Received", AMBER)
            self.metric_completed = _metric_box(m_row, "Ready for Release", EMERALD)

        # Quick Shortcuts Banner
        act_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=14)
        act_card.pack(fill="x", pady=(0, 20))

        shortcuts_title = "YOUR QUICK ACTIONS" if is_customer else "QUICK SHORTCUTS & COMMON OPERATIONS"
        tk.Label(act_card, text=shortcuts_title, font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))

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
        r_card = tk.Frame(scrollable_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=16)
        r_card.pack(fill="x")

        table_title = "MY REGISTERED DEVICES & REPAIR TICKETS" if is_customer else "RECENT REPAIR ORDERS ON BENCH"
        tk.Label(r_card, text=table_title, font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))

        cols = ("job_id", "customer", "device", "priority", "status", "date")
        heads = ("Job ID", "Account Name", "Device Specification", "Priority", "Status", "Date Received")
        self.r_frame, self.r_tree = make_table(r_card, cols, heads, (80, 180, 240, 80, 120, 140))
        self.r_tree.configure(height=6)
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
            "FLUX Repair Co. — Workshop Contact",
            "Atelier Facility:\n118 Beacon Works, Unit 3, Old Mill District\n\n"
            "Telephone: (555) 019-3350\n"
            "Email: bench@fluxrepair.co\n\n"
            "Hours of Operation:\n"
            "• Mon - Fri: 9:00 AM - 7:00 PM\n"
            "• Saturday: 10:00 AM - 5:00 PM\n"
            "• Sunday: Closed"
        )

    def _open_new_job_modal(self):
        JobIntakeModal(self, self.acting_user, on_job_created_callback=self.refresh)

    def _open_selected_job(self):
        sel = self.r_tree.selection()
        if not sel:
            return
        jid = self.r_tree.item(sel[0], "values")[0]
        JobDetailsModal(self, jid, self.acting_user, on_refresh_callback=self.refresh)
