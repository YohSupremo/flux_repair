import tkinter as tk
from tkinter import ttk, messagebox
import random
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_SM
)

# Dark section tokens for proof marquee
DARK_BG = "#0f172a"
DARK_CARD = "#1e293b"
DARK_BORDER = "#334155"
DARK_INK = "#f8fafc"
DARK_MUTED = "#94a3b8"
DARK_EMERALD = "#34d399"
DARK_EMERALD_BG = "#064e3b"

SERVICES_DATA = [
    {
        "id": "01",
        "title": "Screens and Displays",
        "sub": "OLED, mini-LED, touch ICs and backlights",
        "turnaround": "Same Day",
        "price": "From $49",
        "desc": "Cracked glass, dead pixels, no backlight or ghost touch. We fit original-grade panels, calibrate color and True Tone, and preserve Face ID and biometric sensors wherever possible.",
        "badge": "Compatible: iPhone, MacBook, Surface, Galaxy, iPad"
    },
    {
        "id": "02",
        "title": "Liquid Damage Recovery",
        "sub": "Ultrasonic bath, corrosion mapping, honest verdicts",
        "turnaround": "2 to 3 Days",
        "price": "From $89",
        "desc": "Full disassembly, ultrasonic board decontamination, and micro-inspection. Data first: we rescue your files before proceeding with board restoration.",
        "badge": "Coverage: Water, coffee, beverage, and chemical ingress"
    },
    {
        "id": "03",
        "title": "Board-Level Micro-Soldering",
        "sub": "Precision component rework under high magnification",
        "turnaround": "2 to 5 Days",
        "price": "From $120",
        "desc": "No power, shorted rails, dead charging ICs, torn traces. We fix the specific component instead of charging for whole-motherboard replacement.",
        "badge": "Coverage: Logic boards, Apple Silicon, GPUs, and power rails"
    },
    {
        "id": "04",
        "title": "Batteries and Power Systems",
        "sub": "High-capacity cells with health verification",
        "turnaround": "Same Day",
        "price": "From $39",
        "desc": "Swollen packs, sudden shutdown, worn charging ports. We fit genuine-specification cells and verify power delivery under load.",
        "badge": "Coverage: Genuine specification cells for phones, laptops, and tablets"
    },
    {
        "id": "05",
        "title": "Dedicated Data Recovery",
        "sub": "Your valuable photos and files outrank the hardware",
        "turnaround": "3 to 7 Days",
        "price": "From $150",
        "desc": "Dead phones, clicking drives, water-logged SSDs. In-house chip-off extraction, NAND reballing, and firmware rebuilds.",
        "badge": "Coverage: NAND flash, NVMe, SATA SSDs, and hard drives"
    },
    {
        "id": "06",
        "title": "Retro Audio and Consoles",
        "sub": "Capacitor recaps, mods, and hardware resurrections",
        "turnaround": "2 to 4 Days",
        "price": "From $60",
        "desc": "Capacitor recaps, blown HDMI retimers, region mods, and USB-C upgrades for vintage gaming hardware.",
        "badge": "Coverage: Game Boy, PlayStation, Nintendo, and retro audio"
    }
]

PROCESS_STEPS = [
    ("Step 01", "Free Diagnosis", "Walk in or submit your device online. We open it up, identify the root fault, and give you a firm written estimate within 24 hours."),
    ("Step 02", "Your Approval", "No work begins without your agreement. If teardown reveals more, we call first. If you decline, you pay nothing."),
    ("Step 03", "Precision Repair", "Micro-soldering under the microscope, ESD-safe workstation, and complete documentation of every component replaced."),
    ("Step 04", "Testing and Return", "Every repair passes a 72-hour continuous bench stress test before return, backed by our 90-day comprehensive written warranty.")
]

WORK_ORDERS = [
    {
        "quote": "\"Coffee spill, keyboard first. Another shop quoted a complete logic board replacement. Flux swapped two power chips and my files never left the machine.\"",
        "name": "Marta K.",
        "device": "MacBook Pro 16 (Liquid Damage)"
    },
    {
        "quote": "\"Three shops said my phone was beyond repair. Flux asked about my photos first, then recovered every single photo and restored the phone.\"",
        "name": "Deniz R.",
        "device": "iPhone 12 (No Power / Shorted Rail)"
    },
    {
        "quote": "\"A twelve-year-old iMac now runs cooler and quieter than it did when new. Genuine component-level diagnostics that saved my workspace.\"",
        "name": "Sam O.",
        "device": "iMac 2011 (Logic Board Recap)"
    },
    {
        "quote": "\"Booked online at 9am, ready by 4pm. The final price was lower than quoted because the diagnosis was faster than expected.\"",
        "name": "Priya N.",
        "device": "Galaxy S22 (Charging Port)"
    },
    {
        "quote": "\"PlayStation with a blown HDMI port. Repaired cleanly in 48 hours without swapping the motherboard. Outstanding micro-soldering precision.\"",
        "name": "Alex T.",
        "device": "PlayStation 5 (HDMI Retimer)"
    },
    {
        "quote": "\"Liquid ingress on a ThinkPad SSD with unsaved research. Rescued 100% of the drive partitions without losing a single document.\"",
        "name": "Dr. Elena V.",
        "device": "ThinkPad X1 (Data Recovery)"
    }
]


