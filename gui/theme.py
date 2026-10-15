from tkinter import ttk

# ================= DESIGN SYSTEM TOKENS =================
BG = "#f8fafc"              # Crisp titanium off-white canvas
BG_PANEL = "#ffffff"        # Pure white panel surface
BG_CARD = "#ffffff"         # Pure white card surface
BG_HOVER = "#f1f5f9"        # Subtle slate hover
BG_INPUT = "#ffffff"        # Clean white input field
LINE = "#e2e8f0"            # Clean slate hairline
LINE_BRIGHT = "#cbd5e1"     # Elevated slate border
INK = "#0f172a"             # Deep obsidian slate text (WCAG AAA)
MUTED = "#475569"           # High-contrast slate body
DIM = "#64748b"             # Subtle slate metadata

# Accent Colors
EMERALD = "#059669"         # Surgical Emerald primary accent
EMERALD_HOVER = "#047857"   # Deep emerald hover
EMERALD_LIGHT = "#ecfdf5"   # Mint tint for badges / active items
EMERALD_BORDER = "#a7f3d0"  # Soft mint border

RED = "#dc2626"             # Circuit fault alert red
RED_LIGHT = "#fef2f2"       # Red badge background
RED_BORDER = "#fecaca"

AMBER = "#d97706"           # Warning / Diagnosing amber
AMBER_LIGHT = "#fffbeb"
AMBER_BORDER = "#fde68a"

BLUE = "#2563eb"            # Info / Under repair blue
BLUE_LIGHT = "#eff6ff"
BLUE_BORDER = "#bfdbfe"

PURPLE = "#7c3aed"          # Waiting for parts purple
PURPLE_LIGHT = "#f5f3ff"
PURPLE_BORDER = "#ddd6fe"

# Sidebar Dark Palette
SIDEBAR_BG = "#0f172a"      # Midnight obsidian slate
SIDEBAR_HOVER = "#1e293b"   # Elevated dark card slate
SIDEBAR_ACTIVE = "#059669"  # Luminous surgical emerald accent
SIDEBAR_INK = "#f8fafc"     # Crisp white label
SIDEBAR_MUTED = "#94a3b8"   # Secondary label

# Typography (Segoe UI + Consolas)
FONT_FAMILY = "Segoe UI"
FONT_MONO_FAMILY = "Consolas"

FONT_DISPLAY = (FONT_FAMILY, 18, "bold")
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_HEADING = (FONT_FAMILY, 11, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
FONT_MONO = (FONT_MONO_FAMILY, 10)
FONT_MONO_BOLD = (FONT_MONO_FAMILY, 10, "bold")
FONT_MONO_SM = (FONT_MONO_FAMILY, 9)


def apply_theme(root):
    """Configure modern ttk styles across the entire application."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Treeview (Modern flat cleanroom table)
    style.configure(
        "Treeview",
        background=BG_PANEL,
        foreground=INK,
        fieldbackground=BG_PANEL,
        font=FONT_BODY,
        rowheight=34,
        borderwidth=0,
        highlightthickness=0
    )
    style.map(
        "Treeview",
        background=[("selected", EMERALD_LIGHT)],
        foreground=[("selected", EMERALD)]
    )

    style.configure(
        "Treeview.Heading",
        background=BG_HOVER,
        foreground=MUTED,
        font=FONT_SMALL_BOLD,
        borderwidth=0,
        relief="flat",
        padding=(10, 8)
    )
    style.map(
        "Treeview.Heading",
        background=[("active", LINE)]
    )

    # Scrollbars (Thin modern scrollbar)
    style.configure(
        "Vertical.TScrollbar",
        background=LINE,
        troughcolor=BG_PANEL,
        bordercolor=BG_PANEL,
        arrowcolor=MUTED,
        relief="flat",
        width=10
    )

    # Combobox
    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_HOVER,
        foreground=INK,
        arrowcolor=MUTED,
        padding=6,
        font=FONT_BODY
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        selectbackground=[("readonly", EMERALD_LIGHT)],
        selectforeground=[("readonly", EMERALD)]
    )
