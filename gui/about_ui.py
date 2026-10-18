import tkinter as tk
from tkinter import ttk
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_SM
)


class AboutUsView(tk.Frame):
    """
    About Us View (Client Portal and Workshop Info).
    Presents the atelier philosophy, component-level repair standards,
    bench equipment capabilities, written warranties, and facility contact.
    """
    def __init__(self, parent, acting_user=None, on_book_callback=None):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.on_book_callback = on_book_callback

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
            if self.winfo_exists() and canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Top Banner
        header = tk.Frame(scrollable_frame, bg=BG_PANEL, padx=32, pady=20, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        tk.Label(
            header,
            text="ABOUT FLUX REPAIR CO.",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Independent Electronics Repair Atelier and Microsoldering Lab",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 4))

        tk.Label(
            header,
            text="Founded in 2014 | Component-level diagnostics | Zero unnecessary board replacements",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Main Centered Content Wrap
        wrap = tk.Frame(scrollable_frame, bg=BG, padx=32, pady=24)
        wrap.pack(fill="both", expand=True)

        # Mission Manifesto Card
        hero_card = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=28, pady=24)
        hero_card.pack(fill="x", pady=(0, 20))

        tk.Label(
            hero_card,
            text="Our Core Philosophy",
            font=FONT_HEADING,
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            hero_card,
            text="Dead is a diagnosis, not a verdict.",
            font=("Segoe UI", 20, "bold"),
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 10))

        manifesto_text = (
            "Most electronics manufacturers and franchise repair shops treat devices as disposable modules. "
            "When a single power rail shorts or a charging controller fails, their only answer is a costly motherboard "
            "replacement that erases your data and costs more than the machine is worth.\n\n"
            "At FLUX Repair Co., we isolate faults to the individual micro-component. Using high-magnification "
            "microscopes, thermal imaging, and board schematics, we replace the specific 50-cent IC or shorted capacitor. "
            "You keep your original motherboard, preserve your unbacked files, and save up to 70% compared to factory replacements."
        )

        tk.Label(
            hero_card,
            text=manifesto_text,
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL,
            wraplength=840,
            justify="left"
        ).pack(anchor="w", pady=(0, 16))

        # 4 Bench Standards
        tk.Label(wrap, text="ATELIER BENCH CAPABILITIES", font=FONT_SMALL_BOLD, fg=DIM, bg=BG).pack(anchor="w", pady=(10, 8))

        standards_grid = tk.Frame(wrap, bg=BG)
        standards_grid.pack(fill="x", pady=(0, 20))

        caps = [
            ("45x Stereo Micro-Inspection", "Micro-soldering down to 0201 passive components, BGA chip reballing, and torn trace reconstruction under binocular optics."),
            ("Ultrasonic Chemical Decontamination", "Multi-stage Branson ultrasonic bath with specialized flux and corrosion cleaners to reverse severe liquid damage."),
            ("Data-First Rescue Priority", "Direct NAND chip-off extraction and firmware rebuilds to rescue photos and work before invasive hardware rework begins."),
            ("72-Hour Quality Stress Testing", "Every repaired unit undergoes thermal stress, battery discharge curves, and load benchmarks before customer release.")
        ]

        for i, (cap_title, cap_desc) in enumerate(caps):
            card = tk.Frame(standards_grid, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=16)
            card.pack(fill="x", pady=4)

            tk.Label(card, text=f"0{i+1}", font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w")
            tk.Label(card, text=cap_title, font=FONT_HEADING, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(2, 4))
            tk.Label(card, text=cap_desc, font=FONT_BODY, fg=MUTED, bg=BG_PANEL, wraplength=820, justify="left").pack(anchor="w")

        # 4 Guarantees
        tk.Label(wrap, text="OUR CLIENT COMMITMENTS", font=FONT_SMALL_BOLD, fg=DIM, bg=BG).pack(anchor="w", pady=(10, 8))

        commit_box = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        commit_box.pack(fill="x", pady=(0, 20))

        guarantees = [
            ("Free 24-Hour Diagnosis", "Bring your device in. We perform full electrical testing and give you a firm, written quote within 24 hours at zero charge."),
            ("No Fix, No Fee Guarantee", "If a logic board cannot be restored to full stable operation, you pay zero bench diagnostic fees."),
            ("90-Day Written Warranty", "All replaced components and bench craftsmanship are backed by a comprehensive 90-day parts and labor warranty."),
            ("Full Transparency", "We explain the exact root cause in plain English with photo proof of damaged and replaced parts.")
        ]

        for title, desc in guarantees:
            row = tk.Frame(commit_box, bg=BG_PANEL)
            row.pack(fill="x", pady=6)
            tk.Label(row, text="[PASS]", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL, width=8, anchor="w").pack(side="left")
            t_col = tk.Frame(row, bg=BG_PANEL)
            t_col.pack(side="left", fill="x", expand=True)
            tk.Label(t_col, text=title, font=FONT_BODY_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w")
            tk.Label(t_col, text=desc, font=FONT_BODY, fg=MUTED, bg=BG_PANEL).pack(anchor="w")

        # Facility and Location Info Card
        fac_card = tk.Frame(wrap, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        fac_card.pack(fill="x", pady=(0, 24))

        tk.Label(fac_card, text="Workshop Facility & Inquiries", font=FONT_HEADING, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))

        info_cols = tk.Frame(fac_card, bg=BG_PANEL)
        info_cols.pack(fill="x")

        c1 = tk.Frame(info_cols, bg=BG_PANEL)
        c1.pack(side="left", fill="both", expand=True)
        tk.Label(c1, text="Address", font=FONT_SMALL_BOLD, fg=DIM, bg=BG_PANEL).pack(anchor="w")
        tk.Label(c1, text="118 Beacon Works, Unit 3\nOld Mill District", font=FONT_BODY, fg=INK, bg=BG_PANEL, justify="left").pack(anchor="w", pady=(2, 8))
        tk.Label(c1, text="Direct Phone", font=FONT_SMALL_BOLD, fg=DIM, bg=BG_PANEL).pack(anchor="w")
        tk.Label(c1, text="(555) 019-3350", font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(2, 0))

        c2 = tk.Frame(info_cols, bg=BG_PANEL)
        c2.pack(side="left", fill="both", expand=True)
        tk.Label(c2, text="Operating Hours", font=FONT_SMALL_BOLD, fg=DIM, bg=BG_PANEL).pack(anchor="w")
        tk.Label(c2, text="Monday to Friday: 9:00 AM to 7:00 PM\nSaturday: 10:00 AM to 5:00 PM\nSunday: Bench closed", font=FONT_BODY, fg=INK, bg=BG_PANEL, justify="left").pack(anchor="w", pady=(2, 8))
        tk.Label(c2, text="Email Support", font=FONT_SMALL_BOLD, fg=DIM, bg=BG_PANEL).pack(anchor="w")
        tk.Label(c2, text="bench@fluxrepair.co", font=FONT_BODY, fg=EMERALD, bg=BG_PANEL).pack(anchor="w", pady=(2, 0))
