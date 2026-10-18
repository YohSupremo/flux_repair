import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED,
    FONT_DISPLAY, FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO_SM
)
from gui.widgets import guard, primary_button, secondary_button
from logic.auth import (
    login, register_user, find_user_by_identity, recover_password,
    compose_full_name, compose_address
)
from storage import get_rows
from errors import ValidationError, RuleError
from utils import valid_contact


class ForgotPasswordModal(tk.Toplevel):
    """
    Interactive Password Recovery Modal.
    Permits account lookup by Username or Registered Email, followed by
    identity verification and direct password reset.
    """
    def __init__(self, parent, on_reset_success_callback=None):
        super().__init__(parent)
        self.on_reset_success_callback = on_reset_success_callback

        self.title("Account Recovery - FLUX Repair Co.")
        self.configure(bg=BG)
        self.resizable(False, False)

        w, h = 500, 480
        self.geometry(f"{w}x{h}")
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
            self.geometry(f"{w}x{h}+{max(10, px)}+{max(10, py)}")
        except Exception:
            pass

        self.verified_user = None
        self._build_ui()

    def _build_ui(self):
        # Header banner
        hdr = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text="ACCOUNT RECOVERY",
            font=("Consolas", 8, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT,
            padx=8,
            pady=2
        ).pack(anchor="w")

        tk.Label(
            hdr,
            text="Reset Your Password",
            font=FONT_HEADING,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(3, 0))

        tk.Label(
            hdr,
            text="Verify your account username or registered email to reset your credentials.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # Body container
        self.body = tk.Frame(self, bg=BG, padx=24, pady=16)
        self.body.pack(fill="both", expand=True)

        # Card container
        self.card = tk.Frame(self.body, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=20, pady=16)
        self.card.pack(fill="both", expand=True)

        # Step 1: Identity Lookup
        tk.Label(self.card, text="Account identifier (username or email)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.ident_ent = tk.Entry(
            self.card,
            font=FONT_BODY,
            bg=BG_INPUT,
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE_BRIGHT,
            highlightcolor=EMERALD
        )
        self.ident_ent.pack(fill="x", ipady=7, padx=2)
        self.ident_err = tk.Label(self.card, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")
        self.ident_ent.bind("<KeyRelease>", lambda e: self._clear_ident_err())
        self.ident_ent.focus_set()

        self.btn_verify = primary_button(
            self.card,
            text="Verify Account",
            command=self._handle_verify,
            padx=18,
            pady=8
        )
        self.btn_verify.pack(anchor="w", pady=(12, 18))

        # Reset Section (revealed after verification)
        self.reset_frame = tk.Frame(self.card, bg=BG_PANEL)

        self.info_box = tk.Frame(self.reset_frame, bg=EMERALD_LIGHT, padx=12, pady=8, highlightthickness=1, highlightbackground=EMERALD)
        self.info_box.pack(fill="x", pady=(0, 16))
        self.info_lbl = tk.Label(self.info_box, text="", font=FONT_SMALL_BOLD, fg=EMERALD, bg=EMERALD_LIGHT)
        self.info_lbl.pack(anchor="w")

        tk.Label(self.reset_frame, text="New password (min 8 characters)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.new_pwd_ent = tk.Entry(self.reset_frame, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*", highlightthickness=1, highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)
        self.new_pwd_ent.pack(fill="x", ipady=7, padx=2)
        self.new_pwd_err = tk.Label(self.reset_frame, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")
        self.new_pwd_ent.bind("<KeyRelease>", lambda e: self._clear_pwd_err())

        tk.Label(self.reset_frame, text="Confirm new password", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(10, 4))
        self.conf_pwd_ent = tk.Entry(self.reset_frame, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*", highlightthickness=1, highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)
        self.conf_pwd_ent.pack(fill="x", ipady=7, padx=2)
        self.conf_pwd_err = tk.Label(self.reset_frame, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")
        self.conf_pwd_ent.bind("<KeyRelease>", lambda e: self._clear_conf_err())

        self.btn_save = primary_button(
            self.reset_frame,
            text="Save Password",
            command=self._handle_save_password,
            padx=20,
            pady=8
        )
        self.btn_save.pack(anchor="w", pady=(14, 0))

        # Footer close button
        bot = tk.Frame(self, bg=BG_PANEL, padx=24, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(side="bottom", fill="x")

        btn_close = secondary_button(
            bot,
            text="Close",
            command=self.destroy,
            padx=18,
            pady=8
        )
        btn_close.pack(side="right")

    def _clear_ident_err(self):
        self.ident_err.configure(text="")
        self.ident_err.pack_forget()
        self.ident_ent.configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _clear_pwd_err(self):
        self.new_pwd_err.configure(text="")
        self.new_pwd_err.pack_forget()
        self.new_pwd_ent.configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _clear_conf_err(self):
        self.conf_pwd_err.configure(text="")
        self.conf_pwd_err.pack_forget()
        self.conf_pwd_ent.configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _handle_verify(self):
        self._clear_ident_err()
        ident = self.ident_ent.get().strip()
        if not ident:
            self.ident_err.configure(text="Please enter your username or registered email.")
            self.ident_err.pack(anchor="w", pady=(2, 0), before=self.btn_verify)
            self.ident_ent.configure(highlightbackground=RED, highlightcolor=RED)
            self.ident_ent.focus_set()
            return

        user = find_user_by_identity(ident)
        if not user:
            self.ident_err.configure(text=f"No registered account matches \"{ident}\".")
            self.ident_err.pack(anchor="w", pady=(2, 0), before=self.btn_verify)
            self.ident_ent.configure(highlightbackground=RED, highlightcolor=RED)
            self.ident_ent.focus_set()
            return

        self.verified_user = user
        self.ident_ent.configure(state="readonly")
        self.btn_verify.pack_forget()

        self.info_lbl.configure(text=f"Account Verified: {user['full_name']} (@{user['username']})")
        self.reset_frame.pack(fill="x")
        self.new_pwd_ent.focus_set()

    def _handle_save_password(self):
        if not self.verified_user:
            return

        self._clear_pwd_err()
        self._clear_conf_err()

        np = self.new_pwd_ent.get().strip()
        cp = self.conf_pwd_ent.get().strip()

        has_err = False
        if not np:
            self.new_pwd_err.configure(text="New password is required.")
            self.new_pwd_err.pack(anchor="w", pady=(2, 0), before=self.conf_pwd_ent.master if False else None)
            self.new_pwd_ent.configure(highlightbackground=RED, highlightcolor=RED)
            self.new_pwd_ent.focus_set()
            has_err = True
        elif len(np) < 8:
            self.new_pwd_err.configure(text="Password must be at least 8 characters long.")
            self.new_pwd_err.pack(anchor="w", pady=(2, 0))
            self.new_pwd_ent.configure(highlightbackground=RED, highlightcolor=RED)
            self.new_pwd_ent.focus_set()
            has_err = True

        if not cp:
            self.conf_pwd_err.configure(text="Please confirm your new password.")
            self.conf_pwd_err.pack(anchor="w", pady=(2, 0), before=self.btn_save)
            self.conf_pwd_ent.configure(highlightbackground=RED, highlightcolor=RED)
            if not has_err:
                self.conf_pwd_ent.focus_set()
            has_err = True
        elif np and np != cp:
            self.conf_pwd_err.configure(text="New passwords do not match.")
            self.conf_pwd_err.pack(anchor="w", pady=(2, 0), before=self.btn_save)
            self.conf_pwd_ent.configure(highlightbackground=RED, highlightcolor=RED)
            if not has_err:
                self.conf_pwd_ent.focus_set()
            has_err = True

        if has_err:
            return

        try:
            recover_password(self.verified_user['username'], np, cp)
            messagebox.showinfo("Success", "Password updated successfully. You may now sign in with your new password.", parent=self)
            if self.on_reset_success_callback:
                self.on_reset_success_callback(self.verified_user['username'])
            self.destroy()
        except Exception as e:
            self.conf_pwd_err.configure(text=str(e))
            self.conf_pwd_err.pack(anchor="w", pady=(2, 0), before=self.btn_save)


class LoginView(tk.Frame):
    """
    Modern Split-Pane Website Login Page.
    Features:
    - Left Hero Showcase: Atelier mission, value propositions, and direct facility line.
    - Right Auth Console: Segmented sign-in/register switcher, email or username login,
      password visibility toggle, interactive forgot password flow, and 1-click test fill chips.
    """
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG)
        try:
            self.winfo_toplevel().title("FLUX Repair Co.")
        except Exception:
            pass
        self.on_login_success = on_login_success
        self.mode = "login"  # 'login' or 'register'
        self.show_password = False
        self.remember_var = tk.BooleanVar(value=True)
        self.field_errors = {}
        self.field_wrappers = {}

        self._build_ui()

    def _build_ui(self):
        # Master horizontal split container
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        # ---------------- LEFT PANE: ATELIER SHOWCASE ----------------
        left_pane = tk.Frame(container, bg="#0f172a", width=520)
        left_pane.pack(side="left", fill="both")
        left_pane.pack_propagate(False)

        left_content = tk.Frame(left_pane, bg="#0f172a", padx=48, pady=44)
        left_content.pack(fill="both", expand=True)

        # Top Brand Banner
        brand_row = tk.Frame(left_content, bg="#0f172a")
        brand_row.pack(anchor="w", pady=(0, 6))

        tk.Label(
            brand_row,
            text="FLUX",
            font=("Segoe UI", 20, "bold"),
            fg="#f8fafc",
            bg="#0f172a"
        ).pack(side="left")

        tk.Label(
            brand_row,
            text=" REPAIR CO.",
            font=("Segoe UI", 11, "bold"),
            fg="#34d399",
            bg="#0f172a"
        ).pack(side="left", pady=(5, 0))

        tk.Label(
            left_content,
            text="Precision Electronics Diagnostics & Microsoldering Lab",
            font=FONT_SMALL,
            fg="#94a3b8",
            bg="#0f172a"
        ).pack(anchor="w", pady=(0, 36))

        # Hero Value Proposition
        tk.Label(
            left_content,
            text="Dead is a diagnosis.\nNot a verdict.",
            font=("Segoe UI", 26, "bold"),
            fg="#f8fafc",
            bg="#0f172a",
            justify="left"
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(
            left_content,
            text=(
                "Component-level surgical repairs and emergency data retrieval for phones, "
                "laptops, and complex logic boards. We rescue what factory stores replace."
            ),
            font=FONT_BODY,
            fg="#94a3b8",
            bg="#0f172a",
            wraplength=420,
            justify="left"
        ).pack(anchor="w", pady=(0, 28))

        # Value Proposition Checkpoints
        checks = [
            "Free 24-hour diagnostic evaluation with upfront flat estimates",
            "90-day comprehensive written warranty on parts and labor",
            "Component rework preserving 100% of your personal files",
            "Real-time bench telemetry tracking throughout repair cycle"
        ]

        for item in checks:
            row = tk.Frame(left_content, bg="#0f172a")
            row.pack(fill="x", pady=6)

            pip = tk.Canvas(row, width=16, height=16, bg="#0f172a", highlightthickness=0)
            pip.pack(side="left", padx=(0, 10), pady=1)
            pip.create_oval(2, 2, 14, 14, fill="#064e3b", outline="#34d399")
            pip.create_text(8, 8, text="v", fill="#34d399", font=("Segoe UI", 7, "bold"))

            tk.Label(
                row,
                text=item,
                font=FONT_BODY,
                fg="#e2e8f0",
                bg="#0f172a",
                wraplength=380,
                justify="left"
            ).pack(side="left")

        # Bottom Atelier Facility Info
        bot_info = tk.Frame(left_content, bg="#1e293b", padx=18, pady=14, highlightthickness=1, highlightbackground="#334155")
        bot_info.pack(fill="x", side="bottom")

        tk.Label(
            bot_info,
            text="118 Beacon Works, Unit 3  |  Direct Line: (555) 019-3350",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        ).pack(anchor="w")

        tk.Label(
            bot_info,
            text="Bench Atelier Status: Online and accepting intakes",
            font=("Consolas", 8, "bold"),
            fg="#34d399",
            bg="#1e293b"
        ).pack(anchor="w", pady=(2, 0))

        # ---------------- RIGHT PANE: MODERN WEB AUTH ----------------
        right_pane = tk.Frame(container, bg=BG)
        right_pane.pack(side="right", fill="both", expand=True)

        # Center card container
        self.auth_card = tk.Frame(
            right_pane,
            bg=BG_PANEL,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=44,
            pady=38
        )
        self.auth_card.place(relx=0.5, rely=0.5, anchor="center")

        # Fixed width inner card (480px)
        self.inner = tk.Frame(self.auth_card, bg=BG_PANEL)
        self.inner.pack()
        tk.Frame(self.inner, width=480, height=0, bg=BG_PANEL).pack()

        # Segmented Pill Switcher
        pill_box = tk.Frame(self.inner, bg="#f1f5f9", padx=4, pady=4, bd=0, highlightthickness=1, highlightbackground=LINE)
        pill_box.pack(fill="x", pady=(0, 28))

        self.btn_tab_login = tk.Button(
            pill_box,
            text="Sign In",
            font=FONT_SMALL_BOLD,
            bg="#ffffff",
            fg=INK,
            bd=0,
            highlightthickness=1,
            highlightbackground=LINE,
            padx=18,
            pady=8,
            cursor="hand2",
            command=lambda: self._set_mode("login")
        )
        self.btn_tab_login.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_tab_reg = tk.Button(
            pill_box,
            text="Register",
            font=FONT_SMALL_BOLD,
            bg="#f1f5f9",
            fg=MUTED,
            bd=0,
            highlightthickness=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=lambda: self._set_mode("register")
        )
        self.btn_tab_reg.pack(side="left", fill="x", expand=True, padx=2)

        # Dynamic form area
        self.form_host = tk.Frame(self.inner, bg=BG_PANEL)
        self.form_host.pack(fill="x")

        self._render_form()

    def _show_field_error(self, key, message):
        if key in self.field_errors:
            lbl = self.field_errors[key]
            lbl.configure(text=message)
            lbl.pack(anchor="w", pady=(2, 0))
        if key in self.field_wrappers:
            self.field_wrappers[key].configure(highlightbackground=RED, highlightcolor=RED)

    def _clear_field_error(self, key):
        if key in self.field_errors:
            lbl = self.field_errors[key]
            lbl.configure(text="")
            lbl.pack_forget()
        if key in self.field_wrappers:
            self.field_wrappers[key].configure(highlightbackground=LINE, highlightcolor=EMERALD)

    def _clear_all_field_errors(self):
        for k in list(self.field_errors.keys()):
            self._clear_field_error(k)

    def _on_field_focus(self, key, wrp):
        wrp.configure(highlightbackground=EMERALD, highlightcolor=EMERALD)

    def _on_field_unfocus(self, key, wrp):
        if key in self.field_errors and self.field_errors[key].winfo_ismapped():
            wrp.configure(highlightbackground=RED, highlightcolor=RED)
        else:
            wrp.configure(highlightbackground=LINE)

    def _on_phone_char_validate(self, key, action, proposed, char):
        if action == '1':  # insertion
            if any(c.isalpha() for c in char):
                self._show_field_error(key, "Contact number cannot contain letters.")
                return False
        return True

    def _render_form(self):
        self._clear_all_field_errors()
        self.field_errors.clear()
        self.field_wrappers.clear()
        for child in self.form_host.winfo_children():
            child.destroy()

        is_login = (self.mode == "login")
        if is_login:
            self.btn_tab_login.configure(bg="#ffffff", fg=INK, highlightthickness=1)
            self.btn_tab_reg.configure(bg="#f1f5f9", fg=MUTED, highlightthickness=0)
            self._build_login_form()
        else:
            self.btn_tab_login.configure(bg="#f1f5f9", fg=MUTED, highlightthickness=0)
            self.btn_tab_reg.configure(bg="#ffffff", fg=INK, highlightthickness=1)
            self._build_register_form()

    def _build_login_form(self):
        tk.Label(self.form_host, text="Welcome Back", font=("Segoe UI", 18, "bold"), fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            self.form_host,
            text="Enter your workshop username or registered email address.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(4, 24))

        # Username / Email Input
        self.user_entry = self._build_input(self.form_host, "Username or email address", "e.g. admin or customer", bottom_pad=14, field_key="login_ident")
        self.user_entry.focus_set()

        # Password Input with Toggle
        self.pass_entry = self._build_input(
            self.form_host,
            "Password",
            "Enter password",
            show="*" if not self.show_password else "",
            with_toggle=True,
            bottom_pad=10,
            field_key="login_pass"
        )

        # Remember Me and Forgot Password Row
        opt_row = tk.Frame(self.form_host, bg=BG_PANEL)
        opt_row.pack(fill="x", pady=(0, 24))

        cb = tk.Checkbutton(
            opt_row,
            text="Remember me",
            variable=self.remember_var,
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=INK,
            bd=0,
            cursor="hand2"
        )
        cb.pack(side="left")

        forgot_link = tk.Label(
            opt_row,
            text="Forgot password?",
            font=FONT_SMALL_BOLD,
            fg=EMERALD,
            bg=BG_PANEL,
            cursor="hand2"
        )
        forgot_link.pack(side="right")
        forgot_link.bind("<Button-1>", lambda e: self._open_forgot_password_modal())
        forgot_link.bind("<Enter>", lambda e: forgot_link.configure(fg=EMERALD_HOVER))
        forgot_link.bind("<Leave>", lambda e: forgot_link.configure(fg=EMERALD))

        # Error notification label
        self.err_lbl = tk.Label(self.form_host, text="", font=FONT_SMALL_BOLD, fg=RED, bg=BG_PANEL)
        self.err_lbl.pack(anchor="w", pady=(0, 8))

        # Sign-in Action Button
        btn_sign = primary_button(
            self.form_host,
            text="Sign In",
            command=self._handle_login,
            pady=9
        )
        btn_sign.pack(fill="x", pady=(0, 20))

        # Switch to registration prompt
        sw_box = tk.Frame(self.form_host, bg=BG_PANEL)
        sw_box.pack(anchor="center")
        tk.Label(sw_box, text="Don't have an account? ", font=FONT_SMALL, fg=DIM, bg=BG_PANEL).pack(side="left")
        lnk = tk.Label(sw_box, text="Register", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._set_mode("register"))

        self.user_entry.bind("<Return>", lambda e: self._handle_login())
        self.pass_entry.bind("<Return>", lambda e: self._handle_login())

    def _build_register_form(self):
        tk.Label(self.form_host, text="Create Client Account", font=("Segoe UI", 18, "bold"), fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            self.form_host,
            text="Precision client onboarding for warranty coverage and device telemetry.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(4, 20))

        # 3-Step Segmented Stepper Bar (Read-only visual indicator; progression via buttons only)
        self.reg_tab_bar = tk.Frame(self.form_host, bg="#f1f5f9", padx=3, pady=3, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.reg_tab_bar.pack(fill="x", pady=(0, 26))

        self.reg_tab_btns = {}
        tabs = [
            ("personal", "1. Personal"),
            ("security", "2. Security"),
            ("address", "3. Address")
        ]

        for tab_key, tab_label in tabs:
            lbl = tk.Label(
                self.reg_tab_bar,
                text=tab_label,
                font=FONT_SMALL_BOLD,
                bg="#f1f5f9",
                fg=MUTED,
                bd=0,
                padx=10,
                pady=6
            )
            lbl.pack(side="left", fill="x", expand=True, padx=2)
            self.reg_tab_btns[tab_key] = lbl

        # Container host for the 3 tabs
        self.reg_host = tk.Frame(self.form_host, bg=BG_PANEL)
        self.reg_host.pack(fill="x")

        # ---------------- TAB 1: PERSONAL INFORMATION ----------------
        self.reg_v_personal = tk.Frame(self.reg_host, bg=BG_PANEL)

        # Divided Name: First Name & Last Name in 2 columns
        name_row = tk.Frame(self.reg_v_personal, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 16))

        b_fn = tk.Frame(name_row, bg=BG_PANEL)
        b_fn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_fn, text="First name *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_fn = tk.Frame(b_fn, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_fn.pack(fill="x")
        self.reg_fname = tk.Entry(w_fn, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_fname.pack(fill="x", ipady=7, padx=10)
        self.field_errors["fname"] = tk.Label(b_fn, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        b_ln = tk.Frame(name_row, bg=BG_PANEL)
        b_ln.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_ln, text="Last name *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_ln = tk.Frame(b_ln, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_ln.pack(fill="x")
        self.reg_lname = tk.Entry(w_ln, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_lname.pack(fill="x", ipady=7, padx=10)
        self.field_errors["lname"] = tk.Label(b_ln, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Contact Number
        b_phone = tk.Frame(self.reg_v_personal, bg=BG_PANEL)
        b_phone.pack(fill="x", pady=(0, 8))
        tk.Label(b_phone, text="Contact number *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_phone = tk.Frame(b_phone, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_phone.pack(fill="x")
        vcmd_phone = (self.register(lambda act, p, char: self._on_phone_char_validate("phone", act, p, char)), '%d', '%P', '%S')
        self.reg_phone = tk.Entry(w_phone, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, validate="key", validatecommand=vcmd_phone)
        self.reg_phone.pack(fill="x", ipady=7, padx=10)
        self.field_errors["phone"] = tk.Label(b_phone, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Guidance Note
        tk.Label(
            self.reg_v_personal,
            text="Primary contact used for real-time bench updates and pick-up authorization.",
            font=("Segoe UI", 8),
            fg=DIM,
            bg=BG_PANEL,
            wraplength=460,
            justify="left"
        ).pack(anchor="w", pady=(2, 28))

        # Next Button
        btn_next_sec = primary_button(
            self.reg_v_personal,
            text="Continue",
            command=self._proceed_from_personal,
            pady=9
        )
        btn_next_sec.pack(fill="x")

        # ---------------- TAB 2: SECURITY ----------------
        self.reg_v_security = tk.Frame(self.reg_host, bg=BG_PANEL)

        # Username & Email in 2 columns
        row_id = tk.Frame(self.reg_v_security, bg=BG_PANEL)
        row_id.pack(fill="x", pady=(0, 16))

        b_user = tk.Frame(row_id, bg=BG_PANEL)
        b_user.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_user, text="Username *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_user = tk.Frame(b_user, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_user.pack(fill="x")
        self.reg_uname = tk.Entry(w_user, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_uname.pack(fill="x", ipady=7, padx=10)
        self.field_errors["uname"] = tk.Label(b_user, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        b_email = tk.Frame(row_id, bg=BG_PANEL)
        b_email.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_email, text="Email address *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_email = tk.Frame(b_email, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_email.pack(fill="x")
        self.reg_email = tk.Entry(w_email, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_email.pack(fill="x", ipady=7, padx=10)
        self.field_errors["email"] = tk.Label(b_email, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Passwords in 2 columns
        row_pw = tk.Frame(self.reg_v_security, bg=BG_PANEL)
        row_pw.pack(fill="x", pady=(0, 6))

        b_p1 = tk.Frame(row_pw, bg=BG_PANEL)
        b_p1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_p1, text="Password *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_p1 = tk.Frame(b_p1, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_p1.pack(fill="x")
        self.reg_pwd = tk.Entry(w_p1, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*")
        self.reg_pwd.pack(fill="x", ipady=7, padx=10)
        self.field_errors["pwd"] = tk.Label(b_p1, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        b_p2 = tk.Frame(row_pw, bg=BG_PANEL)
        b_p2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_p2, text="Confirm password *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_p2 = tk.Frame(b_p2, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_p2.pack(fill="x")
        self.reg_cpwd = tk.Entry(w_p2, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show="*")
        self.reg_cpwd.pack(fill="x", ipady=7, padx=10)
        self.field_errors["cpwd"] = tk.Label(b_p2, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        tk.Label(
            self.reg_v_security,
            text="Min 8 characters. Both username and email can be used to sign in.",
            font=("Segoe UI", 8),
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 28))

        # Nav Buttons Row
        sec_nav = tk.Frame(self.reg_v_security, bg=BG_PANEL)
        sec_nav.pack(fill="x")

        btn_back_p = secondary_button(
            sec_nav,
            text="Back",
            command=lambda: self._switch_reg_tab("personal"),
            padx=20,
            pady=8
        )
        btn_back_p.pack(side="left")

        btn_next_addr = primary_button(
            sec_nav,
            text="Continue",
            command=self._proceed_from_security,
            padx=26,
            pady=8
        )
        btn_next_addr.pack(side="right")

        # ---------------- TAB 3: ADDRESS ----------------
        self.reg_v_address = tk.Frame(self.reg_host, bg=BG_PANEL)

        # Street Address
        b_st = tk.Frame(self.reg_v_address, bg=BG_PANEL)
        b_st.pack(fill="x", pady=(0, 14))
        tk.Label(b_st, text="Street address *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_st = tk.Frame(b_st, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_st.pack(fill="x")
        self.reg_street = tk.Entry(w_st, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_street.pack(fill="x", ipady=7, padx=10)
        self.field_errors["street"] = tk.Label(b_st, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Apartment / Suite / Unit (Optional)
        b_unit = tk.Frame(self.reg_v_address, bg=BG_PANEL)
        b_unit.pack(fill="x", pady=(0, 14))
        tk.Label(b_unit, text="Apartment, suite, unit (optional)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_unit = tk.Frame(b_unit, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_unit.pack(fill="x")
        self.reg_unit = tk.Entry(w_unit, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_unit.pack(fill="x", ipady=7, padx=10)

        # City & State / Province in 2 columns
        row_cs = tk.Frame(self.reg_v_address, bg=BG_PANEL)
        row_cs.pack(fill="x", pady=(0, 14))

        b_city = tk.Frame(row_cs, bg=BG_PANEL)
        b_city.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_city, text="City *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_city = tk.Frame(b_city, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_city.pack(fill="x")
        self.reg_city = tk.Entry(w_city, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_city.pack(fill="x", ipady=7, padx=10)
        self.field_errors["city"] = tk.Label(b_city, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        b_state = tk.Frame(row_cs, bg=BG_PANEL)
        b_state.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_state, text="State / Province *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_state = tk.Frame(b_state, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_state.pack(fill="x")
        self.reg_state = tk.Entry(w_state, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_state.pack(fill="x", ipady=7, padx=10)
        self.field_errors["state"] = tk.Label(b_state, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Postal Code / ZIP
        b_zip = tk.Frame(self.reg_v_address, bg=BG_PANEL)
        b_zip.pack(fill="x", pady=(0, 26))
        tk.Label(b_zip, text="Postal code / ZIP *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        w_zip = tk.Frame(b_zip, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        w_zip.pack(fill="x")
        self.reg_zip = tk.Entry(w_zip, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0)
        self.reg_zip.pack(fill="x", ipady=7, padx=10)
        self.field_errors["zip"] = tk.Label(b_zip, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        # Nav Buttons Row
        addr_nav = tk.Frame(self.reg_v_address, bg=BG_PANEL)
        addr_nav.pack(fill="x")

        btn_back_s = secondary_button(
            addr_nav,
            text="Back",
            command=lambda: self._switch_reg_tab("security"),
            padx=20,
            pady=8
        )
        btn_back_s.pack(side="left")

        btn_finish = primary_button(
            addr_nav,
            text="Create Account",
            command=self._handle_register,
            padx=26,
            pady=8
        )
        btn_finish.pack(side="right")

        # Focus highlights & typing listeners for all inputs
        for key, ent, wrp in [
            ("fname", self.reg_fname, w_fn),
            ("lname", self.reg_lname, w_ln),
            ("phone", self.reg_phone, w_phone),
            ("uname", self.reg_uname, w_user),
            ("email", self.reg_email, w_email),
            ("pwd", self.reg_pwd, w_p1),
            ("cpwd", self.reg_cpwd, w_p2),
            ("street", self.reg_street, w_st),
            ("unit", self.reg_unit, w_unit),
            ("city", self.reg_city, w_city),
            ("state", self.reg_state, w_state),
            ("zip", self.reg_zip, w_zip)
        ]:
            self.field_wrappers[key] = wrp
            ent.bind("<FocusIn>", lambda e, k=key, w=wrp: self._on_field_focus(k, w))
            ent.bind("<FocusOut>", lambda e, k=key, w=wrp: self._on_field_unfocus(k, w))
            ent.bind("<KeyRelease>", lambda e, k=key: self._clear_field_error(k))

        # Return key progression
        self.reg_fname.bind("<Return>", lambda e: self.reg_lname.focus_set())
        self.reg_lname.bind("<Return>", lambda e: self.reg_phone.focus_set())
        self.reg_phone.bind("<Return>", lambda e: self._proceed_from_personal())
        self.reg_uname.bind("<Return>", lambda e: self.reg_email.focus_set())
        self.reg_email.bind("<Return>", lambda e: self.reg_pwd.focus_set())
        self.reg_pwd.bind("<Return>", lambda e: self.reg_cpwd.focus_set())
        self.reg_cpwd.bind("<Return>", lambda e: self._proceed_from_security())
        self.reg_street.bind("<Return>", lambda e: self.reg_unit.focus_set())
        self.reg_unit.bind("<Return>", lambda e: self.reg_city.focus_set())
        self.reg_city.bind("<Return>", lambda e: self.reg_state.focus_set())
        self.reg_state.bind("<Return>", lambda e: self.reg_zip.focus_set())
        self.reg_zip.bind("<Return>", lambda e: self._handle_register())

        # Error notification label (for general server/system alerts)
        self.err_lbl = tk.Label(self.form_host, text="", font=FONT_SMALL_BOLD, fg=RED, bg=BG_PANEL)
        self.err_lbl.pack(anchor="w", pady=(12, 4))

        # Switch to login prompt
        sw_box = tk.Frame(self.form_host, bg=BG_PANEL)
        sw_box.pack(anchor="center", pady=(16, 0))
        tk.Label(sw_box, text="Already have an account? ", font=FONT_SMALL, fg=DIM, bg=BG_PANEL).pack(side="left")
        lnk = tk.Label(sw_box, text="Sign in", font=FONT_SMALL_BOLD, fg=EMERALD, bg=BG_PANEL, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._set_mode("login"))

        # Activate initial tab
        self._switch_reg_tab("personal")

    def _proceed_from_personal(self):
        self._clear_all_field_errors()
        self.err_lbl.configure(text="")
        fname = self.reg_fname.get().strip()
        lname = self.reg_lname.get().strip()
        phone = self.reg_phone.get().strip()

        has_error = False
        first_focus = None

        if not fname:
            self._show_field_error("fname", "First name is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_fname
        if not lname:
            self._show_field_error("lname", "Last name is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_lname
        if not phone:
            self._show_field_error("phone", "Contact number is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_phone
        elif any(c.isalpha() for c in phone):
            self._show_field_error("phone", "Contact number cannot contain letters.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_phone
        else:
            try:
                valid_contact(phone, "Contact number")
            except ValidationError as ve:
                self._show_field_error("phone", str(ve))
                has_error = True
                if not first_focus:
                    first_focus = self.reg_phone

        if has_error:
            first_focus.focus_set()
            return

        self._switch_reg_tab("security")

    def _proceed_from_security(self):
        self._clear_all_field_errors()
        self.err_lbl.configure(text="")
        uname = self.reg_uname.get().strip()
        email = self.reg_email.get().strip()
        pwd = self.reg_pwd.get()
        cpwd = self.reg_cpwd.get()

        has_error = False
        first_focus = None

        if not uname:
            self._show_field_error("uname", "Username is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_uname
        elif " " in uname or len(uname) < 3 or len(uname) > 20:
            self._show_field_error("uname", "Must be 3-20 characters, no spaces.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_uname
        else:
            for u in get_rows('users'):
                if u['username'].lower() == uname.lower():
                    self._show_field_error("uname", f"Username '{uname}' is already taken.")
                    has_error = True
                    if not first_focus:
                        first_focus = self.reg_uname
                    break

        if not email:
            self._show_field_error("email", "Email address is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_email
        elif "@" not in email or "." not in email:
            self._show_field_error("email", "Please enter a valid email address.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_email

        if not pwd:
            self._show_field_error("pwd", "Password is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_pwd
        elif len(pwd) < 8:
            self._show_field_error("pwd", "Password must be at least 8 characters.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_pwd

        if not cpwd:
            self._show_field_error("cpwd", "Please confirm your password.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_cpwd
        elif pwd and pwd != cpwd:
            self._show_field_error("cpwd", "Passwords do not match.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_cpwd

        if has_error:
            first_focus.focus_set()
            return

        self._switch_reg_tab("address")

    def _switch_reg_tab(self, tab_key):
        self._clear_all_field_errors()
        self.err_lbl.configure(text="")
        self.reg_active_tab = tab_key
        for k, btn in self.reg_tab_btns.items():
            if k == tab_key:
                btn.configure(
                    bg="#ffffff",
                    fg=INK,
                    font=FONT_SMALL_BOLD,
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=LINE
                )
            else:
                btn.configure(
                    bg="#f1f5f9",
                    fg=MUTED,
                    font=FONT_SMALL_BOLD,
                    bd=0,
                    highlightthickness=0
                )

        self.reg_v_personal.pack_forget()
        self.reg_v_security.pack_forget()
        self.reg_v_address.pack_forget()

        if tab_key == "personal":
            self.reg_v_personal.pack(fill="x")
            if hasattr(self, 'reg_fname'):
                self.reg_fname.focus_set()
        elif tab_key == "security":
            self.reg_v_security.pack(fill="x")
            if hasattr(self, 'reg_uname'):
                self.reg_uname.focus_set()
        elif tab_key == "address":
            self.reg_v_address.pack(fill="x")
            if hasattr(self, 'reg_street'):
                self.reg_street.focus_set()

    def _build_input(self, parent, label_text, placeholder="", show="", with_toggle=False, bottom_pad=18, field_key=None):
        box = tk.Frame(parent, bg=BG_PANEL)
        box.pack(fill="x", pady=(0, bottom_pad))

        tk.Label(box, text=label_text, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))

        wrap = tk.Frame(box, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        wrap.pack(fill="x")

        entry = tk.Entry(wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, show=show)
        entry.pack(side="left", fill="x", expand=True, ipady=7, padx=10)

        if field_key:
            self.field_wrappers[field_key] = wrap
            self.field_errors[field_key] = tk.Label(box, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")
            entry.bind("<FocusIn>", lambda e, k=field_key, w=wrap: self._on_field_focus(k, w))
            entry.bind("<FocusOut>", lambda e, k=field_key, w=wrap: self._on_field_unfocus(k, w))
            entry.bind("<KeyRelease>", lambda e, k=field_key: self._clear_field_error(k))
        else:
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

    def _open_forgot_password_modal(self):
        ForgotPasswordModal(
            self.winfo_toplevel(),
            on_reset_success_callback=lambda uname: self._on_password_reset_success(uname)
        )

    def _on_password_reset_success(self, username):
        if hasattr(self, 'user_entry') and self.user_entry.winfo_exists():
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, username)
        if hasattr(self, 'pass_entry') and self.pass_entry.winfo_exists():
            self.pass_entry.delete(0, tk.END)
            self.pass_entry.focus_set()

    def _set_mode(self, mode):
        self.mode = mode
        self.show_password = False
        self._render_form()

    @guard
    def _handle_login(self):
        self._clear_all_field_errors()
        self.err_lbl.configure(text="")
        ident = self.user_entry.get().strip()
        password = self.pass_entry.get()

        has_error = False
        first_err = None

        if not ident:
            self._show_field_error("login_ident", "Please enter your username or email address.")
            has_error = True
            if not first_err:
                first_err = self.user_entry
        if not password:
            self._show_field_error("login_pass", "Please enter your password.")
            has_error = True
            if not first_err:
                first_err = self.pass_entry

        if has_error:
            first_err.focus_set()
            return

        user = login(ident, password)
        self.on_login_success(user)

    @guard
    def _handle_register(self):
        self._clear_all_field_errors()
        self.err_lbl.configure(text="")
        fname = self.reg_fname.get().strip()
        lname = self.reg_lname.get().strip()
        phone = self.reg_phone.get().strip()

        uname = self.reg_uname.get().strip()
        email = self.reg_email.get().strip()
        pwd = self.reg_pwd.get()
        cpwd = self.reg_cpwd.get()

        street = self.reg_street.get().strip()
        unit = self.reg_unit.get().strip()
        city = self.reg_city.get().strip()
        state = self.reg_state.get().strip()
        zip_code = self.reg_zip.get().strip()

        # Step 3 Inline validations
        has_error = False
        first_focus = None

        if not street:
            self._show_field_error("street", "Street address is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_street
        if not city:
            self._show_field_error("city", "City is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_city
        if not state:
            self._show_field_error("state", "State / Province is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_state
        if not zip_code:
            self._show_field_error("zip", "Postal code / ZIP is required.")
            has_error = True
            if not first_focus:
                first_focus = self.reg_zip

        if has_error:
            first_focus.focus_set()
            return

        full_name = compose_full_name(fname, lname)
        address = compose_address(street, unit, city, state, zip_code)

        try:
            user = register_user(
                username=uname,
                password=pwd,
                confirm_password=cpwd,
                full_name=full_name,
                contact_no=phone,
                email=email,
                address=address
            )
            messagebox.showinfo(
                "Account Created",
                f"Welcome, {full_name}!\n\nYour client account has been created successfully."
            )
            self.on_login_success(user)
        except (ValidationError, RuleError) as err:
            err_msg = str(err)
            if "username" in err_msg.lower():
                self._switch_reg_tab("security")
                self._show_field_error("uname", err_msg)
                self.reg_uname.focus_set()
            elif "password" in err_msg.lower():
                self._switch_reg_tab("security")
                self._show_field_error("pwd", err_msg)
                self.reg_pwd.focus_set()
            elif "contact" in err_msg.lower():
                self._switch_reg_tab("personal")
                self._show_field_error("phone", err_msg)
                self.reg_phone.focus_set()
            else:
                self.err_lbl.configure(text=err_msg)
        except Exception as e:
            self.err_lbl.configure(text=f"Registration failed: {e}")
