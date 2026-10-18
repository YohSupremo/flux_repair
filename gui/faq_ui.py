import tkinter as tk
from tkinter import ttk
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_SM
)
from gui.widgets import primary_button, secondary_button


FAQ_DATA = [
    {
        "cat": "Warranty",
        "q": "What is covered under the 90-Day Written Warranty?",
        "a": (
            "Every micro-soldering repair, IC rework, power rail restoration, and replacement part fitted "
            "by FLUX Repair Co. is backed by our comprehensive 90-calendar-day written warranty.\n\n"
            "If the exact same symptom or fitted component fails during normal daily use within 90 days, "
            "we will re-service your hardware at zero charge or refund 100% of your labor fee upon request. "
            "Coverage does not apply to subsequent drops, broken physical screens, or new liquid exposure after delivery."
        )
    },
    {
        "cat": "Warranty",
        "q": "How does the No Fix, No Fee Guarantee work?",
        "a": (
            "We believe customers should never pay for diagnostic attempts that do not result in a working device. "
            "If our technicians open your unit, run microscopic traces, and conclude the logic board cannot be safely "
            "restored, your balance due is zero dollars.\n\n"
            "You only pay when we successfully achieve the agreed-upon repair or recover your critical files."
        )
    },
    {
        "cat": "Turnaround",
        "q": "What are your diagnostic and repair turnaround times?",
        "a": (
            "We provide honest, realistic timelines:\n\n"
            "• Diagnostic Verdict: Within 24 hours of bench intake.\n"
            "• Same-Day Repairs: Batteries, screens, charging ports, and modular replacements (2 to 4 hours).\n"
            "• Board-Level Micro-Soldering: Logic board power rails, backlight ICs, audio ICs (2 to 4 business days).\n"
            "• Severe Liquid Recovery or Data Retrieval: Ultrasonic bath, corrosion mapping, chip-off NAND (3 to 7 business days)."
        )
    },
    {
        "cat": "Liquid Damage",
        "q": "Emergency Liquid Damage: What should I do right now?",
        "a": (
            "If liquid just spilled on your device, follow this emergency bench protocol:\n\n"
            "1. Turn the device completely OFF immediately. Do NOT plug in a charger under any circumstances.\n"
            "2. Do NOT place the unit in raw uncooked rice. Rice dust combines with liquid to form an alkaline paste that damages logic circuits.\n"
            "3. Dry the exterior with a towel, position the keyboard or ports facing downward, and bring the unit into our atelier within 24 to 48 hours for ultrasonic decontamination."
        )
    },
    {
        "cat": "Data Safety",
        "q": "Is my private data safe during hardware repair?",
        "a": (
            "Data privacy is paramount. Unlike franchise retail stores that mandate factory wiping before touching your hardware, "
            "our technicians work exclusively at the component hardware level.\n\n"
            "Your storage drives remain encrypted and untouched. We do not ask for your system password unless peripheral hardware "
            "testing (such as camera or microphone functional tests) specifically requires operating system login."
        )
    },
    {
        "cat": "Payment",
        "q": "What payment methods are accepted and when do I pay?",
        "a": (
            "We accept Cash, Debit, Visa, MasterCard, and direct digital ACH transfers.\n\n"
            "Payment is only collected at the time of pickup or dispatch, after you have verified the repair."
        )
    }
]


