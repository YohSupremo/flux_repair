import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD
)
from gui.widgets import guard
from logic.auth import login, register_user


class LoginView(tk.Frame):
    """
    Polished Minimalist Authentication Card.
    Clean, focused, distraction-free interface for Sign In and Account Registration.
    """
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG)
        self.on_login_success = on_login_success
        self.mode = "login"  # 'login' or 'register'
        self.show_password = False

        self._build_ui()

    def _build_ui(self):
        # Center card container
        self.card = tk.Frame(
            self,
            bg=BG_PANEL,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=44,
            pady=36
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")

        # Fixed width inner wrapper (420px wide)
        self.inner = tk.Frame(self.card, bg=BG_PANEL)
        self.inner.pack()
        # Invisible spacer to lock constant card width across both tabs
        tk.Frame(self.inner, width=380, height=0, bg=BG_PANEL).pack()

        # Brand Header
        brand_row = tk.Frame(self.inner, bg=BG_PANEL)
        brand_row.pack(anchor="center", pady=(0, 4))

        tk.Label(
            brand_row,
            text="FLUX",
            font=("Segoe UI", 20, "bold"),
            fg=INK,
            bg=BG_PANEL
        ).pack(side="left")

        tk.Label(
            brand_row,
            text=" REPAIR CO.",
            font=("Segoe UI", 11, "bold"),
            fg=EMERALD,
            bg=BG_PANEL
        ).pack(side="left", pady=(5, 0))

        tk.Label(
            self.inner,
            text="Computer & Electronics Service System",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="center", pady=(0, 20))

        # Thin hairline divider
        tk.Frame(self.inner, bg=LINE, height=1).pack(fill="x", pady=(0, 20))

        # Segmented Tab Switcher (Sign In / Create Account)
        self.tab_bar = tk.Frame(
            self.inner,
            bg="#f1f5f9",
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=4,
            pady=4
        )
        self.tab_bar.pack(fill="x", pady=(0, 24))

        self.form_host = tk.Frame(self.inner, bg=BG_PANEL)
        self.form_host.pack(fill="x")

        self._render_form()

    def _render_form(self):
        # Update tab styles
        for child in self.tab_bar.winfo_children():
            child.destroy()

        is_login = (self.mode == "login")

        login_tab = tk.Button(
            self.tab_bar,
            text="Sign In",
            font=FONT_BODY_BOLD if is_login else FONT_BODY,
            bg=BG_PANEL if is_login else "#f1f5f9",
            fg=INK if is_login else MUTED,
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
            command=lambda: self._set_mode("login")
        )
        login_tab.pack(side="left", fill="x", expand=True)

        reg_tab = tk.Button(
            self.tab_bar,
            text="Create Account",
            font=FONT_BODY_BOLD if not is_login else FONT_BODY,
            bg=BG_PANEL if not is_login else "#f1f5f9",
            fg=INK if not is_login else MUTED,
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
            command=lambda: self._set_mode("register")
        )
        reg_tab.pack(side="left", fill="x", expand=True)

        # Clear form host
        for child in self.form_host.winfo_children():
            child.destroy()

        if is_login:
            self._build_login_form()
        else:
            self._build_register_form()

    def _build_login_form(self):
        # Username
        self.user_entry = self._build_input(self.form_host, "USERNAME", "Enter your username")
        self.user_entry.focus_set()

        # Password
        self.pass_entry = self._build_input(
            self.form_host,
            "PASSWORD",
            "Enter your password",
            show="*" if not self.show_password else "",
            with_toggle=True
        )

        # Error notification label
        self.err_lbl = tk.Label(self.form_host, text="", font=FONT_SMALL_BOLD, fg=RED, bg=BG_PANEL)
        self.err_lbl.pack(anchor="w", pady=(0, 10))

        # Sign-in button
        sign_btn = tk.Button(
            self.form_host,
            text="Sign In →",
            font=FONT_BODY_BOLD,
            bg=EMERALD,
            fg="#ffffff",
            activebackground=EMERALD_HOVER,
            activeforeground="#ffffff",
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self._handle_login
        )
        sign_btn.pack(fill="x", pady=(0, 4))

        # Enter key triggers login
        self.user_entry.bind("<Return>", lambda e: self._handle_login())
        self.pass_entry.bind("<Return>", lambda e: self._handle_login())

    def _build_register_form(self):
        # Full Name
        self.reg_fname = self._build_input(self.form_host, "FULL NAME *", "e.g. Maria Santos")
        self.reg_fname.focus_set()

        # Username
        self.reg_uname = self._build_input(self.form_host, "USERNAME *", "e.g. maria_santos")

        # Two-column Passwords row
        p_row = tk.Frame(self.form_host, bg=BG_PANEL)
        p_row.pack(fill="x", pady=(0, 14))

        # Password
        p1_box = tk.Frame(p_row, bg=BG_PANEL)
        p1_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(p1_box, text="PASSWORD *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        p1_wrap = tk.Frame(p1_box, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        p1_wrap.pack(fill="x")
        self.reg_pwd = tk.Entry(p1_wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*")
        self.reg_pwd.pack(fill="x", ipady=7, padx=10)

        # Confirm Password
        p2_box = tk.Frame(p_row, bg=BG_PANEL)
        p2_box.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(p2_box, text="CONFIRM *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        p2_wrap = tk.Frame(p2_box, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        p2_wrap.pack(fill="x")
        self.reg_cpwd = tk.Entry(p2_wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*")
        self.reg_cpwd.pack(fill="x", ipady=7, padx=10)

        # Error notification label
        self.err_lbl = tk.Label(self.form_host, text="", font=FONT_SMALL_BOLD, fg=RED, bg=BG_PANEL)
        self.err_lbl.pack(anchor="w", pady=(0, 10))

        # Register button
        reg_btn = tk.Button(
            self.form_host,
            text="Create Account →",
            font=FONT_BODY_BOLD,
            bg=EMERALD,
            fg="#ffffff",
            activebackground=EMERALD_HOVER,
            activeforeground="#ffffff",
            bd=0,
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self._handle_register
        )
        reg_btn.pack(fill="x", pady=(0, 12))

        # Switch to login prompt
        sw_box = tk.Frame(self.form_host, bg=BG_PANEL)
        sw_box.pack(anchor="center")

        tk.Label(sw_box, text="Already have an account? ", font=FONT_SMALL, fg=DIM, bg=BG_PANEL).pack(side="left")
        lnk = tk.Label(sw_box, text="Sign in", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._set_mode("login"))

        self.reg_fname.bind("<Return>", lambda e: self._handle_register())
        self.reg_uname.bind("<Return>", lambda e: self._handle_register())
        self.reg_pwd.bind("<Return>", lambda e: self._handle_register())
        self.reg_cpwd.bind("<Return>", lambda e: self._handle_register())

    def _build_input(self, parent, label_text, placeholder, show="", with_toggle=False):
        """Construct clean padded input field with focus highlighting."""
        box = tk.Frame(parent, bg=BG_PANEL)
        box.pack(fill="x", pady=(0, 14))

        tk.Label(box, text=label_text, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))

        wrap = tk.Frame(box, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        wrap.pack(fill="x")

        entry = tk.Entry(wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show=show)
        entry.pack(side="left", fill="x", expand=True, ipady=7, padx=12)

        entry.bind("<FocusIn>", lambda e, w=wrap: w.configure(highlightbackground=EMERALD, highlightcolor=EMERALD))
        entry.bind("<FocusOut>", lambda e, w=wrap: w.configure(highlightbackground=LINE))

        if with_toggle:
            btn = tk.Label(wrap, text="Show", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=BG_INPUT, cursor="hand2", padx=10)
            btn.pack(side="right")

            def _toggle():
                self.show_password = not self.show_password
                if self.show_password:
                    entry.configure(show="")
                    btn.configure(text="Hide", fg=EMERALD)
                else:
                    entry.configure(show="*")
                    btn.configure(text="Show", fg=MUTED)

            btn.bind("<Button-1>", lambda e: _toggle())

        return entry

    def _set_mode(self, mode):
        self.mode = mode
        self.show_password = False
        self._render_form()

    @guard
    def _handle_login(self):
        self.err_lbl.configure(text="")
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        user = login(username, password)
        self.on_login_success(user)

    @guard
    def _handle_register(self):
        self.err_lbl.configure(text="")
        fname = self.reg_fname.get().strip()
        uname = self.reg_uname.get().strip()
        pwd = self.reg_pwd.get()
        cpwd = self.reg_cpwd.get()

        user = register_user(uname, pwd, cpwd, fname)
        messagebox.showinfo(
            "Account Created",
            f"Welcome, {fname}!\n\nYour account has been created successfully."
        )
        self.on_login_success(user)
