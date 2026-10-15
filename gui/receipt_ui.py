import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_MONO
)
from gui.widgets import primary_button, secondary_button, guard


class ReceiptViewerModal(tk.Toplevel):
    """
    Monospace Receipt / Invoice Viewer Window (FR-19, FR-41).
    Displays formatted receipt with option to copy or save as .txt.
    """
    def __init__(self, parent, title_text, receipt_content, default_filename="receipt.txt"):
        super().__init__(parent)
        self.title(title_text)
        self.geometry("620x720")
        self.minsize(500, 600)
        self.configure(bg=BG)
        self.receipt_content = receipt_content
        self.default_filename = default_filename

        self.transient(parent)
        self.grab_set()

        self._build_ui(title_text)

    def _build_ui(self, title_text):
        # Header
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        tk.Label(top_bar, text=title_text, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(side="left")

        # Action Buttons in Header
        btn_box = tk.Frame(top_bar, bg=BG_PANEL)
        btn_box.pack(side="right")

        copy_btn = secondary_button(btn_box, "Copy Text", command=self._copy_to_clipboard)
        copy_btn.pack(side="left", padx=(0, 8))

        save_btn = primary_button(btn_box, "Save .TXT File", command=self._save_to_file)
        save_btn.pack(side="left")

        # Content area with scrollable monospace text
        content_frame = tk.Frame(self, bg=BG, padx=20, pady=16)
        content_frame.pack(fill="both", expand=True)

        card = tk.Frame(content_frame, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="both", expand=True)

        txt = tk.Text(
            card,
            font=FONT_MONO,
            bg=BG_PANEL,
            fg=INK,
            bd=0,
            padx=16,
            pady=16,
            wrap="none"
        )
        txt.insert("1.0", self.receipt_content)
        txt.configure(state="disabled")

        vsb = ttk.Scrollbar(card, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)

        txt.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.receipt_content)
        messagebox.showinfo("Copied", "Receipt text copied to clipboard.")

    @guard
    def _save_to_file(self):
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Save Receipt",
            initialfile=self.default_filename,
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("All Files", "*.*")]
        )
        if dest:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(self.receipt_content)
            messagebox.showinfo("Saved", f"Receipt successfully saved to:\n{dest}")
