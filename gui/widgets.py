import tkinter as tk
from tkinter import ttk, messagebox
from errors import ValidationError, RuleError, StorageError
from gui.theme import (
    BG, BG_PANEL, BG_CARD, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT,
    INK, MUTED, DIM, EMERALD, EMERALD_HOVER, EMERALD_LIGHT, EMERALD_BORDER,
    RED, RED_LIGHT, RED_BORDER, AMBER, AMBER_LIGHT, AMBER_BORDER,
    BLUE, BLUE_LIGHT, BLUE_BORDER, PURPLE, PURPLE_LIGHT, PURPLE_BORDER,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO, FONT_MONO_BOLD, FONT_MONO_SM
)


def guard(fn):
    """
    Decorator for GUI handlers that intercepts exceptions and displays
    native Tkinter dialogs instead of printing to terminal (FR-52, FR-56).
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (ValidationError, RuleError) as e:
            messagebox.showwarning("Notice", str(e))
        except StorageError as e:
            messagebox.showerror("Storage / File Error", str(e))
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred:\n{e}")
    return wrapper


def confirm(title, message):
    """Wrap messagebox.askyesno for destructive confirmations (FR-53)."""
    return messagebox.askyesno(title, message)


def make_card(parent, bg=BG_PANEL, bd_color=LINE, padx=16, pady=16):
    """Create a cleanroom card container with 1px hairline border."""
    card = tk.Frame(parent, bg=bg, bd=0, highlightthickness=1, highlightbackground=bd_color)
    inner = tk.Frame(card, bg=bg, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    return card, inner


def primary_button(parent, text, command, padx=16, pady=7):
    """Create primary surgical emerald button with tactile hover."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=EMERALD,
        fg="#ffffff",
        activebackground=EMERALD_HOVER,
        activeforeground="#ffffff",
        font=FONT_BODY_BOLD,
        bd=0,
        highlightthickness=1,
        highlightbackground="#047857",
        relief="flat",
        cursor="hand2",
        padx=padx,
        pady=pady
    )
    btn.bind("<Enter>", lambda e: btn.configure(bg=EMERALD_HOVER) if btn.cget('state') != 'disabled' else None)
    btn.bind("<Leave>", lambda e: btn.configure(bg=EMERALD) if btn.cget('state') != 'disabled' else None)
    return btn


def secondary_button(parent, text, command, padx=14, pady=6):
    """Create distinct neutral tactile button with clear border and hover affordance."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg="#f1f5f9",
        fg=INK,
        activebackground="#e2e8f0",
        activeforeground=INK,
        font=FONT_BODY_BOLD,
        bd=0,
        highlightthickness=1,
        highlightbackground="#cbd5e1",
        relief="flat",
        cursor="hand2",
        padx=padx,
        pady=pady
    )
    btn.bind("<Enter>", lambda e: btn.configure(bg="#e2e8f0", highlightbackground="#94a3b8") if btn.cget('state') != 'disabled' else None)
    btn.bind("<Leave>", lambda e: btn.configure(bg="#f1f5f9", highlightbackground="#cbd5e1") if btn.cget('state') != 'disabled' else None)
    return btn


def danger_button(parent, text, command, padx=14, pady=6):
    """Create danger outline button with hover affordance."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=RED_LIGHT,
        fg=RED,
        activebackground=RED,
        activeforeground="#ffffff",
        font=FONT_BODY_BOLD,
        bd=0,
        highlightthickness=1,
        highlightbackground=RED_BORDER,
        relief="flat",
        cursor="hand2",
        padx=padx,
        pady=pady
    )
    btn.bind("<Enter>", lambda e: btn.configure(bg="#fee2e2", highlightbackground=RED) if btn.cget('state') != 'disabled' else None)
    btn.bind("<Leave>", lambda e: btn.configure(bg=RED_LIGHT, highlightbackground=RED_BORDER) if btn.cget('state') != 'disabled' else None)
    return btn


def status_badge(parent, status):
    """Create a colored status pill."""
    styles = {
        'Received': (BLUE, BLUE_LIGHT, BLUE_BORDER),
        'Diagnosing': (AMBER, AMBER_LIGHT, AMBER_BORDER),
        'Waiting for Parts': (PURPLE, PURPLE_LIGHT, PURPLE_BORDER),
        'Under Repair': (BLUE, BLUE_LIGHT, BLUE_BORDER),
        'Completed': (EMERALD, EMERALD_LIGHT, EMERALD_BORDER),
        'Released': (DIM, BG_HOVER, LINE),
        'Cancelled': (RED, RED_LIGHT, RED_BORDER),
    }
    fg, bg, bd = styles.get(status, (DIM, BG_HOVER, LINE))
    lbl = tk.Label(
        parent,
        text=status,
        font=FONT_SMALL_BOLD,
        fg=fg,
        bg=bg,
        bd=0,
        highlightthickness=1,
        highlightbackground=bd,
        padx=8,
        pady=3
    )
    return lbl


def make_table(parent, columns, headings, widths=None):
    """
    Create a modern flat Treeview table with vertical scrollbar (FR-59).
    Returns (container_frame, treeview).
    """
    frame = tk.Frame(parent, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)

    tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
        selectmode="browse",
        style="Treeview"
    )

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=vsb.set)

    for i, col in enumerate(columns):
        head = headings[i] if i < len(headings) else col
        w = widths[i] if (widths and i < len(widths)) else 100
        tree.heading(col, text=head, anchor="w")
        tree.column(col, width=w, minwidth=max(40, int(w * 0.7)), anchor="w")

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # Alternating row tag colors
    tree.tag_configure("even", background=BG_PANEL)
    tree.tag_configure("odd", background="#fcfdfd")

    return frame, tree


def fill_table(tree, rows, columns):
    """Fill Treeview rows with alternating row striping."""
    tree.delete(*tree.get_children())
    for idx, r in enumerate(rows):
        values = [r.get(c, "") for c in columns]
        tag = "even" if idx % 2 == 0 else "odd"
        tree.insert("", "end", iid=str(idx), values=values, tags=(tag,))


def labeled_field(parent, label_text, widget_class=tk.Entry, **widget_kwargs):
    """Create labeled field container with consistent vertical rhythm."""
    box = tk.Frame(parent, bg=BG_PANEL)
    lbl = tk.Label(box, text=label_text, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL)
    lbl.pack(anchor="w", pady=(0, 4))

    if widget_class == tk.Entry:
        w = tk.Entry(
            box,
            font=FONT_BODY,
            bg=BG_INPUT,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=EMERALD,
            **widget_kwargs
        )
    elif widget_class == ttk.Combobox:
        w = ttk.Combobox(box, state="readonly", font=FONT_BODY, **widget_kwargs)
    elif widget_class == tk.Text:
        w = tk.Text(
            box,
            font=FONT_BODY,
            bg=BG_INPUT,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            highlightcolor=EMERALD,
            **widget_kwargs
        )
    else:
        w = widget_class(box, **widget_kwargs)

    w.pack(fill="x", expand=True)
    return box, w
