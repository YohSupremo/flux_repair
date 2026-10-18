import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_SM
)
from gui.widgets import primary_button, secondary_button
from logic.jobs import list_jobs, job_details, find_job
from gui.job_details_ui import JobDetailsModal


class TrackRepairView(tk.Frame):
    """
    Track Repair View (Client Portal and Workshop Tracker).
    Enables quick status lookup by Job ID or Serial Number with interactive
    stepper timeline, diagnostic logs, and direct ticket details.
    """
    def __init__(self, parent, current_user=None, on_open_intake_callback=None):
        super().__init__(parent, bg=BG)
        self.current_user = current_user
        self.on_open_intake_callback = on_open_intake_callback

        self._build_ui()

    def _build_ui(self):
        # Scrollable container
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg=BG)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        win_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(win_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            if self.winfo_exists() and self.winfo_ismapped() and canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Top Header Banner
        header = tk.Frame(scrollable_frame, bg=BG_PANEL, padx=32, pady=20, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        tk.Label(
            header,
            text="REPAIR ORDER TRACKING",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Live Repair Status and Bench Telemetry",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 4))

        tk.Label(
            header,
            text="Enter your Job Ticket ID or Serial Number to inspect current bench stage and diagnostic notes.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Main Centered Content Wrap
        wrap = tk.Frame(scrollable_frame, bg=BG, padx=32, pady=24)
        wrap.pack(fill="both", expand=True)

        # Search Card
        search_card = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        search_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            search_card,
            text="Lookup Repair Ticket",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            search_card,
            text="Search by Job ID (e.g. J-0001, J-0002) or Device Serial Number:",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 10))

        input_row = tk.Frame(search_card, bg=BG_PANEL)
        input_row.pack(fill="x", pady=(0, 12))

        self.query_var = tk.StringVar()
        entry = tk.Entry(
            input_row,
            textvariable=self.query_var,
            font=("Segoe UI", 12),
            bg=BG_INPUT,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE_BRIGHT,
            highlightcolor=EMERALD
        )
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 12))
        entry.bind("<Return>", lambda e: self._perform_lookup())

        btn_track = primary_button(input_row, "Track Repair ->", command=self._perform_lookup)
        btn_track.pack(side="right")

        # Registered jobs quick chips for logged-in user
        if self.current_user and self.current_user.get('role') == 'Customer':
            c_name = self.current_user.get('full_name')
            my_jobs = list_jobs(customer_name_filter=c_name)
            if my_jobs:
                quick_row = tk.Frame(search_card, bg=BG_PANEL)
                quick_row.pack(fill="x", pady=(8, 0))

                tk.Label(
                    quick_row,
                    text="Your Active Repairs:",
                    font=FONT_SMALL_BOLD,
                    fg=MUTED,
                    bg=BG_PANEL
                ).pack(side="left", padx=(0, 8))

                for j in my_jobs[:4]:
                    jid = j['job_id']
                    lbl_chip = f"{jid} ({j['device_type']})"
                    chip_btn = tk.Button(
                        quick_row,
                        text=lbl_chip,
                        font=FONT_SMALL,
                        bg=BG_HOVER,
                        fg=INK,
                        activebackground=EMERALD_LIGHT,
                        activeforeground=EMERALD,
                        bd=0,
                        highlightthickness=1,
                        highlightbackground=LINE,
                        padx=8,
                        pady=2,
                        cursor="hand2",
                        command=lambda target_id=jid: self._track_specific_id(target_id)
                    )
                    chip_btn.pack(side="left", padx=4)

        # Result Container
        self.result_container = tk.Frame(wrap, bg=BG)
        self.result_container.pack(fill="both", expand=True)

        # Show empty guide card initially
        self._show_initial_guide()

    def _track_specific_id(self, jid):
        self.query_var.set(jid)
        self._perform_lookup()

    def _show_initial_guide(self):
        for child in self.result_container.winfo_children():
            child.destroy()

        card = tk.Frame(self.result_container, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=28, pady=24)
        card.pack(fill="x")

        tk.Label(
            card,
            text="Bench Stage Progression Guide",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            card,
            text="Every device at FLUX Repair Co. transitions through five documented stages:",
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 16))

        steps = [
            ("01. Received", "Device is checked into the atelier, serial recorded, and placed in ESD protective bin."),
            ("02. Diagnostic", "Board inspection under microscope, thermal imaging, and shorted rail isolation."),
            ("03. In Repair", "Precision component-level micro-soldering, IC replacement, or trace repair."),
            ("04. Testing and QA", "72-hour continuous thermal and benchmark stress testing before certification."),
            ("05. Ready for Pickup", "Cleaned with ESD-safe solvents, packaged, and ready for release.")
        ]

        for num_title, desc in steps:
            row = tk.Frame(card, bg=BG_PANEL)
            row.pack(fill="x", pady=6)

            tk.Label(
                row,
                text=num_title,
                font=FONT_BODY_BOLD,
                fg=EMERALD,
                bg=BG_PANEL,
                width=20,
                anchor="w"
            ).pack(side="left")

            tk.Label(
                row,
                text=desc,
                font=FONT_BODY,
                fg=MUTED,
                bg=BG_PANEL
            ).pack(side="left")

    def _perform_lookup(self):
        raw_q = self.query_var.get().strip()
        if not raw_q:
            messagebox.showinfo("Lookup", "Please enter a Job ID or Serial Number.")
            return

        all_jobs = list_jobs()
        matched_job = None

        # Try exact Job ID match
        clean_q = raw_q.upper()
        for j in all_jobs:
            if j['job_id'].upper() == clean_q:
                matched_job = j
                break

        # If not found by ID, try matching Serial No
        if not matched_job:
            for j in all_jobs:
                if j.get('serial_no', '').upper() == clean_q:
                    matched_job = j
                    break

        if not matched_job:
            self._show_not_found(raw_q)
            return

        self._render_job_telemetry(matched_job['job_id'])

    def _show_not_found(self, query):
        for child in self.result_container.winfo_children():
            child.destroy()

        card = tk.Frame(self.result_container, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=28, pady=24)
        card.pack(fill="x")

        tk.Label(
            card,
            text="No Ticket Found",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            card,
            text=f"No active repair order matches query: \"{query}\".",
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            card,
            text="Please verify the Job ID printed on your intake claim slip (e.g. J-0001) or check your device serial number.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

    def _render_job_telemetry(self, job_id):
        for child in self.result_container.winfo_children():
            child.destroy()

        details = job_details(job_id)
        job = details['job']
        cust = details['customer'] or {}
        st = details['status']

        # Results Card
        card = tk.Frame(self.result_container, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=28, pady=24)
        card.pack(fill="x", pady=(0, 16))

        # Top Header Row of Result
        top_row = tk.Frame(card, bg=BG_PANEL)
        top_row.pack(fill="x", pady=(0, 16))

        id_box = tk.Frame(top_row, bg=BG_PANEL)
        id_box.pack(side="left")

        tk.Label(
            id_box,
            text=f"TICKET {job['job_id']}",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w")

        dev_title = f"{job['device_type']} : {job['brand']} {job['model']}"
        tk.Label(
            id_box,
            text=dev_title,
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # Status Badge
        st_box = tk.Frame(top_row, bg=BG_PANEL)
        st_box.pack(side="right")

        st_chip = tk.Frame(st_box, bg=EMERALD_LIGHT, padx=14, pady=6, highlightthickness=1, highlightbackground=EMERALD)
        st_chip.pack(anchor="e")

        tk.Label(
            st_chip,
            text=f"STAGE: {st.upper()}",
            font=FONT_BODY_BOLD,
            fg=EMERALD,
            bg=EMERALD_LIGHT
        ).pack()

        # Visual Stepper Timeline
        stepper_frame = tk.Frame(card, bg=BG_PANEL, pady=16)
        stepper_frame.pack(fill="x")

        stages = [
            ("Received", "Logged in"),
            ("Diagnostic", "Bench triage"),
            ("Under Repair", "Microsoldering"),
            ("Testing", "Stress QA"),
            ("Completed", "Ready for pickup")
        ]

        # Determine index of current stage
        curr_idx = 0
        if st in ("Received", "Cancelled"):
            curr_idx = 0
        elif st == "Waiting for Parts":
            curr_idx = 2
        elif st == "Under Repair":
            curr_idx = 2
        elif st == "Completed":
            curr_idx = 4
        elif st == "Released":
            curr_idx = 4
        else:
            curr_idx = 1

        for i, (stage_name, stage_sub) in enumerate(stages):
            is_active = (i == curr_idx)
            is_past = (i < curr_idx)

            step_box = tk.Frame(stepper_frame, bg=BG_PANEL)
            step_box.pack(side="left", fill="both", expand=True)

            # Node indicator
            node_bg = EMERALD if (is_past or is_active) else BG_HOVER
            node_fg = "#ffffff" if (is_past or is_active) else MUTED
            border_col = EMERALD if (is_past or is_active) else LINE

            node = tk.Label(
                step_box,
                text=str(i + 1),
                font=("Segoe UI", 9, "bold"),
                fg=node_fg,
                bg=node_bg,
                width=3,
                height=1,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=border_col
            )
            node.pack(anchor="center", pady=(0, 6))

            tk.Label(
                step_box,
                text=stage_name,
                font=FONT_BODY_BOLD if is_active else FONT_SMALL_BOLD,
                fg=EMERALD if is_active else (INK if is_past else MUTED),
                bg=BG_PANEL
            ).pack(anchor="center")

            tk.Label(
                step_box,
                text=stage_sub,
                font=("Segoe UI", 8),
                fg=DIM,
                bg=BG_PANEL
            ).pack(anchor="center")

        # Divider
        tk.Frame(card, bg=LINE, height=1).pack(fill="x", pady=16)

        # Two-column Info Grid
        info_grid = tk.Frame(card, bg=BG_PANEL)
        info_grid.pack(fill="x", pady=(0, 16))

        # Left Column: Specs and Intake
        left_col = tk.Frame(info_grid, bg=BG_PANEL)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 16))

        def _data_row(parent, label, value):
            r = tk.Frame(parent, bg=BG_PANEL)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL, width=16, anchor="w").pack(side="left")
            tk.Label(r, text=value, font=FONT_BODY, fg=INK, bg=BG_PANEL, anchor="w").pack(side="left")

        _data_row(left_col, "Customer Name:", cust.get('name', 'N/A'))
        _data_row(left_col, "Serial Number:", job.get('serial_no') or "None Recorded")
        _data_row(left_col, "Intake Condition:", job.get('device_condition') or "Standard Intake")
        _data_row(left_col, "Date Received:", job.get('date_received') or "Recent")

        # Right Column: Financial & Priority
        right_col = tk.Frame(info_grid, bg=BG_PANEL)
        right_col.pack(side="right", fill="both", expand=True, padx=(16, 0))

        bill = details.get('bill') or {}
        _data_row(right_col, "Service Priority:", job.get('priority', 'Standard'))
        _data_row(right_col, "Assigned Tech:", details.get('technician', {}).get('full_name') if details.get('technician') else "Bench Pool")
        _data_row(right_col, "Repair Total:", f"${bill.get('total_amount', '0.00')}")
        _data_row(right_col, "Payment Status:", "PAID IN FULL" if bill.get('is_paid') else f"Balance: ${bill.get('balance_due', '0.00')}")

        # Diagnosis Description
        if job.get('fault_details'):
            f_box = tk.Frame(card, bg=BG_HOVER, padx=16, pady=12, highlightthickness=1, highlightbackground=LINE)
            f_box.pack(fill="x", pady=(0, 16))
            tk.Label(f_box, text="Reported Symptoms and Diagnostic Notes:", font=FONT_SMALL_BOLD, fg=INK, bg=BG_HOVER).pack(anchor="w", pady=(0, 4))
            tk.Label(f_box, text=job['fault_details'], font=FONT_BODY, fg=MUTED, bg=BG_HOVER, wraplength=760, justify="left").pack(anchor="w")

        # Action Buttons Row
        action_row = tk.Frame(card, bg=BG_PANEL)
        action_row.pack(fill="x")

        primary_button(
            action_row,
            "View Full Diagnostic Dossier",
            command=lambda: self._open_modal(job['job_id'])
        ).pack(side="left", padx=(0, 10))

        if self.on_open_intake_callback:
            secondary_button(
                action_row,
                "+ Book Another Repair",
                command=self.on_open_intake_callback
            ).pack(side="left")

    def _open_modal(self, job_id):
        JobDetailsModal(
            self.winfo_toplevel(),
            job_id,
            self.current_user or {'role': 'Customer', 'full_name': 'Guest'},
            on_refresh_callback=lambda: self._render_job_telemetry(job_id)
        )