class AccordionItem:
    def __init__(self, parent, data, on_book_callback, toggle_callback):
        self.data = data
        self.is_open = False
        self.toggle_callback = toggle_callback
        self.on_book_callback = on_book_callback

        self.card = tk.Frame(parent, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.card.pack(fill="x", pady=4)

        self.head_frame = tk.Frame(self.card, bg=BG_PANEL, cursor="hand2", padx=20, pady=16)
        self.head_frame.pack(fill="x")
        self._bind_click(self.head_frame)

        self.idx_lbl = tk.Label(self.head_frame, text=data["id"], font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_PANEL)
        self.idx_lbl.pack(side="left", padx=(0, 16))
        self._bind_click(self.idx_lbl)

        title_box = tk.Frame(self.head_frame, bg=BG_PANEL)
        title_box.pack(side="left", fill="x", expand=True)
        self._bind_click(title_box)

        self.title_lbl = tk.Label(title_box, text=data["title"], font=FONT_HEADING, fg=INK, bg=BG_PANEL)
        self.title_lbl.pack(anchor="w")
        self._bind_click(self.title_lbl)

        self.sub_lbl = tk.Label(title_box, text=data["sub"], font=FONT_SMALL, fg=DIM, bg=BG_PANEL)
        self.sub_lbl.pack(anchor="w", pady=(2, 0))
        self._bind_click(self.sub_lbl)

        meta_box = tk.Frame(self.head_frame, bg=BG_PANEL)
        meta_box.pack(side="right")
        self._bind_click(meta_box)

        self.turn_lbl = tk.Label(meta_box, text=f"Turnaround: {data['turnaround']}", font=FONT_BODY, fg=MUTED, bg=BG_PANEL)
        self.turn_lbl.pack(side="left", padx=16)
        self._bind_click(self.turn_lbl)

        self.price_lbl = tk.Label(meta_box, text=data["price"], font=FONT_BODY_BOLD, fg=EMERALD, bg=BG_PANEL)
        self.price_lbl.pack(side="left", padx=12)
        self._bind_click(self.price_lbl)

        self.chev_lbl = tk.Label(meta_box, text="v", font=FONT_BODY, fg=MUTED, bg=BG_PANEL, width=2)
        self.chev_lbl.pack(side="right", padx=(4, 0))
        self._bind_click(self.chev_lbl)

        # Drawer Body
        self.body_frame = tk.Frame(self.card, bg="#f8fafc", padx=24, pady=18, bd=0, highlightthickness=0)

        self.desc_lbl = tk.Label(
            self.body_frame,
            text=data["desc"],
            font=FONT_BODY,
            fg=INK,
            bg="#f8fafc",
            wraplength=880,
            justify="left"
        )
        self.desc_lbl.pack(anchor="w", pady=(0, 14))

        b_bot = tk.Frame(self.body_frame, bg="#f8fafc")
        b_bot.pack(fill="x")

        tk.Label(
            b_bot,
            text=data["badge"],
            font=FONT_SMALL,
            fg=EMERALD,
            bg=EMERALD_LIGHT,
            padx=10,
            pady=4,
            bd=0,
            highlightthickness=1,
            highlightbackground="#a7f3d0"
        ).pack(side="left")

        self.book_btn = tk.Button(
            b_bot,
            text="Book This Repair ->",
            font=FONT_SMALL_BOLD,
            bg=BG_PANEL,
            fg=EMERALD,
            activebackground=EMERALD,
            activeforeground="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground=EMERALD,
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_book_callback(data["title"])
        )
        self.book_btn.pack(side="right")
        self.book_btn.bind("<Enter>", lambda e: self.book_btn.configure(bg=EMERALD, fg="#ffffff"))
        self.book_btn.bind("<Leave>", lambda e: self.book_btn.configure(bg=BG_PANEL, fg=EMERALD))

    def _bind_click(self, widget):
        widget.bind("<Button-1>", lambda e: self.toggle_callback(self))
        widget.bind("<Enter>", lambda e: self._on_hover(True))
        widget.bind("<Leave>", lambda e: self._on_hover(False))

    def _on_hover(self, entering):
        if not self.is_open:
            self.card.configure(highlightbackground=EMERALD if entering else LINE)
            self.title_lbl.configure(fg=EMERALD if entering else INK)

    def expand(self):
        self.is_open = True
        self.card.configure(highlightbackground=EMERALD, bg=BG_PANEL)
        self.head_frame.configure(bg=BG_PANEL)
        self.title_lbl.configure(fg=EMERALD, bg=BG_PANEL)
        self.chev_lbl.configure(text="^", fg=EMERALD, bg=BG_PANEL)
        self.body_frame.pack(fill="x")

    def collapse(self):
        self.is_open = False
        self.card.configure(highlightbackground=LINE, bg=BG_PANEL)
        self.head_frame.configure(bg=BG_PANEL)
        self.title_lbl.configure(fg=INK, bg=BG_PANEL)
        self.chev_lbl.configure(text="v", fg=MUTED, bg=BG_PANEL)
        self.body_frame.pack_forget()


class LandingPageView(tk.Frame):
    """
    Direct Website Landing Page View embedded directly in the Tab shell.
    Features modern website layout, scrollable sections, hero CTA, interactive
    service drawers, proof telemetry marquee, and appointment booking.
    """
    def __init__(self, parent, current_user=None, on_open_intake_callback=None, on_navigate_callback=None):
        super().__init__(parent, bg=BG)
        self.current_user = current_user
        self.on_open_intake_callback = on_open_intake_callback
        self.on_navigate_callback = on_navigate_callback

        self.section_anchors = {}
        self.accordion_items = []
        self.section_inners = []

        self.review_offset = 0.0
        self.review_paused = False
        self.review_card_width = 370
        self.review_card_padx = 8
        self.review_step_width = len(WORK_ORDERS) * (self.review_card_width + 2 * self.review_card_padx)

        self._anim_job = None

        self._build_scrollable_viewport()

        # Build Website Sections
        self._build_hero_section()
        self._build_services_section()
        self._build_process_section()
        self._build_proof_section()
        self._build_visit_and_booking_section()
        self._build_footer_content()

        # Bindings and marquee start
        self._bind_mousewheel()
        self._animate_reviews_loop()

    def destroy(self):
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception:
            pass
        if self._anim_job:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        super().destroy()

    # ---------------- SCROLLABLE VIEWPORT ----------------
    def _build_scrollable_viewport(self):
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

        self.content = tk.Frame(self.canvas, bg=BG)
        self.content.bind("<Configure>", self._on_content_configure)

        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _on_content_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        canvas_height = event.height
        self.canvas.itemconfig(self.window_id, width=canvas_width)
        self.canvas.coords(self.window_id, 0, 0)

        # Make hero section occupy the full visible viewport frame (min 540px)
        if hasattr(self, "hero_sec") and canvas_height > 300:
            target_h = max(540, canvas_height)
            self.hero_sec.configure(height=target_h)
            self.hero_sec.pack_propagate(False)

        margin = max(36, (canvas_width - 1060) // 2)
        for inner in self.section_inners:
            try:
                inner.pack_configure(padx=margin)
            except Exception:
                pass

    def _bind_mousewheel(self):
        def _on_mousewheel(event):
            if not self.winfo_exists():
                return
            try:
                # Scroll if this landing page view is currently visible on screen
                if self.winfo_ismapped() and hasattr(self, "canvas") and self.canvas.winfo_exists():
                    delta = event.delta
                    step = int(-1 * (delta / 120))
                    self.canvas.yview_scroll(step, "units")
            except Exception:
                pass

        # bind_all ensures mouse wheel scrolling works anywhere over text, cards, buttons or whitespace
        self.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units") if (self.winfo_exists() and self.winfo_ismapped()) else None)
        self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units") if (self.winfo_exists() and self.winfo_ismapped()) else None)

    def scroll_to_section(self, key):
        self.update_idletasks()
        if key in self.section_anchors:
            widget = self.section_anchors[key]
            y = widget.winfo_y()
            total_h = self.content.winfo_height()
            if total_h > 0:
                self.canvas.yview_moveto(max(0.0, min(1.0, y / total_h)))

    def _handle_cta_book(self):
        if self.on_open_intake_callback:
            self.on_open_intake_callback()
        else:
            self.scroll_to_section("visit")

    # ---------------- SECTION 1: FULL-FRAME HERO ----------------
    def _build_hero_section(self):
        self.hero_sec = tk.Frame(self.content, bg="#ffffff", height=580)
        self.hero_sec.pack(fill="x")
        self.hero_sec.pack_propagate(False)
        self.section_anchors["hero"] = self.hero_sec

        self.hero_inner = tk.Frame(self.hero_sec, bg="#ffffff")
        self.hero_inner.pack(fill="both", expand=True)
        self.section_inners.append(self.hero_inner)

        hero_box = tk.Frame(self.hero_inner, bg="#ffffff")
        hero_box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            hero_box,
            text="INDEPENDENT ELECTRONICS ATELIER",
            font=("Segoe UI", 10, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT,
            padx=16,
            pady=5
        ).pack(anchor="center", pady=(0, 20))

        h1 = tk.Frame(hero_box, bg="#ffffff")
        h1.pack(anchor="center")
        tk.Label(h1, text="Dead is a diagnosis. ", font=("Segoe UI", 40, "bold"), fg=INK, bg="#ffffff").pack(side="left")
        tk.Label(h1, text="Not a verdict.", font=("Segoe UI", 40, "bold"), fg=EMERALD, bg="#ffffff").pack(side="left")

        tk.Label(
            hero_box,
            text="Expert component-level repair and data recovery for phones, laptops, and logic boards.\nFree diagnosis within 24 hours. Zero fee if unfixable.",
            font=("Segoe UI", 13),
            fg=MUTED,
            bg="#ffffff",
            justify="center"
        ).pack(anchor="center", pady=(18, 28))

        cta_row = tk.Frame(hero_box, bg="#ffffff")
        cta_row.pack(anchor="center", pady=(0, 24))

        btn_book = tk.Button(
            cta_row,
            text="Book a Repair ->",
            font=("Segoe UI", 11, "bold"),
            bg=EMERALD,
            fg="#ffffff",
            activebackground=EMERALD_HOVER,
            activeforeground="#ffffff",
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self._handle_cta_book
        )
        btn_book.pack(side="left", padx=10)
        btn_book.bind("<Enter>", lambda e: btn_book.configure(bg=EMERALD_HOVER))
        btn_book.bind("<Leave>", lambda e: btn_book.configure(bg=EMERALD))

        btn_prices = tk.Button(
            cta_row,
            text="View Services and Pricing",
            font=("Segoe UI", 11, "bold"),
            bg=BG_HOVER,
            fg=INK,
            activebackground=BG_PANEL,
            activeforeground=EMERALD,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE_BRIGHT,
            padx=26,
            pady=12,
            cursor="hand2",
            command=lambda: self.scroll_to_section("services")
        )
        btn_prices.pack(side="left", padx=10)
        btn_prices.bind("<Enter>", lambda e: btn_prices.configure(bg="#ffffff", fg=EMERALD, highlightbackground=EMERALD))
        btn_prices.bind("<Leave>", lambda e: btn_prices.configure(bg=BG_HOVER, fg=INK, highlightbackground=LINE_BRIGHT))

        trust_row = tk.Frame(hero_box, bg="#ffffff")
        trust_row.pack(anchor="center", pady=(0, 18))
        for item in ["Free 24h Diagnosis", "No Fix, No Fee", "90-Day Warranty", "Walk-ins Welcome"]:
            chip = tk.Frame(trust_row, bg=BG_HOVER, padx=12, pady=5, highlightthickness=1, highlightbackground=LINE)
            chip.pack(side="left", padx=4)
            tk.Label(chip, text=item, font=("Segoe UI", 9, "bold"), fg=MUTED, bg=BG_HOVER).pack()

        scroll_hint = tk.Label(
            hero_box,
            text="Explore Repair Services  v",
            font=("Segoe UI", 9, "bold"),
            fg=MUTED,
            bg="#ffffff",
            cursor="hand2"
        )
        scroll_hint.pack(anchor="center", pady=(4, 0))
        scroll_hint.bind("<Button-1>", lambda e: self.scroll_to_section("services"))
        scroll_hint.bind("<Enter>", lambda e: scroll_hint.configure(fg=EMERALD))
        scroll_hint.bind("<Leave>", lambda e: scroll_hint.configure(fg=MUTED))

    # ---------------- SECTION 2: SERVICES ACCORDION ----------------
    def _build_services_section(self):
        sec = tk.Frame(self.content, bg="#f8fafc", pady=44)
        sec.pack(fill="x")
        self.section_anchors["services"] = sec

        inner = tk.Frame(sec, bg="#f8fafc")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        head = tk.Frame(inner, bg="#f8fafc")
        head.pack(fill="x", pady=(0, 16))
        tk.Label(head, text="What We Repair", font=FONT_TITLE, fg=INK, bg="#f8fafc").pack(side="left")
        tk.Label(head, text="Upfront flat estimates before work begins. No fix, no fee.", font=FONT_BODY, fg=DIM, bg="#f8fafc").pack(side="right")

        acc_container = tk.Frame(inner, bg="#f8fafc")
        acc_container.pack(fill="x")

        self.accordion_items = []
        for s in SERVICES_DATA:
            item = AccordionItem(
                acc_container,
                s,
                on_book_callback=self._prefill_booking,
                toggle_callback=self._toggle_accordion_item
            )
            self.accordion_items.append(item)

        if self.accordion_items:
            self.accordion_items[0].expand()

    def _toggle_accordion_item(self, clicked_item):
        if clicked_item.is_open:
            clicked_item.collapse()
        else:
            for item in self.accordion_items:
                if item != clicked_item and item.is_open:
                    item.collapse()
            clicked_item.expand()

    def _expand_service_by_title(self, title):
        norm = str(title).lower().strip()
        for item in self.accordion_items:
            t = str(item.data.get("title", "")).lower().strip()
            if norm in t or t in norm:
                item.expand()
            else:
                item.collapse()

    def _prefill_booking(self, svc_title):
        if hasattr(self, "book_svc_var"):
            self.book_svc_var.set(svc_title)
        self.scroll_to_section("visit")
        if self.on_open_intake_callback:
            self.on_open_intake_callback()

    # ---------------- SECTION 3: PROCESS ----------------
    def _build_process_section(self):
        sec = tk.Frame(self.content, bg="#ffffff", pady=44)
        sec.pack(fill="x")
        self.section_anchors["process"] = sec

        inner = tk.Frame(sec, bg="#ffffff")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        head = tk.Frame(inner, bg="#ffffff")
        head.pack(fill="x", pady=(0, 16))
        tk.Label(head, text="How It Works", font=FONT_TITLE, fg=INK, bg="#ffffff").pack(side="left")
        tk.Label(head, text="Transparent approvals at every step. Zero surprise fees.", font=FONT_BODY, fg=DIM, bg="#ffffff").pack(side="right")

        steps_row = tk.Frame(inner, bg="#ffffff")
        steps_row.pack(fill="x")

        for tag, title, desc in PROCESS_STEPS:
            sc = tk.Frame(steps_row, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=18, pady=18)
            sc.pack(side="left", fill="both", expand=True, padx=6)

            tk.Label(sc, text=tag, font=FONT_SMALL_BOLD, fg=EMERALD, bg="#f8fafc").pack(anchor="w")
            tk.Label(sc, text=title, font=FONT_HEADING, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(4, 8))
            tk.Label(sc, text=desc, font=FONT_BODY, fg=MUTED, bg="#f8fafc", wraplength=210, justify="left").pack(anchor="w")

    # ---------------- SECTION 4: PROOF & REVIEWS ----------------
    def _build_proof_section(self):
        sec = tk.Frame(self.content, bg=DARK_BG, pady=48)
        sec.pack(fill="x")
        self.section_anchors["proof"] = sec

        inner = tk.Frame(sec, bg=DARK_BG)
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        head = tk.Frame(inner, bg=DARK_BG)
        head.pack(fill="x", pady=(0, 18))
        tk.Label(head, text="Client Reviews and Bench Metrics", font=FONT_TITLE, fg=DARK_INK, bg=DARK_BG).pack(side="left")
        tk.Label(head, text="Rated 4.9 / 5.0 across 1,100+ repairs. Hover card to pause.", font=FONT_BODY, fg=DARK_MUTED, bg=DARK_BG).pack(side="right")

        grid = tk.Frame(inner, bg=DARK_BG)
        grid.pack(fill="x", pady=(0, 18))

        big_stat = tk.Frame(grid, bg=DARK_CARD, bd=0, highlightthickness=1, highlightbackground=DARK_BORDER, padx=22, pady=18)
        big_stat.pack(side="left", fill="both", expand=True, padx=(0, 12))
        tk.Label(big_stat, text="12,406", font=("Segoe UI", 32, "bold"), fg=DARK_EMERALD, bg=DARK_CARD).pack(anchor="w")
        tk.Label(big_stat, text="Devices Restored Since 2014", font=FONT_HEADING, fg=DARK_INK, bg=DARK_CARD).pack(anchor="w", pady=(2, 2))
        tk.Label(big_stat, text="Verified bench logs across smartphones, laptops, and complex logic boards.", font=FONT_BODY, fg=DARK_MUTED, bg=DARK_CARD).pack(anchor="w")

        side_stats = tk.Frame(grid, bg=DARK_BG)
        side_stats.pack(side="right", fill="both", expand=True)

        for b, sub in [
            ("90 Days", "Comprehensive warranty covering parts and labor"),
            ("48 Hours", "Median turnaround time for standard repairs"),
            ("94%", "Rescue rate on boards declared unfixable elsewhere")
        ]:
            card = tk.Frame(side_stats, bg=DARK_CARD, bd=0, highlightthickness=1, highlightbackground=DARK_BORDER, padx=16, pady=8)
            card.pack(fill="x", pady=2)
            tk.Label(card, text=b, font=FONT_HEADING, fg=DARK_EMERALD, bg=DARK_CARD, width=10, anchor="w").pack(side="left")
            tk.Label(card, text=sub, font=FONT_BODY, fg=DARK_MUTED, bg=DARK_CARD).pack(side="left")

        # Marquee
        marquee_wrap = tk.Frame(inner, bg=DARK_BG)
        marquee_wrap.pack(fill="x", pady=(6, 12))

        self.reviews_canvas = tk.Canvas(marquee_wrap, height=170, bg=DARK_BG, highlightthickness=0)
        self.reviews_canvas.pack(fill="x")

        self.reviews_track = tk.Frame(self.reviews_canvas, bg=DARK_BG)
        self.reviews_win = self.reviews_canvas.create_window((0, 0), window=self.reviews_track, anchor="nw")

        loop_items = WORK_ORDERS * 3
        for item in loop_items:
            rcard = tk.Frame(
                self.reviews_track,
                bg=DARK_CARD,
                bd=0,
                highlightthickness=1,
                highlightbackground=DARK_BORDER,
                width=self.review_card_width,
                height=155,
                padx=18,
                pady=14
            )
            rcard.pack(side="left", padx=self.review_card_padx, pady=4)
            rcard.pack_propagate(False)

            r_top = tk.Frame(rcard, bg=DARK_CARD)
            r_top.pack(fill="x", pady=(0, 8))

            tk.Label(r_top, text="[5 Stars]", font=FONT_SMALL_BOLD, fg=DARK_EMERALD, bg=DARK_CARD).pack(side="left")
            tk.Label(
                r_top,
                text="Verified Client",
                font=FONT_MONO_SM,
                fg=DARK_EMERALD,
                bg=DARK_EMERALD_BG,
                padx=8,
                pady=2,
                bd=0,
                highlightthickness=1,
                highlightbackground="#059669"
            ).pack(side="right")

            q_lbl = tk.Label(
                rcard,
                text=item["quote"],
                font=("Segoe UI", 9, "italic"),
                fg="#f1f5f9",
                bg=DARK_CARD,
                wraplength=325,
                justify="left"
            )
            q_lbl.pack(anchor="w", fill="x", expand=True)

            r_bot = tk.Frame(rcard, bg=DARK_CARD)
            r_bot.pack(fill="x", pady=(6, 0))

            tk.Label(r_bot, text=item["name"], font=FONT_BODY_BOLD, fg=DARK_INK, bg=DARK_CARD).pack(side="left")
            tk.Label(r_bot, text=item["device"], font=FONT_SMALL, fg=DARK_MUTED, bg=DARK_CARD).pack(side="right")

            def _bind_hover(widget, c=rcard):
                widget.bind("<Enter>", lambda e: self._on_review_card_hover(c, True))
                widget.bind("<Leave>", lambda e: self._on_review_card_hover(c, False))

            for w in [rcard, r_top, q_lbl, r_bot]:
                _bind_hover(w)

    def _on_review_card_hover(self, card, entering):
        self.review_paused = entering
        card.configure(highlightbackground=DARK_EMERALD if entering else DARK_BORDER)

    def _animate_reviews_loop(self):
        if not self.winfo_exists():
            return
        if not self.review_paused and hasattr(self, "reviews_canvas") and self.review_step_width > 0:
            self.review_offset += 1.0
            if self.review_offset >= self.review_step_width:
                self.review_offset -= self.review_step_width
            try:
                self.reviews_canvas.coords(self.reviews_win, -int(self.review_offset), 0)
            except Exception:
                pass
        self._anim_job = self.after(25, self._animate_reviews_loop)

    # ---------------- SECTION 5: VISIT & BOOKING ----------------
    def _build_visit_and_booking_section(self):
        sec = tk.Frame(self.content, bg="#ffffff", pady=44)
        sec.pack(fill="x")
        self.section_anchors["visit"] = sec

        inner = tk.Frame(sec, bg="#ffffff")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        head = tk.Frame(inner, bg="#ffffff")
        head.pack(fill="x", pady=(0, 18))
        tk.Label(head, text="Workshop Location and Appointments", font=FONT_TITLE, fg=INK, bg="#ffffff").pack(side="left")

        grid = tk.Frame(inner, bg="#ffffff")
        grid.pack(fill="x")

        # Left Card: Hours and Info
        left = tk.Frame(grid, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=20)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(left, text="Visit Our Workshop", font=FONT_HEADING, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(0, 12))

        for label, value in [
            ("Address", "118 Beacon Works, Unit 3, Old Mill District"),
            ("Phone", "(555) 019-3350 (Direct Workshop Line)"),
            ("Email", "bench@fluxrepair.co (Photo Quotes Welcome)")
        ]:
            tk.Label(left, text=label, font=FONT_SMALL_BOLD, fg=DIM, bg="#f8fafc").pack(anchor="w")
            tk.Label(left, text=value, font=FONT_BODY, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(2, 8))

        tk.Label(left, text="Atelier Operating Hours", font=FONT_SMALL_BOLD, fg=DIM, bg="#f8fafc").pack(anchor="w", pady=(4, 4))
        for d, h in [
            ("Monday to Friday", "9:00 AM to 7:00 PM"),
            ("Saturday", "10:00 AM to 5:00 PM"),
            ("Sunday", "Bench closed for deep ultrasonic cycles")
        ]:
            r = tk.Frame(left, bg="#f8fafc")
            r.pack(fill="x", pady=2)
            tk.Label(r, text=d, font=FONT_BODY, fg=MUTED, bg="#f8fafc").pack(side="left")
            tk.Label(r, text=h, font=FONT_BODY_BOLD, fg=INK, bg="#f8fafc").pack(side="right")

        # Right Card: Booking Form
        self.form_panel = tk.Frame(grid, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=20)
        self.form_panel.pack(side="right", fill="both", expand=True)

        self._render_booking_form_fields()

    def _render_booking_form_fields(self):
        for child in self.form_panel.winfo_children():
            child.destroy()

        tk.Label(self.form_panel, text="Request a Free Diagnostic Slot", font=FONT_HEADING, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(0, 2))
        tk.Label(self.form_panel, text="Direct online slot request. Confirmed within 4 business hours.", font=FONT_SMALL, fg=MUTED, bg="#f8fafc").pack(anchor="w", pady=(0, 10))

        def f_input(parent, label_text, prefill=""):
            tk.Label(parent, text=label_text, font=FONT_SMALL_BOLD, fg=MUTED, bg="#f8fafc").pack(anchor="w", pady=(4, 2))
            e = tk.Entry(
                parent,
                font=FONT_BODY,
                bg=BG_INPUT,
                fg=INK,
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE_BRIGHT,
                highlightcolor=EMERALD
            )
            e.pack(fill="x", ipady=4)
            if prefill:
                e.insert(0, prefill)
            return e

        user_name = self.current_user['full_name'] if self.current_user else ""
        self.book_name = f_input(self.form_panel, "Your Full Name *", user_name)
        self.book_contact = f_input(self.form_panel, "Email or Contact Number *")
        self.book_device = f_input(self.form_panel, "Device Model and Issue Description *")

        tk.Label(self.form_panel, text="Select Primary Service Category", font=FONT_SMALL_BOLD, fg=MUTED, bg="#f8fafc").pack(anchor="w", pady=(6, 2))
        self.book_svc_var = tk.StringVar(value="Board-Level Micro-Soldering")
        svc_opts = [s["title"] for s in SERVICES_DATA] + ["Not sure: diagnose at workshop"]
        self.book_cb = ttk.Combobox(
            self.form_panel,
            textvariable=self.book_svc_var,
            values=svc_opts,
            state="readonly",
            font=FONT_BODY
        )
        self.book_cb.pack(fill="x", ipady=3)

        btn_submit = tk.Button(
            self.form_panel,
            text="Submit Diagnostic Booking ->",
            font=FONT_BODY_BOLD,
            bg=EMERALD,
            fg="#ffffff",
            activebackground=EMERALD_HOVER,
            activeforeground="#ffffff",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self._handle_book_submit
        )
        btn_submit.pack(fill="x", pady=(14, 6))
        btn_submit.bind("<Enter>", lambda e: btn_submit.configure(bg=EMERALD_HOVER))
        btn_submit.bind("<Leave>", lambda e: btn_submit.configure(bg=EMERALD))

        tk.Label(self.form_panel, text="No fix, no fee guarantee. Safe local data preservation.", font=FONT_SMALL, fg=DIM, bg="#f8fafc").pack(anchor="w")

    def _handle_book_submit(self):
        name = self.book_name.get().strip()
        contact = self.book_contact.get().strip()
        device = self.book_device.get().strip()

        if not name or not contact or not device:
            messagebox.showwarning("Notice", "Please fill in Name, Contact, and Device fields.")
            return

        tk_id = f"#FL-{random.randint(4900, 4999)}"
        svc = self.book_svc_var.get()

        for child in self.form_panel.winfo_children():
            child.destroy()

        tk.Label(self.form_panel, text="Diagnosis Request Confirmed", font=FONT_HEADING, fg=EMERALD, bg="#f8fafc").pack(anchor="w", pady=(8, 2))
        tk.Label(self.form_panel, text=tk_id, font=("Segoe UI", 24, "bold"), fg=EMERALD, bg="#f8fafc").pack(anchor="w")
        tk.Label(self.form_panel, text=f"{device} : {svc}", font=FONT_BODY_BOLD, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(2, 8))
        tk.Label(self.form_panel, text="We will confirm your appointment slot within 4 business hours.\nPlease bring the power charger if available.", font=FONT_BODY, fg=MUTED, bg="#f8fafc", justify="left").pack(anchor="w", pady=(0, 16))

        btn = tk.Button(
            self.form_panel,
            text="Book Another Device",
            font=FONT_SMALL_BOLD,
            bg=BG_HOVER,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._reset_booking_form
        )
        btn.pack(anchor="w")

    def _reset_booking_form(self):
        self._render_booking_form_fields()
        self.scroll_to_section("visit")

    # ---------------- SECTION 6: FOOTER ----------------
    def _build_footer_content(self):
        foot_panel = tk.Frame(self.content, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)
        foot_panel.pack(fill="x")

        foot_inner = tk.Frame(foot_panel, bg=BG_PANEL)
        foot_inner.pack(fill="x", padx=48, pady=(32, 24))
        self.section_inners.append(foot_inner)

        def _make_link(parent, label_text, target_tab=None, target_section=None, accordion_title=None, command=None):
            lbl = tk.Label(parent, text=label_text, font=FONT_BODY, fg=MUTED, bg=BG_PANEL, cursor="hand2")
            lbl.pack(anchor="w", pady=2)
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg=EMERALD))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(fg=MUTED))

            def _on_click(e):
                if command:
                    command()
                    return
                # 1. Primary redirect: if on_navigate_callback is set and target_tab is provided
                if target_tab and getattr(self, "on_navigate_callback", None):
                    self.on_navigate_callback(target_tab)
                    return
                # 2. Accordion expansion if specified
                if accordion_title:
                    self.scroll_to_section("services")
                    self._expand_service_by_title(accordion_title)
                    return
                # 3. Fallback to section scrolling
                if target_section and target_section in self.section_anchors:
                    self.scroll_to_section(target_section)
                elif target_tab and getattr(self, "on_navigate_callback", None):
                    self.on_navigate_callback(target_tab)

            lbl.bind("<Button-1>", _on_click)
            return lbl

        cols_wrap = tk.Frame(foot_inner, bg=BG_PANEL)
        cols_wrap.pack(fill="x", pady=(0, 20))

        # Col 1: Brand & Contact
        col1 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 16))

        b_title = tk.Frame(col1, bg=BG_PANEL, cursor="hand2")
        b_title.pack(anchor="w", pady=(0, 6))
        b_title.bind("<Button-1>", lambda e: self.on_navigate_callback("dashboard") if getattr(self, "on_navigate_callback", None) else self.scroll_to_section("hero"))

        tk.Label(b_title, text="FLUX", font=("Segoe UI", 14, "bold"), fg=INK, bg=BG_PANEL).pack(side="left")
        tk.Label(b_title, text=" REPAIR CO.", font=("Segoe UI", 9, "bold"), fg=EMERALD, bg=BG_PANEL).pack(side="left", pady=(2, 0))

        tk.Label(
            col1,
            text="Independent electronics repair atelier and cleanroom micro-soldering facility.",
            font=FONT_BODY,
            fg=MUTED,
            bg=BG_PANEL,
            wraplength=220,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))

        addr_lbl = tk.Label(col1, text="118 Beacon Works, Unit 3, Old Mill District", font=FONT_SMALL, fg=DIM, bg=BG_PANEL, cursor="hand2")
        addr_lbl.pack(anchor="w", pady=1)
        addr_lbl.bind("<Enter>", lambda e: addr_lbl.configure(fg=EMERALD))
        addr_lbl.bind("<Leave>", lambda e: addr_lbl.configure(fg=DIM))
        addr_lbl.bind("<Button-1>", lambda e: self.on_navigate_callback("about") if getattr(self, "on_navigate_callback", None) else self.scroll_to_section("visit"))

        phone_lbl = tk.Label(col1, text="Phone: (555) 019-3350", font=FONT_SMALL, fg=EMERALD, bg=BG_PANEL, cursor="hand2")
        phone_lbl.pack(anchor="w", pady=1)
        phone_lbl.bind("<Button-1>", lambda e: self.on_navigate_callback("about") if getattr(self, "on_navigate_callback", None) else self.scroll_to_section("visit"))

        # Col 2: Services (Routes directly to Services card catalog tab)
        col2 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col2.pack(side="left", fill="both", expand=True, padx=16)
        tk.Label(col2, text="SERVICES", font=FONT_SMALL_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))
        _make_link(col2, "Screens and Displays", target_tab="services", target_section="services")
        _make_link(col2, "Liquid Damage Recovery", target_tab="services", target_section="services")
        _make_link(col2, "Board-Level Micro-Soldering", target_tab="services", target_section="services")
        _make_link(col2, "Batteries and Power Systems", target_tab="services", target_section="services")
        _make_link(col2, "Dedicated Data Recovery", target_tab="services", target_section="services")

        # Col 3: Process (Routes directly to FAQ & Warranty tab)
        col3 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col3.pack(side="left", fill="both", expand=True, padx=(16, 0))
        tk.Label(col3, text="PROCESS", font=FONT_SMALL_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 8))
        _make_link(col3, "Free 24-Hour Diagnosis", target_tab="faq", target_section="process")
        _make_link(col3, "Pre-Approval and Estimates", target_tab="faq", target_section="process")
        _make_link(col3, "Micro-Soldering Rework", target_tab="faq", target_section="process")
        _make_link(col3, "72-Hour Quality Stress Test", target_tab="faq", target_section="process")
        _make_link(col3, "90-Day Written Warranty", target_tab="faq", target_section="process")

        # Bottom copyright
        tk.Frame(foot_inner, bg=LINE, height=1).pack(fill="x", pady=(10, 10))
        bot_bar = tk.Frame(foot_inner, bg=BG_PANEL)
        bot_bar.pack(fill="x")
        tk.Label(bot_bar, text="FLUX Repair Co.  Precision Diagnostics and Component Restoration", font=FONT_SMALL, fg=DIM, bg=BG_PANEL).pack(side="left")
        tk.Label(bot_bar, text="Dead is a diagnosis, not a verdict", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL).pack(side="right")
