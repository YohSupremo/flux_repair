"""
FLUX Repair Co. — Modern Desktop Web-Style GUI (Tkinter)
Scrollable Landing Page with Centered Wrap & Modern Accordion Widget
Palette: Modern Cleanroom Light & Surgical Emerald
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import random

# ================= MODERN CLEANROOM LIGHT TOKENS =================
BG = "#f8fafc"           # Crisp titanium off-white canvas
BG_PANEL = "#ffffff"     # Pure white panel surface
BG_CARD = "#ffffff"      # Pure white card surface
BG_CARD_HOVER = "#f1f5f9"# Subtle slate hover
BG_INPUT = "#ffffff"     # Clean white input field
LINE = "#e2e8f0"         # Clean slate hairline
LINE_BRIGHT = "#cbd5e1"  # Elevated slate border
INK = "#0f172a"          # Deep obsidian slate text (WCAG AAA)
MUTED = "#475569"        # High-contrast slate body
DIM = "#64748b"          # Subtle slate metadata
AMBER = "#059669"        # Surgical Emerald primary accent
AMBER_HOVER = "#047857"  # Deep emerald hover
AMBER_DK = "#ecfdf5"     # Emerald mint tint for badges
GREEN = "#059669"        # Diagnostic pass emerald
RED = "#dc2626"          # Circuit fault red

# Complementary Dark Section Palette
DARK_BG = "#0f172a"          # Midnight obsidian for centerpiece social proof
DARK_CARD = "#1e293b"        # Elevated dark card slate
DARK_BORDER = "#334155"      # Dark slate hairline border
DARK_INK = "#f8fafc"         # Crisp light title on dark
DARK_MUTED = "#94a3b8"       # Secondary body text on dark
DARK_DIM = "#64748b"         # Subtle metadata on dark
DARK_EMERALD = "#34d399"     # Luminous surgical emerald accent on dark
DARK_EMERALD_BG = "#064e3b"  # Deep emerald badge background
DARK_FOOTER_BG = "#0b1120"   # Grounded midnight anchor footer

# Modern Web Sans-Serif Typography (Segoe UI)
FONT_BASE = ("Segoe UI", 10)
FONT_LEDE = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_EYEBROW = ("Segoe UI", 9, "bold")
FONT_HERO = ("Segoe UI", 34, "bold")
FONT_H2 = ("Segoe UI", 18, "bold")
FONT_H3 = ("Segoe UI", 12, "bold")
FONT_NAV = ("Segoe UI", 10)
FONT_BTN = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SM = ("Segoe UI", 9)
FONT_MONO_BOLD = ("Segoe UI", 10, "bold")

# ================= SERVICES DATA =================
SERVICES_DATA = [
    {
        "id": "01",
        "title": "Screens & Displays",
        "sub": "OLED, mini-LED, touch ICs and backlights",
        "turnaround": "Same Day",
        "price": "From $49",
        "desc": "Cracked glass, dead pixels, no-backlight or ghost-touch. We fit original-grade panels, calibrate color and True Tone, and preserve Face ID and fingerprint sensors wherever possible.",
        "badge": "Compatible Devices: iPhone, MacBook, Surface, Galaxy, iPad"
    },
    {
        "id": "02",
        "title": "Liquid Damage Recovery",
        "sub": "Ultrasonic bath, corrosion mapping, honest verdicts",
        "turnaround": "2–3 Days",
        "price": "From $89",
        "desc": "Full disassembly, ultrasonic board decontamination, and micro-inspection. Data first: we rescue your files before proceeding with board restoration.",
        "badge": "Coverage: Water, coffee, drink, and chemical ingress"
    },
    {
        "id": "03",
        "title": "Board-Level Micro-Soldering",
        "sub": "Precision component rework under high magnification",
        "turnaround": "2–5 Days",
        "price": "From $120",
        "desc": "No power, shorted rails, dead charging ICs, torn traces. We fix the specific component instead of charging for whole-motherboard replacement.",
        "badge": "Coverage: Logic boards, Apple Silicon, GPUs, and power rails"
    },
    {
        "id": "04",
        "title": "Batteries & Power Systems",
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
        "turnaround": "3–7 Days",
        "price": "From $150",
        "desc": "Dead phones, clicking drives, water-logged SSDs. In-house chip-off extraction, NAND reballing, and firmware rebuilds.",
        "badge": "Coverage: NAND flash, NVMe, SATA SSDs, and hard drives"
    },
    {
        "id": "06",
        "title": "Retro Audio & Consoles",
        "sub": "Capacitor recaps, mods, and hardware resurrections",
        "turnaround": "2–4 Days",
        "price": "From $60",
        "desc": "Capacitor recaps, blown HDMI retimers, region mods, and USB-C upgrades for vintage gaming hardware.",
        "badge": "Coverage: Game Boy, PlayStation, Nintendo, and retro audio"
    }
]

PROCESS_STEPS = [
    ("Step 01", "Free Diagnosis", "Walk in or ship your device. We open it up, identify the root fault, and hand you a firm written estimate within 24 hours."),
    ("Step 02", "Your Approval", "No work begins without your agreement. If teardown reveals more, we call first. If you decline, you pay nothing."),
    ("Step 03", "Precision Repair", "Micro-soldering under the microscope, ESD-safe workstation, and complete photo-documentation of every component replaced."),
    ("Step 04", "Testing & Return", "Every repair passes a 72-hour continuous bench stress test before return, backed by our 90-day comprehensive written warranty.")
]

WORK_ORDERS = [
    {
        "quote": "“Coffee spill, keyboard first. Another shop quoted a complete logic board replacement. Flux swapped two power chips and my files never left the machine.”",
        "name": "Marta K.",
        "device": "MacBook Pro 16″ (Liquid Damage)"
    },
    {
        "quote": "“Three shops said my phone was beyond repair. Flux asked about my photos first, then recovered every single photo and restored the phone.”",
        "name": "Deniz R.",
        "device": "iPhone 12 (No Power / Shorted Rail)"
    },
    {
        "quote": "“A twelve-year-old iMac now runs cooler and quieter than it did when new. Genuine component-level diagnostics that saved my workspace.”",
        "name": "Sam O.",
        "device": "iMac 2011 (Logic Board Recap)"
    },
    {
        "quote": "“Booked online at 9am, ready by 4pm. The final price was lower than quoted because the diagnosis was faster than expected.”",
        "name": "Priya N.",
        "device": "Galaxy S22 (Charging Port)"
    },
    {
        "quote": "“PlayStation with a blown HDMI port. Repaired cleanly in 48 hours without swapping the motherboard. Outstanding micro-soldering precision.”",
        "name": "Alex T.",
        "device": "PlayStation 5 (HDMI Retimer)"
    },
    {
        "quote": "“Liquid ingress on a ThinkPad SSD with unsaved research. Rescued 100% of the drive partitions without losing a single document.”",
        "name": "Dr. Elena V.",
        "device": "ThinkPad X1 (Data Recovery)"
    }
]


# ================= MODERN ACCORDION WIDGET =================
class AccordionItem:
    def __init__(self, parent, data, on_book_callback, toggle_callback):
        self.data = data
        self.is_open = False
        self.toggle_callback = toggle_callback
        self.on_book_callback = on_book_callback

        # Main Row Card (Clean modern website card: 1px hairline border, no bevels)
        self.card = tk.Frame(parent, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.card.pack(fill="x", pady=4)

        # Header Row (Clickable)
        self.head_frame = tk.Frame(self.card, bg=BG_PANEL, cursor="hand2", padx=20, pady=16)
        self.head_frame.pack(fill="x")

        self._bind_click(self.head_frame)

        # Number Index
        self.idx_lbl = tk.Label(self.head_frame, text=data["id"], font=FONT_BOLD, fg=AMBER, bg=BG_PANEL)
        self.idx_lbl.pack(side="left", padx=(0, 16))
        self._bind_click(self.idx_lbl)

        # Title + Subtitle
        title_box = tk.Frame(self.head_frame, bg=BG_PANEL)
        title_box.pack(side="left", fill="x", expand=True)
        self._bind_click(title_box)

        self.title_lbl = tk.Label(title_box, text=data["title"], font=FONT_H3, fg=INK, bg=BG_PANEL)
        self.title_lbl.pack(anchor="w")
        self._bind_click(self.title_lbl)

        self.sub_lbl = tk.Label(title_box, text=data["sub"], font=FONT_MONO_SM, fg=DIM, bg=BG_PANEL)
        self.sub_lbl.pack(anchor="w", pady=(2, 0))
        self._bind_click(self.sub_lbl)

        # Right Metadata: Turnaround & Price & Chevron
        meta_box = tk.Frame(self.head_frame, bg=BG_PANEL)
        meta_box.pack(side="right")
        self._bind_click(meta_box)

        self.turn_lbl = tk.Label(meta_box, text=f"Turnaround: {data['turnaround']}", font=FONT_BASE, fg=MUTED, bg=BG_PANEL)
        self.turn_lbl.pack(side="left", padx=16)
        self._bind_click(self.turn_lbl)

        self.price_lbl = tk.Label(meta_box, text=data["price"], font=FONT_BOLD, fg=AMBER, bg=BG_PANEL)
        self.price_lbl.pack(side="left", padx=12)
        self._bind_click(self.price_lbl)

        self.chev_lbl = tk.Label(meta_box, text="▼", font=FONT_BASE, fg=MUTED, bg=BG_PANEL, width=2)
        self.chev_lbl.pack(side="right", padx=(4, 0))
        self._bind_click(self.chev_lbl)

        # Collapsible Drawer Body (No heavy nested borders)
        self.body_frame = tk.Frame(self.card, bg="#f8fafc", padx=24, pady=18, bd=0, highlightthickness=0)

        self.desc_lbl = tk.Label(
            self.body_frame,
            text=data["desc"],
            font=FONT_BASE,
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
            font=FONT_MONO_SM,
            fg=AMBER,
            bg=AMBER_DK,
            padx=10,
            pady=4,
            bd=0,
            highlightthickness=1,
            highlightbackground="#a7f3d0"
        ).pack(side="left")

        self.book_btn = tk.Button(
            b_bot,
            text="Book This Repair →",
            font=FONT_BTN,
            bg=BG_PANEL,
            fg=AMBER,
            activebackground=AMBER,
            activeforeground="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground=AMBER,
            padx=16,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_book_callback(data["title"])
        )
        self.book_btn.pack(side="right")
        self.book_btn.bind("<Enter>", lambda e: self.book_btn.configure(bg=AMBER, fg="#ffffff"))
        self.book_btn.bind("<Leave>", lambda e: self.book_btn.configure(bg=BG_PANEL, fg=AMBER))

        # Keyboard accessibility
        self.card.bind("<Return>", lambda e: self.toggle_callback(self))
        self.card.bind("<space>", lambda e: self.toggle_callback(self))

    def _bind_click(self, widget):
        widget.bind("<Button-1>", lambda e: self.toggle_callback(self))
        widget.bind("<Enter>", lambda e: self._on_hover(True))
        widget.bind("<Leave>", lambda e: self._on_hover(False))

    def _on_hover(self, entering):
        if not self.is_open:
            self.card.configure(highlightbackground=AMBER if entering else LINE)
            self.title_lbl.configure(fg=AMBER if entering else INK)

    def expand(self):
        self.is_open = True
        self.card.configure(highlightbackground=AMBER, bg=BG_PANEL)
        self.head_frame.configure(bg=BG_PANEL)
        self.title_lbl.configure(fg=AMBER, bg=BG_PANEL)
        self.chev_lbl.configure(text="▲", fg=AMBER, bg=BG_PANEL)
        self.body_frame.pack(fill="x")

    def collapse(self):
        self.is_open = False
        self.card.configure(highlightbackground=LINE, bg=BG_PANEL)
        self.head_frame.configure(bg=BG_PANEL)
        self.title_lbl.configure(fg=INK, bg=BG_PANEL)
        self.chev_lbl.configure(text="▼", fg=MUTED, bg=BG_PANEL)
        self.body_frame.pack_forget()


# ================= MAIN LANDING PAGE =================
class CircuitCareLandingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FLUX Repair Co. — Dead is a diagnosis, not a verdict")

        # Responsive comfortable desktop window dimensions (prevents overflow on standard monitors)
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        app_w = min(1380, max(1240, scr_w - 40))
        app_h = min(780, max(600, scr_h - 70))
        pos_x = max(0, (scr_w - app_w) // 2)
        pos_y = max(0, (scr_h - app_h) // 2 - 20)
        self.geometry(f"{app_w}x{app_h}+{pos_x}+{pos_y}")
        self.minsize(1180, 560)
        self.configure(bg=BG)

        # State
        self.section_anchors = {}
        self.accordion_items = []

        # Scrolling Reviews Carousel State
        self.review_offset = 0.0
        self.review_paused = False
        self.review_card_width = 370
        self.review_card_padx = 8
        self.review_step_width = len(WORK_ORDERS) * (self.review_card_width + 2 * self.review_card_padx)

        # Configure Cleanroom ttk Theme for Scrollbar and Combobox
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure(
            "Vertical.TScrollbar",
            troughcolor=BG,
            background=LINE_BRIGHT,
            bordercolor=BG,
            arrowcolor=MUTED,
            relief="flat"
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[("active", AMBER), ("hover", MUTED)]
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            background=BG_CARD_HOVER,
            foreground=INK,
            selectbackground="#ffffff",
            selectforeground=INK,
            darkcolor=LINE,
            lightcolor=LINE,
            bordercolor=LINE_BRIGHT,
            arrowcolor=AMBER,
            insertcolor=AMBER,
            relief="flat",
            padding=6
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#ffffff"), ("focus", "#ffffff")],
            foreground=[("readonly", INK), ("focus", INK)],
            selectbackground=[("readonly", "#ffffff"), ("focus", "#ffffff"), ("!disabled", "#ffffff")],
            selectforeground=[("readonly", INK), ("focus", INK), ("!disabled", INK)],
            bordercolor=[("focus", AMBER)]
        )
        self.option_add("*TCombobox*Listbox.background", "#ffffff")
        self.option_add("*TCombobox*Listbox.foreground", INK)
        self.option_add("*TCombobox*Listbox.selectBackground", AMBER_DK)
        self.option_add("*TCombobox*Listbox.selectForeground", AMBER)
        self.option_add("*TCombobox*Listbox.font", FONT_BASE)
        self.option_add("*TCombobox*selectBackground", "#ffffff")
        self.option_add("*TCombobox*selectForeground", INK)
        self.option_add("*Combobox*selectBackground", "#ffffff")
        self.option_add("*Combobox*selectForeground", INK)

        self.section_inners = []

        self._build_fixed_header()
        self._build_scrollable_viewport()

        # Build Page Content
        self._build_hero_section()
        self._build_services_section()
        self._build_process_section()
        self._build_proof_section()
        self._build_visit_and_booking_section()
        self._build_footer_content()

        # Bindings & Timers
        self._bind_mousewheel()
        self._update_clock()
        self._animate_reviews_loop()

    # ---------------- FIXED TOP HEADER ----------------
    def _build_fixed_header(self):
        # Clean modern website navbar (1px bottom hairline divider)
        self.header = tk.Frame(self, bg=BG_PANEL, height=64, bd=0, highlightbackground=LINE, highlightthickness=1)
        self.header.pack(fill="x", side="top")

        hdr_wrap = tk.Frame(self.header, bg=BG_PANEL)
        hdr_wrap.pack(fill="x", padx=56, pady=12)
        self.hdr_wrap = hdr_wrap

        # Brand
        brand_box = tk.Frame(hdr_wrap, bg=BG_PANEL, cursor="hand2")
        brand_box.pack(side="left")
        brand_box.bind("<Button-1>", lambda e: self.scroll_to_section("hero"))

        icon_cv = tk.Canvas(brand_box, width=28, height=28, bg=BG_PANEL, highlightthickness=0)
        icon_cv.pack(side="left", padx=(0, 10))
        icon_cv.create_oval(3, 16, 12, 25, outline=AMBER, width=2)
        icon_cv.create_line(8, 16, 8, 9, 15, 9, 19, 5, 25, 5, fill=AMBER, width=2)
        icon_cv.create_oval(22, 3, 27, 8, fill=AMBER, outline=AMBER)
        icon_cv.bind("<Button-1>", lambda e: self.scroll_to_section("hero"))

        l_brand = tk.Label(brand_box, text="FLUX", font=("Segoe UI", 15, "bold"), fg=INK, bg=BG_PANEL)
        l_brand.pack(side="left")
        l_brand.bind("<Button-1>", lambda e: self.scroll_to_section("hero"))

        l_sub = tk.Label(brand_box, text=" REPAIR CO.", font=("Segoe UI", 8, "bold"), fg=AMBER, bg=BG_PANEL)
        l_sub.pack(side="left", pady=(5, 0))
        l_sub.bind("<Button-1>", lambda e: self.scroll_to_section("hero"))

        # Nav Links (Title Case website links)
        nav_box = tk.Frame(hdr_wrap, bg=BG_PANEL)
        nav_box.pack(side="right")

        for title, key in [
            ("Services", "services"),
            ("How It Works", "process"),
            ("Reviews", "proof"),
            ("Location & Hours", "visit"),
        ]:
            b = tk.Button(
                nav_box,
                text=title,
                font=FONT_NAV,
                fg=MUTED,
                bg=BG_PANEL,
                activeforeground=AMBER,
                activebackground=BG_PANEL,
                bd=0,
                padx=12,
                cursor="hand2",
                command=lambda k=key: self.scroll_to_section(k)
            )
            b.pack(side="left")
            b.bind("<Enter>", lambda e, btn=b: btn.configure(fg=AMBER))
            b.bind("<Leave>", lambda e, btn=b: btn.configure(fg=MUTED))

        # Opening Hours Status Chip (Clean pill)
        self.open_chip_lbl = tk.Label(
            nav_box,
            text="Checking workshop hours...",
            font=FONT_MONO_SM,
            fg=AMBER,
            bg=AMBER_DK,
            padx=12,
            pady=5,
            bd=0,
            highlightthickness=1,
            highlightbackground="#a7f3d0"
        )
        self.open_chip_lbl.pack(side="left", padx=(8, 14))

        # Primary Header CTA
        self.btn_hdr_book = tk.Button(
            nav_box,
            text="Book a Repair",
            font=FONT_BTN,
            bg=AMBER,
            fg="#ffffff",
            activebackground=AMBER_HOVER,
            activeforeground="#ffffff",
            bd=0,
            padx=18,
            pady=7,
            cursor="hand2",
            command=lambda: self.scroll_to_section("visit")
        )
        self.btn_hdr_book.pack(side="left")
        self.btn_hdr_book.bind("<Enter>", lambda e: self.btn_hdr_book.configure(bg=AMBER_HOVER))
        self.btn_hdr_book.bind("<Leave>", lambda e: self.btn_hdr_book.configure(bg=AMBER))

    # ---------------- SCROLLABLE VIEWPORT & CENTERED WRAP ----------------
    def _build_scrollable_viewport(self):
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

        # Centered Inner Wrap (.wrap { max-width: 1160px; margin: 0 auto; })
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
        # Expand self.content to full canvas width so section backgrounds stretch edge-to-edge
        self.canvas.itemconfig(self.window_id, width=canvas_width)
        self.canvas.coords(self.window_id, 0, 0)

        # Calculate symmetric horizontal padding for inner section containers (max-width 1040px)
        margin = max(48, (canvas_width - 1040) // 2)
        if hasattr(self, "hdr_wrap"):
            self.hdr_wrap.pack_configure(padx=margin)
        for inner in self.section_inners:
            try:
                inner.pack_configure(padx=margin)
            except Exception:
                pass

    def _bind_mousewheel(self):
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.bind_all("<MouseWheel>", _on_mousewheel)

    def scroll_to_section(self, key):
        self.update_idletasks()
        if key in self.section_anchors:
            widget = self.section_anchors[key]
            y = widget.winfo_y()
            total_h = self.content.winfo_height()
            if total_h > 0:
                self.canvas.yview_moveto(max(0.0, min(1.0, y / total_h)))

    # ---------------- SECTION 1: MINIMALIST WEBSITE HERO ----------------
    def _build_hero_section(self):
        sec = tk.Frame(self.content, bg="#ffffff", pady=56)
        sec.pack(fill="x")
        self.section_anchors["hero"] = sec

        inner = tk.Frame(sec, bg="#ffffff")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        hero_box = tk.Frame(inner, bg="#ffffff")
        hero_box.pack(anchor="center")

        # Eyebrow Tag
        tk.Label(
            hero_box,
            text="INDEPENDENT ELECTRONICS ATELIER",
            font=FONT_EYEBROW,
            fg=AMBER,
            bg=AMBER_DK,
            padx=12,
            pady=4
        ).pack(anchor="center", pady=(0, 20))

        # Headline
        h1 = tk.Frame(hero_box, bg="#ffffff")
        h1.pack(anchor="center")
        tk.Label(h1, text="Dead is a diagnosis. ", font=("Segoe UI", 36, "bold"), fg=INK, bg="#ffffff").pack(side="left")
        tk.Label(h1, text="Not a verdict.", font=("Segoe UI", 36, "bold"), fg=AMBER, bg="#ffffff").pack(side="left")

        # Concise Subhead (One short crisp sentence)
        tk.Label(
            hero_box,
            text="Expert component-level repair and data recovery for phones, laptops, and logic boards.\nFree diagnosis within 24 hours — zero fee if unfixable.",
            font=FONT_LEDE,
            fg=MUTED,
            bg="#ffffff",
            justify="center"
        ).pack(anchor="center", pady=(18, 28))

        # CTA Buttons Row
        cta_row = tk.Frame(hero_box, bg="#ffffff")
        cta_row.pack(anchor="center", pady=(0, 24))

        self.btn_hero_book = tk.Button(
            cta_row,
            text="Book a Repair →",
            font=FONT_BTN,
            bg=AMBER,
            fg="#ffffff",
            activebackground=AMBER_HOVER,
            activeforeground="#ffffff",
            bd=0,
            padx=26,
            pady=12,
            cursor="hand2",
            command=lambda: self.scroll_to_section("visit")
        )
        self.btn_hero_book.pack(side="left", padx=8)
        self.btn_hero_book.bind("<Enter>", lambda e: self.btn_hero_book.configure(bg=AMBER_HOVER))
        self.btn_hero_book.bind("<Leave>", lambda e: self.btn_hero_book.configure(bg=AMBER))

        self.btn_hero_prices = tk.Button(
            cta_row,
            text="View Services & Pricing",
            font=FONT_BTN,
            bg=BG_CARD_HOVER,
            fg=INK,
            activebackground=BG_CARD_HOVER,
            activeforeground=AMBER,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE_BRIGHT,
            padx=22,
            pady=12,
            cursor="hand2",
            command=lambda: self.scroll_to_section("services")
        )
        self.btn_hero_prices.pack(side="left", padx=8)
        self.btn_hero_prices.bind("<Enter>", lambda e: self.btn_hero_prices.configure(bg="#ffffff", fg=AMBER, highlightbackground=AMBER))
        self.btn_hero_prices.bind("<Leave>", lambda e: self.btn_hero_prices.configure(bg=BG_CARD_HOVER, fg=INK, highlightbackground=LINE_BRIGHT))

        # Reassurance strip (Clean, quiet, single line)
        tk.Label(
            hero_box,
            text="Free 24h Diagnosis   •   No Fix, No Fee   •   90-Day Warranty   •   Walk-ins Welcome",
            font=FONT_BASE,
            fg=DIM,
            bg="#ffffff"
        ).pack(anchor="center")

    # ---------------- SECTION 2: WHAT WE FIX (MODERN ACCORDION) ----------------
    def _build_services_section(self):
        sec = tk.Frame(self.content, bg="#f8fafc", pady=48)
        sec.pack(fill="x")
        self.section_anchors["services"] = sec

        inner = tk.Frame(sec, bg="#f8fafc")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        # Open section header (No enclosing border box)
        head = tk.Frame(inner, bg="#f8fafc")
        head.pack(fill="x", pady=(0, 20))
        tk.Label(head, text="What We Repair", font=FONT_H2, fg=INK, bg="#f8fafc").pack(side="left")
        tk.Label(head, text="Upfront flat quotes before work begins — No fix, no fee", font=FONT_BASE, fg=DIM, bg="#f8fafc").pack(side="right")

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
            if s.get("default_open"):
                item.expand()

    def _toggle_accordion_item(self, clicked_item):
        if clicked_item.is_open:
            clicked_item.collapse()
        else:
            for item in self.accordion_items:
                if item != clicked_item and item.is_open:
                    item.collapse()
            clicked_item.expand()

    def _prefill_booking(self, svc_title):
        self.book_svc_var.set(svc_title)
        self.scroll_to_section("visit")
        if hasattr(self, "book_cb"):
            self.book_cb.selection_clear()
        messagebox.showinfo("Service Selected", f"Booking pre-selected for: {svc_title}")

    # ---------------- SECTION 3: PROCESS ----------------
    def _build_process_section(self):
        sec = tk.Frame(self.content, bg="#ffffff", pady=48)
        sec.pack(fill="x")
        self.section_anchors["process"] = sec

        inner = tk.Frame(sec, bg="#ffffff")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        # Open section header (No enclosing border box)
        head = tk.Frame(inner, bg="#ffffff")
        head.pack(fill="x", pady=(0, 20))
        tk.Label(head, text="How It Works", font=FONT_H2, fg=INK, bg="#ffffff").pack(side="left")
        tk.Label(head, text="Transparent approvals at every step — Zero surprise fees", font=FONT_BASE, fg=DIM, bg="#ffffff").pack(side="right")

        steps_row = tk.Frame(inner, bg="#ffffff")
        steps_row.pack(fill="x")

        for tag, title, desc in PROCESS_STEPS:
            sc = tk.Frame(steps_row, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=20)
            sc.pack(side="left", fill="both", expand=True, padx=6)

            tk.Label(sc, text=tag, font=FONT_BOLD, fg=AMBER, bg="#f8fafc").pack(anchor="w")
            tk.Label(sc, text=title, font=FONT_H3, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(6, 10))
            tk.Label(sc, text=desc, font=FONT_BASE, fg=MUTED, bg="#f8fafc", wraplength=210, justify="left").pack(anchor="w")

    # ---------------- SECTION 4: PROOF & SCROLLING REVIEWS (DARK SHOWCASE) ----------------
    def _build_proof_section(self):
        sec = tk.Frame(self.content, bg=DARK_BG, pady=54)
        sec.pack(fill="x")
        self.section_anchors["proof"] = sec

        inner = tk.Frame(sec, bg=DARK_BG)
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        # Open section header
        head = tk.Frame(inner, bg=DARK_BG)
        head.pack(fill="x", pady=(0, 22))
        tk.Label(head, text="Client Reviews & Bench Metrics", font=FONT_H2, fg=DARK_INK, bg=DARK_BG).pack(side="left")
        tk.Label(head, text="Rated 4.9 / 5.0 across 1,100+ repairs   •   Hover to pause", font=FONT_BASE, fg=DARK_MUTED, bg=DARK_BG).pack(side="right")

        # Top Stat Strip
        grid = tk.Frame(inner, bg=DARK_BG)
        grid.pack(fill="x", pady=(0, 22))

        big_stat = tk.Frame(grid, bg=DARK_CARD, bd=0, highlightthickness=1, highlightbackground=DARK_BORDER, padx=24, pady=20)
        big_stat.pack(side="left", fill="both", expand=True, padx=(0, 14))
        tk.Label(big_stat, text="12,406", font=("Segoe UI", 36, "bold"), fg=DARK_EMERALD, bg=DARK_CARD).pack(anchor="w")
        tk.Label(big_stat, text="Devices Restored Since 2014", font=FONT_H3, fg=DARK_INK, bg=DARK_CARD).pack(anchor="w", pady=(2, 2))
        tk.Label(big_stat, text="Verified bench logs across smartphones, laptops, and complex logic boards.", font=FONT_BASE, fg=DARK_MUTED, bg=DARK_CARD).pack(anchor="w")

        side_stats = tk.Frame(grid, bg=DARK_BG)
        side_stats.pack(side="right", fill="both", expand=True)

        for b, sub in [
            ("90 Days", "Comprehensive warranty covering parts and labor"),
            ("48 Hours", "Median turnaround time for standard repairs"),
            ("94%", "Rescue rate on boards declared unfixable elsewhere")
        ]:
            card = tk.Frame(side_stats, bg=DARK_CARD, bd=0, highlightthickness=1, highlightbackground=DARK_BORDER, padx=18, pady=10)
            card.pack(fill="x", pady=2)
            tk.Label(card, text=b, font=FONT_H3, fg=DARK_EMERALD, bg=DARK_CARD, width=10, anchor="w").pack(side="left")
            tk.Label(card, text=sub, font=FONT_BASE, fg=DARK_MUTED, bg=DARK_CARD).pack(side="left")

        # Horizontal Infinite Scrolling Marquee Canvas
        marquee_wrap = tk.Frame(inner, bg=DARK_BG)
        marquee_wrap.pack(fill="x", pady=(8, 16))

        self.reviews_canvas = tk.Canvas(marquee_wrap, height=185, bg=DARK_BG, highlightthickness=0)
        self.reviews_canvas.pack(fill="x")

        self.reviews_track = tk.Frame(self.reviews_canvas, bg=DARK_BG)
        self.reviews_win = self.reviews_canvas.create_window((0, 0), window=self.reviews_track, anchor="nw")

        # Duplicate reviews list 3x to ensure wide seamless loop across all screen resolutions
        loop_items = WORK_ORDERS * 3

        for item in loop_items:
            rcard = tk.Frame(
                self.reviews_track,
                bg=DARK_CARD,
                bd=0,
                highlightthickness=1,
                highlightbackground=DARK_BORDER,
                width=self.review_card_width,
                height=170,
                padx=20,
                pady=16
            )
            rcard.pack(side="left", padx=self.review_card_padx, pady=4)
            rcard.pack_propagate(False)

            # Top Row: Stars + Verified Badge
            r_top = tk.Frame(rcard, bg=DARK_CARD)
            r_top.pack(fill="x", pady=(0, 10))

            tk.Label(r_top, text="★★★★★", font=("Segoe UI", 11), fg=DARK_EMERALD, bg=DARK_CARD).pack(side="left")

            v_pill = tk.Label(
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
            )
            v_pill.pack(side="right")

            # Quote Body
            q_lbl = tk.Label(
                rcard,
                text=item["quote"],
                font=("Segoe UI", 10, "italic"),
                fg="#f1f5f9",
                bg=DARK_CARD,
                wraplength=325,
                justify="left"
            )
            q_lbl.pack(anchor="w", fill="x", expand=True)

            # Bottom Row: Name + Device
            r_bot = tk.Frame(rcard, bg=DARK_CARD)
            r_bot.pack(fill="x", pady=(8, 0))

            a_lbl = tk.Label(r_bot, text=item["name"], font=FONT_BOLD, fg=DARK_INK, bg=DARK_CARD)
            a_lbl.pack(side="left")

            d_lbl = tk.Label(r_bot, text=item["device"], font=FONT_MONO_SM, fg=DARK_MUTED, bg=DARK_CARD)
            d_lbl.pack(side="right")

            # Recursive hover events: pause scrolling & highlight card on hover
            def _bind_hover(widget, c=rcard):
                widget.bind("<Enter>", lambda e: self._on_review_card_hover(c, True))
                widget.bind("<Leave>", lambda e: self._on_review_card_hover(c, False))

            for w in [rcard, r_top, q_lbl, r_bot, a_lbl, d_lbl, v_pill]:
                _bind_hover(w)

    def _on_review_card_hover(self, card, entering):
        self.review_paused = entering
        card.configure(highlightbackground=DARK_EMERALD if entering else DARK_BORDER)

    def _animate_reviews_loop(self):
        if not self.review_paused and hasattr(self, "reviews_canvas") and self.review_step_width > 0:
            self.review_offset += 1.0  # smooth 1px glide leftward
            if self.review_offset >= self.review_step_width:
                self.review_offset -= self.review_step_width
            self.reviews_canvas.coords(self.reviews_win, -int(self.review_offset), 0)
        self.after(25, self._animate_reviews_loop)

    # ---------------- SECTION 5: VISIT & BOOKING ----------------
    def _build_visit_and_booking_section(self):
        sec = tk.Frame(self.content, bg="#ffffff", pady=48)
        sec.pack(fill="x")
        self.section_anchors["visit"] = sec

        inner = tk.Frame(sec, bg="#ffffff")
        inner.pack(fill="x", padx=48)
        self.section_inners.append(inner)

        # Open section header (No enclosing border box)
        head = tk.Frame(inner, bg="#ffffff")
        head.pack(fill="x", pady=(0, 20))
        tk.Label(head, text="Workshop Location & Appointments", font=FONT_H2, fg=INK, bg="#ffffff").pack(side="left")

        grid = tk.Frame(inner, bg="#ffffff")
        grid.pack(fill="x")

        # Left Card: Workshop Details & Hours
        left = tk.Frame(grid, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=24)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))

        tk.Label(left, text="Visit Our Workshop", font=FONT_H3, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(0, 14))

        for label, value in [
            ("Address", "118 Beacon Works, Unit 3, Old Mill District"),
            ("Phone", "(555) 019-3350 (Direct Workshop Line)"),
            ("Email", "bench@fluxrepair.co (Photo Quotes Welcome)")
        ]:
            row = tk.Frame(left, bg="#f8fafc")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=FONT_BOLD, fg=AMBER, bg="#f8fafc", width=10, anchor="w").pack(side="left")
            tk.Label(row, text=value, font=FONT_BASE, fg=INK, bg="#f8fafc").pack(side="left")

        tk.Label(left, text="Opening Hours", font=FONT_BOLD, fg=AMBER, bg="#f8fafc").pack(anchor="w", pady=(18, 8))
        for d, h in [
            ("Monday – Friday", "9:00 AM – 7:00 PM"),
            ("Saturday", "10:00 AM – 5:00 PM"),
            ("Sunday", "Closed")
        ]:
            hr = tk.Frame(left, bg="#f8fafc")
            hr.pack(fill="x", pady=3)
            tk.Label(hr, text=d, font=FONT_BASE, fg=INK, bg="#f8fafc").pack(side="left")
            tk.Label(hr, text=h, font=FONT_BASE, fg=MUTED, bg="#f8fafc").pack(side="right")

        # Right Card: Modern Booking Form
        self.form_panel = tk.Frame(grid, bg="#f8fafc", bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=24)
        self.form_panel.pack(side="right", fill="both", expand=True)

        self._render_booking_form_fields()

    def _render_booking_form_fields(self):
        for child in self.form_panel.winfo_children():
            child.destroy()

        tk.Label(self.form_panel, text="Book a Free Diagnosis", font=FONT_H2, fg=AMBER, bg="#f8fafc").pack(anchor="w")
        tk.Label(self.form_panel, text="Describe your device and issue. We confirm within 4 business hours.", font=FONT_BASE, fg=MUTED, bg="#f8fafc").pack(anchor="w", pady=(2, 14))

        def f_input(parent, label_text):
            tk.Label(parent, text=label_text, font=FONT_BOLD, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(6, 2))
            e = tk.Entry(
                parent,
                bg="#ffffff",
                fg=INK,
                insertbackground=AMBER,
                font=FONT_BASE,
                bd=0,
                highlightthickness=1,
                highlightbackground=LINE_BRIGHT,
                highlightcolor=AMBER
            )
            e.pack(fill="x", ipady=6)
            e.bind("<Return>", lambda ev: self._handle_book_submit())
            return e

        self.book_name = f_input(self.form_panel, "Your Name")
        self.book_contact = f_input(self.form_panel, "Email or Phone Number")
        self.book_device = f_input(self.form_panel, "Device Model & Issue Description")

        tk.Label(self.form_panel, text="Service Category", font=FONT_BOLD, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(8, 2))
        self.book_svc_var = tk.StringVar(value="Board-Level Micro-Soldering")
        svc_opts = [s["title"] for s in SERVICES_DATA] + ["Not sure — diagnose it"]
        self.book_cb = ttk.Combobox(
            self.form_panel,
            textvariable=self.book_svc_var,
            values=svc_opts,
            state="readonly",
            font=FONT_BASE,
            exportselection=False
        )
        self.book_cb.pack(fill="x", ipady=4)
        self.book_cb.selection_clear()
        self.book_cb.bind("<<ComboboxSelected>>", lambda e: self.book_cb.after(10, self.book_cb.selection_clear))
        self.book_cb.bind("<FocusIn>", lambda e: self.book_cb.after(10, self.book_cb.selection_clear))
        self.book_cb.bind("<ButtonRelease-1>", lambda e: self.book_cb.after(10, self.book_cb.selection_clear))
        self.book_cb.bind("<Button-1>", lambda e: self.book_cb.after(20, self.book_cb.selection_clear))

        self.submit_btn = tk.Button(
            self.form_panel,
            text="Request Diagnosis Appointment",
            font=FONT_BTN,
            bg=AMBER,
            fg="#ffffff",
            activebackground=AMBER_HOVER,
            activeforeground="#ffffff",
            bd=0,
            pady=12,
            cursor="hand2",
            command=self._handle_book_submit
        )
        self.submit_btn.pack(fill="x", pady=(16, 6))
        self.submit_btn.bind("<Enter>", lambda e: self.submit_btn.configure(bg=AMBER_HOVER))
        self.submit_btn.bind("<Leave>", lambda e: self.submit_btn.configure(bg=AMBER))

        tk.Label(self.form_panel, text="No fix, no fee guarantee  |  Your data remains secure on device", font=FONT_MONO_SM, fg=DIM, bg="#f8fafc").pack(anchor="w")

    def _handle_book_submit(self):
        name = self.book_name.get().strip()
        contact = self.book_contact.get().strip()
        device = self.book_device.get().strip()

        if not name or not contact or not device:
            messagebox.showwarning("Incomplete Form", "Please fill in your Name, Contact, and Device fields.")
            return

        tk_id = f"#FL-{random.randint(4900, 4999)}"
        svc = self.book_svc_var.get()

        for child in self.form_panel.winfo_children():
            child.destroy()

        tk.Label(self.form_panel, text="Diagnosis Request Received", font=FONT_BOLD, fg=GREEN, bg="#f8fafc").pack(anchor="w", pady=(10, 4))
        tk.Label(self.form_panel, text=tk_id, font=("Segoe UI", 32, "bold"), fg=AMBER, bg="#f8fafc").pack(anchor="w")
        tk.Label(self.form_panel, text=f"{device} — {svc}", font=FONT_H3, fg=INK, bg="#f8fafc").pack(anchor="w", pady=(4, 12))
        tk.Label(self.form_panel, text="We will confirm your appointment slot within 4 business hours.\nPlease bring the power charger if available.", font=FONT_BASE, fg=MUTED, bg="#f8fafc", justify="left").pack(anchor="w", pady=(0, 20))

        btn = tk.Button(
            self.form_panel,
            text="Book Another Device",
            font=FONT_BTN,
            bg=BG_CARD_HOVER,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self._reset_booking_form
        )
        btn.pack(anchor="w")
        btn.bind("<Enter>", lambda e: btn.configure(bg="#ffffff", fg=AMBER, highlightbackground=AMBER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=BG_CARD_HOVER, fg=INK, highlightbackground=LINE))

    def _reset_booking_form(self):
        self._render_booking_form_fields()
        self.scroll_to_section("visit")

    # ---------------- UNIFIED BALANCED WEBSITE FOOTER (MATCHING HEADER) ----------------
    def _build_footer_content(self):
        foot_panel = tk.Frame(self.content, bg=BG_PANEL, bd=0, highlightthickness=0)
        foot_panel.pack(fill="x")

        foot_inner = tk.Frame(foot_panel, bg=BG_PANEL)
        foot_inner.pack(fill="x", padx=48, pady=(40, 28))
        self.section_inners.append(foot_inner)

        def _make_link(parent, label_text, target_section=None, info_dialog=None):
            lbl = tk.Label(parent, text=label_text, font=FONT_BASE, fg=MUTED, bg=BG_PANEL, cursor="hand2")
            lbl.pack(anchor="w", pady=3)
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg=AMBER))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(fg=MUTED))
            if target_section:
                lbl.bind("<Button-1>", lambda e, s=target_section: self.scroll_to_section(s))
            elif info_dialog:
                lbl.bind("<Button-1>", lambda e, d=info_dialog: messagebox.showinfo(d[0], d[1]))
            return lbl

        # Single Cohesive Row with 4 Balanced Columns (Flushed to left and right edges)
        cols_wrap = tk.Frame(foot_inner, bg=BG_PANEL)
        cols_wrap.pack(fill="x", pady=(0, 28))

        # Column 1: Brand & Atelier Overview (Left edge flushed with page content)
        col1 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 18))

        b_title = tk.Frame(col1, bg=BG_PANEL, cursor="hand2")
        b_title.pack(anchor="w", pady=(0, 8))
        b_title.bind("<Button-1>", lambda e: self.scroll_to_section("hero"))

        tk.Label(b_title, text="FLUX", font=("Segoe UI", 15, "bold"), fg=INK, bg=BG_PANEL).pack(side="left")
        tk.Label(b_title, text=" REPAIR CO.", font=("Segoe UI", 9, "bold"), fg=AMBER, bg=BG_PANEL).pack(side="left", pady=(3, 0))

        tk.Label(
            col1,
            text="Independent electronics repair atelier and cleanroom micro-soldering facility.",
            font=FONT_BASE,
            fg=MUTED,
            bg=BG_PANEL,
            wraplength=230,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(col1, text="118 Beacon Works, Unit 3", font=FONT_BASE, fg=DIM, bg=BG_PANEL).pack(anchor="w", pady=1)
        tk.Label(col1, text="Old Mill District", font=FONT_BASE, fg=DIM, bg=BG_PANEL).pack(anchor="w", pady=1)
        tk.Label(col1, text="Phone: (555) 019-3350", font=FONT_BASE, fg=AMBER, bg=BG_PANEL).pack(anchor="w", pady=(4, 1))
        tk.Label(col1, text="bench@fluxrepair.co", font=FONT_BASE, fg=AMBER, bg=BG_PANEL).pack(anchor="w", pady=1)

        # Column 2: Repair Services (Balanced middle column)
        col2 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col2.pack(side="left", fill="both", expand=True, padx=18)
        tk.Label(col2, text="SERVICES", font=FONT_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))
        _make_link(col2, "Screens & Displays", target_section="services")
        _make_link(col2, "Liquid Damage Recovery", target_section="services")
        _make_link(col2, "Board-Level Micro-Soldering", target_section="services")
        _make_link(col2, "Batteries & Power Systems", target_section="services")
        _make_link(col2, "Dedicated Data Recovery", target_section="services")
        _make_link(col2, "Retro Audio & Consoles", target_section="services")

        # Column 3: How It Works & Guarantees (Balanced middle column)
        col3 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col3.pack(side="left", fill="both", expand=True, padx=18)
        tk.Label(col3, text="OUR PROCESS", font=FONT_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))
        _make_link(col3, "Free 24-Hour Diagnosis", target_section="process")
        _make_link(col3, "Pre-Approval & Estimates", target_section="process")
        _make_link(col3, "Micro-Soldering Rework", target_section="process")
        _make_link(col3, "72-Hour Stress Bench Testing", target_section="process")
        _make_link(col3, "90-Day Written Warranty", target_section="process")
        _make_link(col3, "No Fix, No Fee Guarantee", target_section="process")

        # Column 4: Quick Links & Legal (Right edge flushed with page content)
        col4 = tk.Frame(cols_wrap, bg=BG_PANEL)
        col4.pack(side="left", fill="both", expand=True, padx=(18, 0))
        tk.Label(col4, text="VISIT & BOOKING", font=FONT_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 10))
        _make_link(col4, "Book an Appointment", target_section="visit")
        _make_link(col4, "Client Reviews & Ratings", target_section="proof")
        _make_link(col4, "Hours: Mon–Fri 9am–7pm", target_section="visit")
        _make_link(col4, "Saturday: 10am–5pm", target_section="visit")
        _make_link(col4, "Privacy Policy", info_dialog=("Privacy Policy", "Device diagnostics are conducted strictly for hardware fault resolution. User storage remains encrypted and is never extracted or accessed without explicit signed consent."))
        _make_link(col4, "Terms of Service", info_dialog=("Terms of Service", "Diagnostics are free within 24 hours. No work begins without explicit approval. All paid repairs include our 90-day parts and labor warranty."))
        _make_link(col4, "Back to Top ↑", target_section="hero")

        # Bottom Hairline Divider
        tk.Frame(foot_inner, bg=LINE, height=1).pack(fill="x", pady=(20, 20))

        # Bottom Legal Row (Symmetrically aligned to left and right edges)
        bottom_bar = tk.Frame(foot_inner, bg=BG_PANEL)
        bottom_bar.pack(fill="x")

        tk.Label(
            bottom_bar,
            text="© 2026 FLUX Repair Co. All rights reserved. Registered Electronics Atelier #BEAC-118.",
            font=FONT_MONO_SM,
            fg=DIM,
            bg=BG_PANEL
        ).pack(side="left")

        tk.Label(
            bottom_bar,
            text="Free 24h Diagnosis   •   No Fix, No Fee   •   90-Day Warranty",
            font=FONT_MONO_SM,
            fg=DIM,
            bg=BG_PANEL
        ).pack(side="right")

    # ---------------- TIMERS ----------------
    def _update_clock(self):
        now = datetime.datetime.now()
        day = now.weekday()
        hour = now.hour + now.minute / 60.0
        is_open = False
        closing = "7:00 PM"
        if day < 5:
            if 9.0 <= hour < 19.0:
                is_open = True
                closing = "7:00 PM"
        elif day == 5:
            if 10.0 <= hour < 17.0:
                is_open = True
                closing = "5:00 PM"

        if is_open:
            self.open_chip_lbl.configure(text=f"Open Today (Closes {closing})", fg=GREEN, bg=AMBER_DK)
        else:
            self.open_chip_lbl.configure(text="Closed (Opens 9:00 AM)", fg=DIM, bg=LINE)

        self.after(60000, self._update_clock)


if __name__ == "__main__":
    app = CircuitCareLandingApp()
    app.mainloop()
