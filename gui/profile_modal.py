import tkinter as tk
from tkinter import messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO_SM
)
from gui.widgets import primary_button, secondary_button
from logic.auth import (
    get_user_profile, update_profile,
    split_full_name, compose_full_name, compose_address, parse_address
)
from errors import ValidationError, RuleError
from utils import valid_contact


class AccountSettingsModal(tk.Toplevel):
    """
    Account Settings & Profile Preferences Modal.
    Features professional typographic hierarchy, generous column gutters,
    and distinct semantic vertical spacing scale:
    - Tab 1: Personal Information (Divided Name & Contact Number)
    - Tab 2: Security (Username, Email, Current/New Password)
    - Tab 3: Address (Chopped Street, Unit, City, State, Postal Code)
    """
    def __init__(self, parent, current_user, on_profile_updated_callback=None):
        super().__init__(parent)
        self.current_user = current_user
        self.on_profile_updated_callback = on_profile_updated_callback

        self.title("Account Settings - FLUX Repair Co.")
        self.configure(bg=BG)
        self.resizable(False, False)

        # Center modal with comfortable, generous dimensions
        w, h = 600, 700
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

        self.active_tab = "personal"
        self.field_errors = {}
        self.field_wrappers = {}
        self._load_data()
        self._build_ui()

    def _load_data(self):
        uid = self.current_user.get('user_id')
        uname = self.current_user.get('username')
        self.profile = get_user_profile(uid, username=uname) or {
            'user_id': uid,
            'username': self.current_user.get('username', ''),
            'role': self.current_user.get('role', 'Customer'),
            'full_name': self.current_user.get('full_name', ''),
            'contact_no': '',
            'email': '',
            'address': ''
        }
        self.first_name, self.last_name = split_full_name(self.profile.get('full_name', ''))
        self.addr_components = parse_address(self.profile.get('address', ''))

    def _build_ui(self):
        # 1. Header Banner
        hdr = tk.Frame(self, bg=BG_PANEL, padx=28, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text="ACCOUNT & PREFERENCES",
            font=("Consolas", 8, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT,
            padx=8,
            pady=3
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            hdr,
            text="Account Settings",
            font=("Segoe UI", 16, "bold"),
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            hdr,
            text="Manage your personal contact info, security credentials, and delivery address.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w")

        # 2. Modern Segmented 3-Pill Tab Bar
        tab_section = tk.Frame(self, bg=BG, padx=28)
        tab_section.pack(fill="x", pady=(12, 10))

        self.pill_bar = tk.Frame(tab_section, bg="#f1f5f9", padx=4, pady=4, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.pill_bar.pack(fill="x")

        self.tab_buttons = {}

        tabs = [
            ("personal", "Personal Information"),
            ("security", "Security"),
            ("address", "Address")
        ]

        for tab_key, label_text in tabs:
            btn = tk.Button(
                self.pill_bar,
                text=label_text,
                font=FONT_SMALL_BOLD,
                bg="#f1f5f9",
                fg=MUTED,
                activebackground="#ffffff",
                activeforeground=INK,
                bd=0,
                padx=14,
                pady=8,
                cursor="hand2",
                command=lambda k=tab_key: self._switch_tab(k)
            )
            btn.pack(side="left", fill="x", expand=True, padx=2)
            self.tab_buttons[tab_key] = btn

        # 3. Harmonized Footer Action Buttons (PINNED TO BOTTOM FIRST)
        bot = tk.Frame(self, bg=BG_PANEL, padx=28, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(side="bottom", fill="x")

        # Primary Save Button
        btn_save = primary_button(
            bot,
            text="Save Changes",
            command=self._save,
            padx=22,
            pady=8
        )
        btn_save.pack(side="right", padx=(12, 0))

        # Secondary Cancel Button
        btn_cancel = secondary_button(
            bot,
            text="Cancel",
            command=self.destroy,
            padx=18,
            pady=8
        )
        btn_cancel.pack(side="right")

        # 4. Content View Area (Fills remaining middle space)
        self.content_container = tk.Frame(self, bg=BG, padx=28)
        self.content_container.pack(side="top", fill="both", expand=True, pady=(0, 10))

        self._build_personal_tab()
        self._build_security_tab()
        self._build_address_tab()

        # Activate initial tab
        self._switch_tab("personal")

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
            self.field_wrappers[key].configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _clear_all_field_errors(self):
        for k in list(self.field_errors.keys()):
            self._clear_field_error(k)

    def _on_field_focus(self, key, wrp):
        wrp.configure(highlightbackground=EMERALD, highlightcolor=EMERALD)

    def _on_field_unfocus(self, key, wrp):
        if key in self.field_errors and self.field_errors[key].winfo_ismapped():
            wrp.configure(highlightbackground=RED, highlightcolor=RED)
        else:
            wrp.configure(highlightbackground=LINE_BRIGHT)

    def _on_phone_char_validate(self, key, action, proposed, char):
        if action == '1':  # insertion
            if any(c.isalpha() for c in char):
                self._show_field_error(key, "Contact number cannot contain letters.")
                return False
        return True

    def _entry(self, parent, default_val="", is_readonly=False, is_password=False, is_phone=False, with_toggle=False, field_key=None):
        show_char = "*" if is_password else ""
        wrap = tk.Frame(parent, bg="#f1f5f9" if is_readonly else BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE_BRIGHT)
        wrap.pack(fill="x")

        extra_kwargs = {}
        if is_phone:
            vcmd = (self.register(lambda act, p, char: self._on_phone_char_validate(field_key or "contact", act, p, char)), '%d', '%P', '%S')
            extra_kwargs["validate"] = "key"
            extra_kwargs["validatecommand"] = vcmd

        ent = tk.Entry(
            wrap,
            font=FONT_BODY,
            bg="#f1f5f9" if is_readonly else BG_INPUT,
            fg=DIM if is_readonly else INK,
            bd=0,
            show=show_char,
            **extra_kwargs
        )
        ent.pack(side="left", fill="x", expand=True, ipady=7, padx=10)

        if is_password and with_toggle:
            t_btn = tk.Label(wrap, text="Show", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=BG_INPUT, cursor="hand2", padx=10)
            t_btn.pack(side="right")

            def _toggle(b=t_btn, e=ent):
                if e.cget("show") == "*":
                    e.configure(show="")
                    b.configure(text="Hide", fg=EMERALD)
                else:
                    e.configure(show="*")
                    b.configure(text="Show", fg=MUTED)

            t_btn.bind("<Button-1>", lambda ev, b=t_btn, e=ent: _toggle(b, e))

        if field_key:
            self.field_wrappers[field_key] = wrap
            self.field_errors[field_key] = tk.Label(parent, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")
            ent.bind("<FocusIn>", lambda e, k=field_key, w=wrap: self._on_field_focus(k, w))
            ent.bind("<FocusOut>", lambda e, k=field_key, w=wrap: self._on_field_unfocus(k, w))
            ent.bind("<KeyRelease>", lambda e, k=field_key: self._clear_field_error(k))
        elif not is_readonly:
            ent.bind("<FocusIn>", lambda e, w=wrap: w.configure(highlightbackground=EMERALD, highlightcolor=EMERALD))
            ent.bind("<FocusOut>", lambda e, w=wrap: w.configure(highlightbackground=LINE_BRIGHT))

        if default_val:
            ent.insert(0, str(default_val))
        if is_readonly:
            ent.configure(state="readonly")
        return ent

    def _build_personal_tab(self):
        self.tab_personal = tk.Frame(self.content_container, bg=BG)

        card = tk.Frame(self.tab_personal, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        card.pack(fill="both", expand=True)

        # Account Meta Info Header
        u_row = tk.Frame(card, bg=BG_PANEL)
        u_row.pack(fill="x", pady=(0, 16))

        tk.Label(
            u_row,
            text=f"Account: {self.profile['username']}",
            font=FONT_BODY_BOLD,
            fg=INK,
            bg=BG_PANEL
        ).pack(side="left")

        role_tag = tk.Frame(u_row, bg=EMERALD_LIGHT, padx=8, pady=3)
        role_tag.pack(side="right")
        tk.Label(
            role_tag,
            text=self.profile['role'].upper(),
            font=("Consolas", 8, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT
        ).pack()

        # Divided Full Name: First Name & Last Name in 2 columns
        name_row = tk.Frame(card, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 16))

        b_fn = tk.Frame(name_row, bg=BG_PANEL)
        b_fn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_fn, text="First name *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.fname_ent = self._entry(b_fn, self.first_name, field_key="fname")

        b_ln = tk.Frame(name_row, bg=BG_PANEL)
        b_ln.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_ln, text="Last name *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.lname_ent = self._entry(b_ln, self.last_name, field_key="lname")

        # Contact Number
        c_box = tk.Frame(card, bg=BG_PANEL)
        c_box.pack(fill="x", pady=(0, 8))
        tk.Label(c_box, text="Contact number *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.contact_ent = self._entry(c_box, self.profile.get('contact_no', ''), is_phone=True, field_key="contact")

        # Guidance Note
        note_box = tk.Frame(card, bg=BG_HOVER, padx=14, pady=10, highlightthickness=1, highlightbackground=LINE)
        note_box.pack(fill="x", pady=(14, 0))
        tk.Label(
            note_box,
            text="Primary contact telephone used for bench diagnostics alerts and release verifications.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG_HOVER,
            wraplength=460,
            justify="left"
        ).pack(anchor="w")

    def _build_security_tab(self):
        self.tab_security = tk.Frame(self.content_container, bg=BG)

        card = tk.Frame(self.tab_security, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=18)
        card.pack(fill="both", expand=True)

        # Security Guidance Note Box
        tip_box = tk.Frame(card, bg=BG_HOVER, padx=16, pady=12, highlightthickness=1, highlightbackground=LINE)
        tip_box.pack(fill="x", pady=(0, 16))

        tk.Label(
            tip_box,
            text="Credentials & Password Security",
            font=FONT_SMALL_BOLD,
            fg=INK,
            bg=BG_HOVER
        ).pack(anchor="w")

        tk.Label(
            tip_box,
            text="Username and registered email can both be used to sign in. Leave password fields blank if not changing your current password.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG_HOVER,
            wraplength=490,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Username (readonly) & Email in 2 columns
        id_row = tk.Frame(card, bg=BG_PANEL)
        id_row.pack(fill="x", pady=(0, 16))

        b_un = tk.Frame(id_row, bg=BG_PANEL)
        b_un.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_un, text="Username", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.user_ent = self._entry(b_un, self.profile.get('username', ''), is_readonly=True)

        b_em = tk.Frame(id_row, bg=BG_PANEL)
        b_em.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_em, text="Email address *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.email_ent = self._entry(b_em, self.profile.get('email', ''), field_key="email")

        # Section Subheader: Password
        pwd_hdr = tk.Frame(card, bg=BG_PANEL)
        pwd_hdr.pack(fill="x", pady=(2, 10))

        tk.Label(
            pwd_hdr,
            text="Change Password",
            font=FONT_SMALL_BOLD,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            pwd_hdr,
            text="Verify your identity with current password, then specify your new 8+ character password.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(1, 0))

        # Current Password
        c_pwd_box = tk.Frame(card, bg=BG_PANEL)
        c_pwd_box.pack(fill="x", pady=(0, 12))
        tk.Label(c_pwd_box, text="Current password (required to change password)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.curr_pwd_ent = self._entry(c_pwd_box, is_password=True, with_toggle=True, field_key="curr_pwd")

        # New Password and Confirm Password in 2 columns
        pwd_row = tk.Frame(card, bg=BG_PANEL)
        pwd_row.pack(fill="x", pady=(0, 4))

        b_np = tk.Frame(pwd_row, bg=BG_PANEL)
        b_np.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_np, text="New password (min 8 chars)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.new_pwd_ent = self._entry(b_np, is_password=True, with_toggle=True, field_key="new_pwd")

        b_cp = tk.Frame(pwd_row, bg=BG_PANEL)
        b_cp.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_cp, text="Confirm new password", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.conf_pwd_ent = self._entry(b_cp, is_password=True, with_toggle=True, field_key="conf_pwd")

    def _build_address_tab(self):
        self.tab_address = tk.Frame(self.content_container, bg=BG)

        card = tk.Frame(self.tab_address, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=18)
        card.pack(fill="both", expand=True)

        # Address guidance tip box
        tip_box = tk.Frame(card, bg=BG_HOVER, padx=14, pady=10, highlightthickness=1, highlightbackground=LINE)
        tip_box.pack(fill="x", pady=(0, 16))

        tk.Label(
            tip_box,
            text="Workshop / Delivery Address",
            font=FONT_SMALL_BOLD,
            fg=INK,
            bg=BG_HOVER
        ).pack(anchor="w")

        tk.Label(
            tip_box,
            text="Standard address details used for bench drop-off, courier returns, and component delivery.",
            font=("Segoe UI", 8),
            fg=MUTED,
            bg=BG_HOVER,
            wraplength=460,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # Street Address
        b_st = tk.Frame(card, bg=BG_PANEL)
        b_st.pack(fill="x", pady=(0, 12))
        tk.Label(b_st, text="Street address *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.street_ent = self._entry(b_st, self.addr_components.get('street', ''), field_key="street")

        # Apartment / Suite / Unit (Optional)
        b_un = tk.Frame(card, bg=BG_PANEL)
        b_un.pack(fill="x", pady=(0, 12))
        tk.Label(b_un, text="Apartment, suite, unit (optional)", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.unit_ent = self._entry(b_un, self.addr_components.get('unit', ''))

        # City & State / Province row
        cs_row = tk.Frame(card, bg=BG_PANEL)
        cs_row.pack(fill="x", pady=(0, 12))

        b_city = tk.Frame(cs_row, bg=BG_PANEL)
        b_city.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(b_city, text="City *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.city_ent = self._entry(b_city, self.addr_components.get('city', ''), field_key="city")

        b_state = tk.Frame(cs_row, bg=BG_PANEL)
        b_state.pack(side="right", fill="x", expand=True, padx=(8, 0))
        tk.Label(b_state, text="State / Province *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.state_ent = self._entry(b_state, self.addr_components.get('state', ''), field_key="state")

        # Postal Code / ZIP
        b_zip = tk.Frame(card, bg=BG_PANEL)
        b_zip.pack(fill="x", pady=(0, 4))
        tk.Label(b_zip, text="Postal code / ZIP *", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        self.zip_ent = self._entry(b_zip, self.addr_components.get('postal_code', ''), field_key="zip")

    def _switch_tab(self, tab_key):
        self.active_tab = tab_key

        # Update pill button appearances
        for k, btn in self.tab_buttons.items():
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

        # Show selected tab
        self.tab_personal.pack_forget()
        self.tab_security.pack_forget()
        self.tab_address.pack_forget()

        if tab_key == "personal":
            self.tab_personal.pack(fill="both", expand=True)
        elif tab_key == "security":
            self.tab_security.pack(fill="both", expand=True)
        elif tab_key == "address":
            self.tab_address.pack(fill="both", expand=True)

    def _save(self):
        self._clear_all_field_errors()
        fname = self.fname_ent.get().strip()
        lname = self.lname_ent.get().strip()
        contact_no = self.contact_ent.get().strip()

        email = self.email_ent.get().strip()
        curr_pwd = self.curr_pwd_ent.get().strip()
        new_pwd = self.new_pwd_ent.get().strip()
        conf_pwd = self.conf_pwd_ent.get().strip()

        street = self.street_ent.get().strip()
        unit = self.unit_ent.get().strip()
        city = self.city_ent.get().strip()
        state = self.state_ent.get().strip()
        zip_code = self.zip_ent.get().strip()

        # Step 1: Personal validation
        if not fname:
            self._switch_tab("personal")
            self._show_field_error("fname", "First name is required.")
            self.fname_ent.focus_set()
            return

        if not contact_no:
            self._switch_tab("personal")
            self._show_field_error("contact", "Contact number is required.")
            self.contact_ent.focus_set()
            return
        elif any(c.isalpha() for c in contact_no):
            self._switch_tab("personal")
            self._show_field_error("contact", "Contact number cannot contain letters.")
            self.contact_ent.focus_set()
            return
        else:
            try:
                valid_contact(contact_no, "Contact number")
            except ValidationError as ve:
                self._switch_tab("personal")
                self._show_field_error("contact", str(ve))
                self.contact_ent.focus_set()
                return

        # Step 2: Security validation
        if not email:
            self._switch_tab("security")
            self._show_field_error("email", "Email address is required.")
            self.email_ent.focus_set()
            return
        elif "@" not in email or "." not in email:
            self._switch_tab("security")
            self._show_field_error("email", "Please enter a valid email address.")
            self.email_ent.focus_set()
            return

        # If user entered any password field, validate
        if new_pwd or curr_pwd or conf_pwd:
            if not curr_pwd:
                self._switch_tab("security")
                self._show_field_error("curr_pwd", "Current password is required to change password.")
                self.curr_pwd_ent.focus_set()
                return
            if not new_pwd:
                self._switch_tab("security")
                self._show_field_error("new_pwd", "New password is required.")
                self.new_pwd_ent.focus_set()
                return
            if len(new_pwd) < 8:
                self._switch_tab("security")
                self._show_field_error("new_pwd", "New password must be at least 8 characters long.")
                self.new_pwd_ent.focus_set()
                return
            if new_pwd != conf_pwd:
                self._switch_tab("security")
                self._show_field_error("conf_pwd", "New passwords do not match.")
                self.conf_pwd_ent.focus_set()
                return

        # Step 3: Address validation
        if not street:
            self._switch_tab("address")
            self._show_field_error("street", "Street address is required.")
            self.street_ent.focus_set()
            return
        if not city:
            self._switch_tab("address")
            self._show_field_error("city", "City is required.")
            self.city_ent.focus_set()
            return
        if not state:
            self._switch_tab("address")
            self._show_field_error("state", "State / Province is required.")
            self.state_ent.focus_set()
            return
        if not zip_code:
            self._switch_tab("address")
            self._show_field_error("zip", "Postal code / ZIP is required.")
            self.zip_ent.focus_set()
            return

        new_name = compose_full_name(fname, lname)
        new_addr = compose_address(street, unit, city, state, zip_code)

        try:
            updated = update_profile(
                user_id=self.profile['user_id'],
                full_name=new_name,
                contact_no=contact_no,
                email=email,
                address=new_addr,
                current_password=curr_pwd if new_pwd else None,
                new_password=new_pwd if new_pwd else None,
                confirm_password=conf_pwd if new_pwd else None,
                username=self.profile.get('username')
            )

            # Update session user
            self.current_user['full_name'] = updated['full_name']

            if self.on_profile_updated_callback:
                self.on_profile_updated_callback(self.current_user)

            messagebox.showinfo(
                "Profile Updated",
                "Your account settings and profile details have been saved.",
                parent=self
            )
            self.destroy()

        except (ValidationError, RuleError) as err:
            err_msg = str(err)
            if "current password" in err_msg.lower() or "password" in err_msg.lower():
                self._switch_tab("security")
                if "current" in err_msg.lower():
                    self._show_field_error("curr_pwd", err_msg)
                    self.curr_pwd_ent.focus_set()
                else:
                    self._show_field_error("new_pwd", err_msg)
                    self.new_pwd_ent.focus_set()
            elif "email" in err_msg.lower():
                self._switch_tab("security")
                self._show_field_error("email", err_msg)
                self.email_ent.focus_set()
            elif "contact" in err_msg.lower():
                self._switch_tab("personal")
                self._show_field_error("contact", err_msg)
                self.contact_ent.focus_set()
            else:
                self._switch_tab("personal")
                self._show_field_error("fname", err_msg)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}", parent=self)