class FAQWarrantyView(tk.Frame):
    """
    FAQ and Written Warranty Charter View.
    Provides clear answers to customer questions regarding written 90-day warranties,
    turnaround guarantees, data preservation, and liquid damage triage.
    """
    def __init__(self, parent, acting_user=None, on_book_callback=None):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.on_book_callback = on_book_callback

        self.current_filter = "All"
        self.item_cards = []

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
            text="CLIENT POLICY AND GUARANTEES",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            header,
            text="FAQ and Written Warranty Charter",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 4))

        tk.Label(
            header,
            text="Transparent 90-day written guarantee, clear turnaround promises, and honest component diagnostics.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Main Centered Content Wrap
        wrap = tk.Frame(scrollable_frame, bg=BG, padx=32, pady=24)
        wrap.pack(fill="both", expand=True)

        # Warranty Guarantee Highlight Box
        w_banner = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=EMERALD, padx=24, pady=20)
        w_banner.pack(fill="x", pady=(0, 20))

        tk.Label(
            w_banner,
            text="90-DAY COMPREHENSIVE REPAIR WARRANTY",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            w_banner,
            text="Every device restored at our workshop receives a written warranty deed.",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 6))

        tk.Label(
            w_banner,
            text=(
                "We document the microscopic components replaced and calibrate all circuit voltages before release. "
                "If the original defect reoccurs under normal usage within 90 days, we fix it at zero cost or refund your fee."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL,
            wraplength=840,
            justify="left"
        ).pack(anchor="w")

        # Filter Chips Row
        f_row = tk.Frame(wrap, bg=BG)
        f_row.pack(fill="x", pady=(0, 16))

        tk.Label(f_row, text="Filter by Topic:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG).pack(side="left", padx=(0, 10))

        cats = ["All", "Warranty", "Turnaround", "Liquid Damage", "Data Safety"]
        self.filter_buttons = {}

        for cat in cats:
            btn = tk.Button(
                f_row,
                text=cat,
                font=FONT_SMALL_BOLD if cat == "All" else FONT_SMALL,
                bg=EMERALD if cat == "All" else BG_PANEL,
                fg="#ffffff" if cat == "All" else INK,
                activebackground=EMERALD_HOVER,
                activeforeground="#ffffff",
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE,
                padx=14,
                pady=5,
                cursor="hand2",
                command=lambda c=cat: self._set_filter(c)
            )
            btn.pack(side="left", padx=4)
            self.filter_buttons[cat] = btn

        # Accordion Container
        self.acc_container = tk.Frame(wrap, bg=BG)
        self.acc_container.pack(fill="x", pady=(0, 24))

        self._render_accordion()

        # Bottom Booking CTA Box
        cta_card = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=28, pady=24)
        cta_card.pack(fill="x")

        tk.Label(
            cta_card,
            text="Ready to inspect your hardware?",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            cta_card,
            text="Free diagnosis within 24 hours. Zero fee if we cannot fix the fault.",
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 16))

        if self.on_book_callback:
            primary_button(
                cta_card,
                "+ Book Free Diagnostic Intake",
                command=self.on_book_callback
            ).pack(anchor="w")

    def _set_filter(self, cat):
        self.current_filter = cat
        for c, btn in self.filter_buttons.items():
            if c == cat:
                btn.configure(bg=EMERALD, fg="#ffffff", font=FONT_SMALL_BOLD)
            else:
                btn.configure(bg=BG_PANEL, fg=INK, font=FONT_SMALL)
        self._render_accordion()

    def _render_accordion(self):
        for child in self.acc_container.winfo_children():
            child.destroy()

        self.item_cards = []

        filtered = [
            item for item in FAQ_DATA
            if self.current_filter == "All" or item["cat"] == self.current_filter
        ]

        for i, item in enumerate(filtered):
            card = tk.Frame(self.acc_container, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)
            card.pack(fill="x", pady=4)

            # Header
            head = tk.Frame(card, bg=BG_PANEL, cursor="hand2", padx=20, pady=16)
            head.pack(fill="x")

            tk.Label(
                head,
                text=item["cat"].upper(),
                font=("Consolas", 8, "bold"),
                fg=EMERALD,
                bg=EMERALD_LIGHT,
                padx=8,
                pady=2
            ).pack(side="left", padx=(0, 14))

            q_lbl = tk.Label(head, text=item["q"], font=FONT_HEADING, fg=INK, bg=BG_PANEL, cursor="hand2")
            q_lbl.pack(side="left", fill="x", expand=True, anchor="w")

            chev_lbl = tk.Label(head, text="v", font=("Segoe UI", 10, "bold"), fg=MUTED, bg=BG_PANEL, width=2)
            chev_lbl.pack(side="right")

            # Body (initially collapsed except first item)
            body = tk.Frame(card, bg=BG_PANEL, padx=20, pady=16)
            a_lbl = tk.Label(
                body,
                text=item["a"],
                font=FONT_BODY,
                fg=MUTED,
                bg=BG_PANEL,
                wraplength=820,
                justify="left"
            )
            a_lbl.pack(anchor="w")

            state = {"open": (i == 0)}
            if state["open"]:
                chev_lbl.configure(text="^", fg=EMERALD)
                body.pack(fill="x")

            def _toggle(b=body, c=chev_lbl, s=state, crd=card):
                if s["open"]:
                    b.pack_forget()
                    c.configure(text="v", fg=MUTED)
                    crd.configure(highlightbackground=LINE)
                    s["open"] = False
                else:
                    b.pack(fill="x")
                    c.configure(text="^", fg=EMERALD)
                    crd.configure(highlightbackground=EMERALD)
                    s["open"] = True

            for w in (head, q_lbl, chev_lbl):
                w.bind("<Button-1>", lambda e, fn=_toggle: fn())
                w.bind("<Enter>", lambda e, crd=card: crd.configure(highlightbackground=EMERALD))
                w.bind("<Leave>", lambda e, crd=card, s=state: crd.configure(highlightbackground=EMERALD if s["open"] else LINE))
