import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, LINE_BRIGHT, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, EMERALD_LIGHT, RED,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.customers import (
    list_customers, search_customers, register_customer_account, edit_customer,
    delete_customer, customer_history, get_customer, reset_customer_account_password,
    update_customer_account_username, find_linked_user_for_customer
)
from logic.auth import (
    compose_full_name, compose_address, parse_address, split_full_name, can,
    deactivate_account, reactivate_account, account_status, can
)
from logic.jobs import status_map
from storage import get_rows
from errors import ValidationError
from utils import valid_contact, valid_email


class CustomersView(tk.Frame):
    """
    Customer Management Interface (FR-07 - FR-12).
    Features customer table, live search, account onboarding/edit modal, delete protection, and repair history.
    """
    def __init__(self, parent, acting_user, on_open_job_callback=None):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user
        self.on_open_job_callback = on_open_job_callback

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # Header Bar
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(title_box, text="Customer Registry", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Manage customer profiles, onboard client logins, and review historical device tickets.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        # Top Actions
        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        add_btn = primary_button(btn_box, "+ Register Customer", command=self._open_add_modal)
        add_btn.pack(side="left")

        # Search Bar Bar
        search_bar = tk.Frame(self, bg=BG, padx=24, pady=12)
        search_bar.pack(fill="x")

        s_box = tk.Frame(search_bar, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=8, pady=4)
        s_box.pack(side="left", fill="x", expand=True)

        tk.Label(s_box, text="Search Directory:", font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(side="left", padx=(4, 8))
        self.search_entry = tk.Entry(s_box, font=FONT_BODY, bg=BG_PANEL, fg=INK, bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._handle_search())

        clear_btn = secondary_button(search_bar, "Clear", command=self._clear_search, padx=10, pady=4)
        clear_btn.pack(side="left", padx=(8, 0))

        # Bottom Action Bar (Packed side="bottom" first to guarantee it is NEVER pushed off screen)
        bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=10, bd=0, highlightthickness=1, highlightbackground=LINE)
        bottom_bar.pack(fill="x", side="bottom")

        hist_btn = secondary_button(bottom_bar, "View Repair History", command=self._view_history)
        hist_btn.pack(side="left", padx=(0, 8))

        edit_btn = secondary_button(bottom_bar, "Edit Details", command=self._open_edit_modal)
        edit_btn.pack(side="left", padx=(0, 8))

        if can(self.acting_user['role'], 'deactivate_customers'):
            self.account_action_btn = danger_button(
                bottom_bar, "Deactivate Account", command=self._handle_account_status
            )
            self.account_action_btn.pack(side="left")

        # Main Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=20)
        table_wrap.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("customer_id", "username", "status", "name", "contact_no", "email", "address")
        heads = ("Customer ID", "Username", "Status", "Full Name", "Contact Number", "Email Address", "Address")
        widths = (110, 130, 110, 200, 150, 220, 260)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths, horizontal=True)
        self.table_frame.pack(fill="both", expand=True)

        # Double click to view history
        self.tree.bind("<Double-1>", lambda e: self._view_history())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_account_action())
        self._update_account_action()

    def refresh(self):
        """Reload customer table from storage, joining username from the users table."""
        query = self.search_entry.get().strip()
        rows = search_customers(query) if query else list_customers()

        # Enrich each customer row with their linked username (or '—' if walk-in)
        enriched = []
        for c in rows:
            enriched_row = dict(c)
            u = find_linked_user_for_customer(c)
            enriched_row['username'] = u.get('username') if u else '—'
            enriched_row['status'] = account_status(u['user_id']) if u else 'No account'
            enriched.append(enriched_row)

        cols = ("customer_id", "username", "status", "name", "contact_no", "email", "address")
        fill_table(self.tree, enriched, cols)
        self._update_account_action()

    def _update_account_action(self):
        if not hasattr(self, 'account_action_btn'):
            return
        customer = self._get_selected_customer(silent=True)
        linked_user = find_linked_user_for_customer(customer) if customer else None
        is_deactivated = linked_user and account_status(linked_user['user_id']) == 'Deactivated'
        self.account_action_btn.configure(
            text="Reactivate Account" if is_deactivated else "Deactivate Account"
        )

    def _handle_search(self):
        self.refresh()

    def _clear_search(self):
        self.search_entry.delete(0, "end")
        self.refresh()

    def _get_selected_customer(self, silent=False):
        sel = self.tree.selection()
        if not sel:
            if not silent:
                messagebox.showwarning("Selection Required", "Please select a customer from the table.")
            return None
        vals = self.tree.item(sel[0], "values")
        cid = vals[0]
        return get_customer(cid)

    def _open_add_modal(self):
        CustomerAccountFormModal(self, self.acting_user, on_save_callback=self.refresh)

    def _open_edit_modal(self):
        c = self._get_selected_customer()
        if c:
            CustomerFormModal(self, "Edit Customer", self.acting_user, customer=c, on_save_callback=self.refresh)

    @guard
    def _handle_delete(self):
        c = self._get_selected_customer()
        if not c:
            return
        cid = c['customer_id']
        name = c['name']

        if confirm("Confirm Deletion", f"Are you sure you want to delete customer {cid} ({name})?"):
            delete_customer(cid, self.acting_user)
            messagebox.showinfo("Deleted", f"Customer {cid} has been removed.")
            self.refresh()

    @guard
    def _handle_account_status(self):
        customer = self._get_selected_customer()
        if not customer:
            return
        linked_user = find_linked_user_for_customer(customer)
        if not linked_user:
            messagebox.showwarning("No Account", "This customer has no linked login account.")
            return
        is_deactivated = account_status(linked_user['user_id']) == 'Deactivated'
        action = "Reactivate" if is_deactivated else "Deactivate"
        if confirm("Confirm Account Status Change", f"{action} the login account '{linked_user['username']}'?"):
            if is_deactivated:
                reactivate_account(linked_user['user_id'], self.acting_user)
            else:
                deactivate_account(linked_user['user_id'], self.acting_user)
            messagebox.showinfo("Account Updated", f"The customer account has been {action.lower()}d.")
            self.refresh()

    def _view_history(self):
        c = self._get_selected_customer()
        if c:
            CustomerHistoryModal(self, c, self.on_open_job_callback)


class CustomerAccountFormModal(tk.Toplevel):
    """
    Customer onboarding modal for authorized roles (Admin/Staff).

    Mirrors the public registration flow: creates a Customer login account
    (username/password) plus the linked customer profile and address.
    """
    def __init__(self, parent, acting_user, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.on_save_callback = on_save_callback

        self.title("Register Customer Account")
        self.configure(bg=BG)
        self.resizable(False, False)

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

        self.field_errors = {}
        self.field_wrappers = {}
        self.active_tab = "personal"
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_PANEL, padx=28, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text="CUSTOMER ONBOARDING",
            font=("Consolas", 8, "bold"),
            fg=EMERALD,
            bg=EMERALD_LIGHT,
            padx=8,
            pady=3
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(hdr, text="Register Customer Account", font=("Segoe UI", 16, "bold"), fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            hdr,
            text="Creates a client login and profile exactly like self-registration.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # Segmented tab bar
        tab_section = tk.Frame(self, bg=BG, padx=28)
        tab_section.pack(fill="x", pady=(12, 10))

        self.tab_bar = tk.Frame(tab_section, bg="#f1f5f9", padx=4, pady=4, bd=0, highlightthickness=1, highlightbackground=LINE)
        self.tab_bar.pack(fill="x")

        self.tab_buttons = {}
        for tab_key, label_text in (("personal", "1. Personal"), ("security", "2. Security"), ("address", "3. Address")):
            btn = tk.Button(
                self.tab_bar,
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

        # Footer actions
        bot = tk.Frame(self, bg=BG_PANEL, padx=28, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(side="bottom", fill="x")

        primary_button(bot, "Create Customer Account", command=self._save, padx=22, pady=8).pack(side="right", padx=(12, 0))
        secondary_button(bot, "Cancel", command=self.destroy, padx=18, pady=8).pack(side="right")

        # Content area
        self.content_container = tk.Frame(self, bg=BG, padx=28)
        self.content_container.pack(side="top", fill="both", expand=True, pady=(0, 10))

        self._build_personal_tab()
        self._build_security_tab()
        self._build_address_tab()

        for key, ent in (
            ("fname", self.fname_ent),
            ("lname", self.lname_ent),
            ("contact", self.contact_ent),
            ("uname", self.uname_ent),
            ("email", self.email_ent),
            ("pwd", self.pwd_ent),
            ("cpwd", self.cpwd_ent),
            ("street", self.street_ent),
            ("unit", self.unit_ent),
            ("city", self.city_ent),
            ("state", self.state_ent),
            ("zip", self.zip_ent),
        ):
            if key not in ("contact", "zip"):
                ent.bind("<KeyRelease>", lambda e, k=key: self._clear_field_error(k))

        self._switch_tab("personal")

    def _build_personal_tab(self):
        self.tab_personal = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_personal, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Personal information", font=FONT_BODY_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        name_row = tk.Frame(card, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 14))

        b_fn = tk.Frame(name_row, bg=BG_PANEL)
        b_fn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.fname_ent = self._field(b_fn, "First name *", "fname")

        b_ln = tk.Frame(name_row, bg=BG_PANEL)
        b_ln.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.lname_ent = self._field(b_ln, "Last name *", "lname")

        b_phone = tk.Frame(card, bg=BG_PANEL)
        b_phone.pack(fill="x")
        self.contact_ent = self._field(b_phone, "Contact number * (e.g. 0917-123-4567)", "contact", phone=True)

    def _build_security_tab(self):
        self.tab_security = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_security, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Login credentials", font=FONT_BODY_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        id_row = tk.Frame(card, bg=BG_PANEL)
        id_row.pack(fill="x", pady=(0, 14))

        b_un = tk.Frame(id_row, bg=BG_PANEL)
        b_un.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.uname_ent = self._field(b_un, "Username * (3-20 chars, no spaces)", "uname")

        b_em = tk.Frame(id_row, bg=BG_PANEL)
        b_em.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.email_ent = self._field(b_em, "Email address *", "email")

        pwd_row = tk.Frame(card, bg=BG_PANEL)
        pwd_row.pack(fill="x", pady=(0, 10))

        b_p1 = tk.Frame(pwd_row, bg=BG_PANEL)
        b_p1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.pwd_ent = self._field(b_p1, "Password * (min 8 characters)", "pwd", show="*", password=True)

        b_p2 = tk.Frame(pwd_row, bg=BG_PANEL)
        b_p2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.cpwd_ent = self._field(b_p2, "Confirm password *", "cpwd", show="*", password=True)

        tk.Label(
            card,
            text="The customer can sign in immediately with this username or email.",
            font=("Segoe UI", 8),
            fg=DIM,
            bg=BG_PANEL,
            wraplength=460,
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

    def _build_address_tab(self):
        self.tab_address = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_address, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=24, pady=18)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Address details", font=FONT_BODY_BOLD, fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        b_st = tk.Frame(card, bg=BG_PANEL)
        b_st.pack(fill="x", pady=(0, 12))
        self.street_ent = self._field(b_st, "Street address *", "street")

        b_unit = tk.Frame(card, bg=BG_PANEL)
        b_unit.pack(fill="x", pady=(0, 12))
        self.unit_ent = self._field(b_unit, "Apartment, suite, unit (optional)", "unit")

        cs_row = tk.Frame(card, bg=BG_PANEL)
        cs_row.pack(fill="x", pady=(0, 12))

        b_city = tk.Frame(cs_row, bg=BG_PANEL)
        b_city.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.city_ent = self._field(b_city, "City *", "city")

        b_state = tk.Frame(cs_row, bg=BG_PANEL)
        b_state.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.state_ent = self._field(b_state, "State / Province *", "state")

        b_zip = tk.Frame(card, bg=BG_PANEL)
        b_zip.pack(fill="x")
        self.zip_ent = self._field(b_zip, "Postal code / ZIP * (4 digits)", "zip", postal=True)

    def _field(self, parent, label_text, field_key, show="", phone=False, postal=False, password=False):
        tk.Label(parent, text=label_text, font=FONT_SMALL_BOLD, fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))

        wrap = tk.Frame(parent, bg=BG_INPUT, bd=0, highlightthickness=1, highlightbackground=LINE)
        wrap.pack(fill="x")

        extra = {}
        if show:
            extra["show"] = show
        if phone:
            extra["validate"] = "key"
            extra["validatecommand"] = (
                self.register(lambda act, p, char: self._on_phone_char_validate(field_key, act, p, char)),
                '%d', '%P', '%S'
            )
        if postal:
            extra["validate"] = "key"
            extra["validatecommand"] = (
                self.register(lambda act, p, char: self._on_postal_char_validate(field_key, act, p, char)),
                '%d', '%P', '%S'
            )

        ent = tk.Entry(wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, **extra)
        ent.pack(side="left", fill="x", expand=True, ipady=7, padx=10)

        if password:
            toggle = tk.Label(wrap, text="Show", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=BG_INPUT, cursor="hand2", padx=10)
            toggle.pack(side="right")

            def _toggle(e=ent, t=toggle):
                if e.cget("show") == "*":
                    e.configure(show="")
                    t.configure(text="Hide", fg=EMERALD)
                else:
                    e.configure(show="*")
                    t.configure(text="Show", fg=MUTED)

            toggle.bind("<Button-1>", lambda ev: _toggle())

        self.field_wrappers[field_key] = wrap
        self.field_errors[field_key] = tk.Label(parent, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w")

        ent.bind("<FocusIn>", lambda e, w=wrap: w.configure(highlightbackground=EMERALD, highlightcolor=EMERALD))
        ent.bind("<FocusOut>", lambda e, k=field_key, w=wrap: w.configure(
            highlightbackground=RED if self.field_errors.get(k) and self.field_errors[k].winfo_ismapped() else LINE
        ))
        return ent

    def _on_phone_char_validate(self, key, action, proposed, char):
        if action == '1':
            if any(c.isalpha() for c in char):
                self._show_field_error(key, "Contact number cannot contain letters.")
                return False
            if sum(c.isdigit() for c in proposed) > 11:
                self._show_field_error(key, "Contact number cannot exceed 11 digits.")
                return False
        return True

    def _on_postal_char_validate(self, key, action, proposed, char):
        if action == '1' and (not char.isdigit() or len(proposed) > 4):
            self._show_field_error(key, "Postal code must contain exactly 4 digits.")
            return False
        return True

    def _show_field_error(self, key, message):
        lbl = self.field_errors.get(key)
        if lbl is not None:
            lbl.configure(text=message)
            if not lbl.winfo_ismapped():
                lbl.pack(anchor="w", pady=(2, 0))
        wrap = self.field_wrappers.get(key)
        if wrap is not None:
            wrap.configure(highlightbackground=RED, highlightcolor=RED)

    def _clear_field_error(self, key):
        lbl = self.field_errors.get(key)
        if lbl is not None:
            lbl.configure(text="")
            lbl.pack_forget()
        wrap = self.field_wrappers.get(key)
        if wrap is not None:
            wrap.configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _clear_all_field_errors(self):
        for key in list(self.field_errors.keys()):
            self._clear_field_error(key)

    def _switch_tab(self, tab_key):
        self.active_tab = tab_key
        for k, btn in self.tab_buttons.items():
            if k == tab_key:
                btn.configure(bg="#ffffff", fg=INK, highlightthickness=1, highlightbackground=LINE)
            else:
                btn.configure(bg="#f1f5f9", fg=MUTED, highlightthickness=0)

        self.tab_personal.pack_forget()
        self.tab_security.pack_forget()
        self.tab_address.pack_forget()

        if tab_key == "personal":
            self.tab_personal.pack(fill="both", expand=True)
            self.fname_ent.focus_set()
        elif tab_key == "security":
            self.tab_security.pack(fill="both", expand=True)
            self.uname_ent.focus_set()
        elif tab_key == "address":
            self.tab_address.pack(fill="both", expand=True)
            self.street_ent.focus_set()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    @guard
    def _save(self):
        self._clear_all_field_errors()

        fname = self.fname_ent.get().strip()
        lname = self.lname_ent.get().strip()
        phone = self.contact_ent.get().strip()

        uname = self.uname_ent.get().strip()
        email = self.email_ent.get().strip()
        pwd = self.pwd_ent.get()
        cpwd = self.cpwd_ent.get()

        street = self.street_ent.get().strip()
        unit = self.unit_ent.get().strip()
        city = self.city_ent.get().strip()
        state = self.state_ent.get().strip()
        zip_code = self.zip_ent.get().strip()

        full_name = compose_full_name(fname, lname)

        # --- Personal ---
        if not fname:
            self._switch_tab("personal")
            self._show_field_error("fname", "First name is required.")
            self.fname_ent.focus_set()
            return
        if not lname:
            self._switch_tab("personal")
            self._show_field_error("lname", "Last name is required.")
            self.lname_ent.focus_set()
            return
        if not phone:
            self._switch_tab("personal")
            self._show_field_error("contact", "Contact number is required.")
            self.contact_ent.focus_set()
            return
        try:
            valid_contact(phone, "Contact number")
        except ValidationError as err:
            self._switch_tab("personal")
            self._show_field_error("contact", str(err))
            self.contact_ent.focus_set()
            return

        # --- Security ---
        if not uname:
            self._switch_tab("security")
            self._show_field_error("uname", "Username is required.")
            self.uname_ent.focus_set()
            return
        if " " in uname or len(uname) < 3 or len(uname) > 20:
            self._switch_tab("security")
            self._show_field_error("uname", "Username must be 3-20 characters with no spaces.")
            self.uname_ent.focus_set()
            return
        if any(u['username'].lower() == uname.lower() for u in get_rows('users')):
            self._switch_tab("security")
            self._show_field_error("uname", f"Username '{uname}' is already taken.")
            self.uname_ent.focus_set()
            return

        if not email:
            self._switch_tab("security")
            self._show_field_error("email", "Email address is required.")
            self.email_ent.focus_set()
            return
        try:
            email_clean = valid_email(email, "Email address")
        except ValidationError as err:
            self._switch_tab("security")
            self._show_field_error("email", str(err))
            self.email_ent.focus_set()
            return

        owner = next(
            (c for c in list_customers()
             if c.get('email', '').strip().lower() == email_clean.lower()),
            None
        )
        if owner and owner.get('name', '').strip().lower() != full_name.strip().lower():
            self._switch_tab("security")
            self._show_field_error("email", "Email address is already registered.")
            self.email_ent.focus_set()
            return

        if not pwd:
            self._switch_tab("security")
            self._show_field_error("pwd", "Password is required.")
            self.pwd_ent.focus_set()
            return
        if len(pwd) < 8:
            self._switch_tab("security")
            self._show_field_error("pwd", "Password must be at least 8 characters.")
            self.pwd_ent.focus_set()
            return
        if not cpwd:
            self._switch_tab("security")
            self._show_field_error("cpwd", "Please confirm the password.")
            self.cpwd_ent.focus_set()
            return
        if pwd != cpwd:
            self._switch_tab("security")
            self._show_field_error("cpwd", "Passwords do not match.")
            self.cpwd_ent.focus_set()
            return

        # --- Address ---
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
        if not zip_code.isdigit() or len(zip_code) != 4:
            self._switch_tab("address")
            self._show_field_error("zip", "Postal code must contain exactly 4 digits.")
            self.zip_ent.focus_set()
            return

        full_name = compose_full_name(fname, lname)
        address = compose_address(street, unit, city, state, zip_code)

        new_user = register_customer_account(
            username=uname,
            password=pwd,
            confirm_password=cpwd,
            full_name=full_name,
            contact_no=phone,
            email=email,
            address=address,
            acting_user=self.acting_user
        )

        messagebox.showinfo(
            "Customer Account Created",
            f"Customer account {new_user['user_id']} created for {full_name}.\n\n"
            f"Login username: {new_user['username']}\n"
            f"Role: {new_user['role']}",
            parent=self
        )

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()


class CustomerFormModal(tk.Toplevel):
    """
    Modal dialog for editing an existing customer profile.

    Identical tab-based layout to CustomerAccountFormModal (registration form):
      Tab 1 – Personal  : First name, Last name, Contact number
      Tab 2 – Account   : Username (read-only badge), Email address
      Tab 3 – Address   : Street, Unit, City, State/Province, Postal code
    """
    def __init__(self, parent, title_text, acting_user, customer=None, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.customer = customer
        self.on_save_callback = on_save_callback

        self.title(title_text)
        self.configure(bg=BG)
        self.resizable(False, False)

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

        self.field_errors = {}
        self.field_wrappers = {}
        self.active_tab = "personal"

        # Resolve linked user for account editing
        self.linked_user = find_linked_user_for_customer(self.customer) if self.customer else None
        self._linked_username = self.linked_user.get('username') if self.linked_user else '—'
        self.can_manage_accounts = can(acting_user['role'], 'manage_customer_accounts')

        # Parse existing address into components
        self._addr_parts = parse_address(customer['address'] if customer else '')

        self._build_ui()
        self._populate()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_PANEL, padx=28, pady=14, bd=0,
                       highlightthickness=1, highlightbackground=LINE)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text="EDIT CUSTOMER PROFILE",
            font=("Consolas", 8, "bold"), fg=EMERALD, bg=EMERALD_LIGHT,
            padx=8, pady=3
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(hdr, text="Edit Customer", font=("Segoe UI", 16, "bold"),
                 fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            hdr,
            text="Update the customer's personal details, account email, and address.",
            font=FONT_SMALL, fg=MUTED, bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        # ── Segmented tab bar ────────────────────────────────────────────
        tab_section = tk.Frame(self, bg=BG, padx=28)
        tab_section.pack(fill="x", pady=(12, 10))

        self.tab_bar = tk.Frame(tab_section, bg="#f1f5f9", padx=4, pady=4,
                                bd=0, highlightthickness=1, highlightbackground=LINE)
        self.tab_bar.pack(fill="x")

        self.tab_buttons = {}
        for tab_key, label_text in (
            ("personal", "1. Personal"),
            ("account",  "2. Account"),
            ("address",  "3. Address"),
        ):
            btn = tk.Button(
                self.tab_bar, text=label_text, font=FONT_SMALL_BOLD,
                bg="#f1f5f9", fg=MUTED,
                activebackground="#ffffff", activeforeground=INK,
                bd=0, padx=14, pady=8, cursor="hand2",
                command=lambda k=tab_key: self._switch_tab(k)
            )
            btn.pack(side="left", fill="x", expand=True, padx=2)
            self.tab_buttons[tab_key] = btn

        # ── Footer (packed before content so it's never pushed off) ─────
        bot = tk.Frame(self, bg=BG_PANEL, padx=28, pady=12, bd=0,
                       highlightthickness=1, highlightbackground=LINE)
        bot.pack(side="bottom", fill="x")

        primary_button(bot, "Save Customer Profile", command=self._save,
                       padx=22, pady=8).pack(side="right", padx=(12, 0))
        secondary_button(bot, "Cancel", command=self.destroy,
                         padx=18, pady=8).pack(side="right")

        # ── Content area ────────────────────────────────────────────────
        self.content_container = tk.Frame(self, bg=BG, padx=28)
        self.content_container.pack(side="top", fill="both", expand=True, pady=(0, 10))

        self._build_personal_tab()
        self._build_account_tab()
        self._build_address_tab()

        # Bind key-release clear for text-only fields
        for key, ent in (
            ("fname",  self.fname_ent),
            ("lname",  self.lname_ent),
            ("uname",  self.uname_ent),
            ("email",  self.email_ent),
            ("pwd",    self.pwd_ent),
            ("cpwd",   self.cpwd_ent),
            ("street", self.street_ent),
            ("unit",   self.unit_ent),
            ("city",   self.city_ent),
            ("state",  self.state_ent),
        ):
            ent.bind("<KeyRelease>", lambda e, k=key: self._clear_field_error(k))

        self._switch_tab("personal")

    # ── Tab builders ────────────────────────────────────────────────────

    def _build_personal_tab(self):
        self.tab_personal = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_personal, bg=BG_PANEL, bd=0,
                        highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Personal information", font=FONT_BODY_BOLD,
                 fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        name_row = tk.Frame(card, bg=BG_PANEL)
        name_row.pack(fill="x", pady=(0, 14))

        b_fn = tk.Frame(name_row, bg=BG_PANEL)
        b_fn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.fname_ent = self._field(b_fn, "First name *", "fname")

        b_ln = tk.Frame(name_row, bg=BG_PANEL)
        b_ln.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.lname_ent = self._field(b_ln, "Last name *", "lname")

        b_phone = tk.Frame(card, bg=BG_PANEL)
        b_phone.pack(fill="x")
        self.contact_ent = self._field(
            b_phone, "Contact number * (e.g. 0917-123-4567)", "contact", phone=True
        )

    def _build_account_tab(self):
        self.tab_account = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_account, bg=BG_PANEL, bd=0,
                        highlightthickness=1, highlightbackground=LINE, padx=24, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Account information", font=FONT_BODY_BOLD,
                 fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        id_row = tk.Frame(card, bg=BG_PANEL)
        id_row.pack(fill="x", pady=(0, 12))

        b_un = tk.Frame(id_row, bg=BG_PANEL)
        b_un.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.uname_ent = self._field(b_un, "Username * (3-20 chars, no spaces)", "uname")

        b_em = tk.Frame(id_row, bg=BG_PANEL)
        b_em.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.email_ent = self._field(b_em, "Email address *", "email")

        if self._linked_username == '—':
            tk.Label(
                card,
                text="This customer has no linked login account (walk-in).\n"
                     "Use + Register Customer to create one.",
                font=("Segoe UI", 8), fg=MUTED, bg=BG_PANEL,
                wraplength=460, justify="left"
            ).pack(anchor="w", pady=(0, 10))

        # Divider
        sep = tk.Frame(card, bg=LINE, height=1)
        sep.pack(fill="x", pady=(4, 14))

        tk.Label(card, text="Reset Password (optional)", font=FONT_BODY_BOLD,
                 fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))
        tk.Label(
            card,
            text="Leave blank to keep the current password unchanged.",
            font=("Segoe UI", 8), fg=DIM, bg=BG_PANEL,
            wraplength=460, justify="left"
        ).pack(anchor="w", pady=(0, 10))

        pwd_row = tk.Frame(card, bg=BG_PANEL)
        pwd_row.pack(fill="x", pady=(0, 10))

        b_p1 = tk.Frame(pwd_row, bg=BG_PANEL)
        b_p1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.pwd_ent = self._field(b_p1, "New password (min 8 characters)", "pwd",
                                   show="*", password=True)

        b_p2 = tk.Frame(pwd_row, bg=BG_PANEL)
        b_p2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.cpwd_ent = self._field(b_p2, "Confirm new password", "cpwd",
                                    show="*", password=True)

        if self._linked_username == '—' or not self.can_manage_accounts:
            # Disable account fields for walk-ins (no linked account)
            self.uname_ent.configure(state="disabled", bg="#f1f5f9")
            self.pwd_ent.configure(state="disabled", bg="#f1f5f9")
            self.cpwd_ent.configure(state="disabled", bg="#f1f5f9")
            if self._linked_username != '—':
                tk.Label(
                    card,
                    text="Only Admin can change usernames or reset customer passwords.",
                    font=("Segoe UI", 8), fg=MUTED, bg=BG_PANEL,
                    wraplength=460, justify="left"
                ).pack(anchor="w", pady=(8, 0))

    def _build_address_tab(self):
        self.tab_address = tk.Frame(self.content_container, bg=BG)
        card = tk.Frame(self.tab_address, bg=BG_PANEL, bd=0,
                        highlightthickness=1, highlightbackground=LINE, padx=24, pady=18)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="Address details", font=FONT_BODY_BOLD,
                 fg=INK, bg=BG_PANEL).pack(anchor="w", pady=(0, 14))

        b_st = tk.Frame(card, bg=BG_PANEL)
        b_st.pack(fill="x", pady=(0, 12))
        self.street_ent = self._field(b_st, "Street address *", "street")

        b_unit = tk.Frame(card, bg=BG_PANEL)
        b_unit.pack(fill="x", pady=(0, 12))
        self.unit_ent = self._field(b_unit, "Apartment, suite, unit (optional)", "unit")

        cs_row = tk.Frame(card, bg=BG_PANEL)
        cs_row.pack(fill="x", pady=(0, 12))

        b_city = tk.Frame(cs_row, bg=BG_PANEL)
        b_city.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.city_ent = self._field(b_city, "City *", "city")

        b_state = tk.Frame(cs_row, bg=BG_PANEL)
        b_state.pack(side="right", fill="x", expand=True, padx=(8, 0))
        self.state_ent = self._field(b_state, "State / Province *", "state")

        b_zip = tk.Frame(card, bg=BG_PANEL)
        b_zip.pack(fill="x")
        self.zip_ent = self._field(b_zip, "Postal code / ZIP * (4 digits)", "zip", postal=True)

    # ── Tab switcher ────────────────────────────────────────────────────

    def _switch_tab(self, tab_key):
        self.active_tab = tab_key
        for k, btn in self.tab_buttons.items():
            if k == tab_key:
                btn.configure(bg="#ffffff", fg=INK,
                              highlightthickness=1, highlightbackground=LINE)
            else:
                btn.configure(bg="#f1f5f9", fg=MUTED, highlightthickness=0)

        self.tab_personal.pack_forget()
        self.tab_account.pack_forget()
        self.tab_address.pack_forget()

        if tab_key == "personal":
            self.tab_personal.pack(fill="both", expand=True)
            self.fname_ent.focus_set()
        elif tab_key == "account":
            self.tab_account.pack(fill="both", expand=True)
            self.email_ent.focus_set()
        elif tab_key == "address":
            self.tab_address.pack(fill="both", expand=True)
            self.street_ent.focus_set()

    # ── Populate existing data ───────────────────────────────────────────

    def _populate(self):
        """Pre-fill entries from the existing customer record."""
        if not self.customer:
            return
        fname, lname = split_full_name(self.customer.get('name', ''))
        self.fname_ent.insert(0, fname)
        self.lname_ent.insert(0, lname)
        self.contact_ent.insert(0, self.customer.get('contact_no', ''))

        if self._linked_username != '—':
            self.uname_ent.insert(0, self._linked_username)
        else:
            self.uname_ent.insert(0, "—")

        self.email_ent.insert(0, self.customer.get('email', ''))
        self.street_ent.insert(0, self._addr_parts.get('street', ''))
        self.unit_ent.insert(0, self._addr_parts.get('unit', ''))
        self.city_ent.insert(0, self._addr_parts.get('city', ''))
        self.state_ent.insert(0, self._addr_parts.get('state', ''))
        self.zip_ent.insert(0, self._addr_parts.get('postal_code', ''))

    # ------------------------------------------------------------------
    # Field helpers (identical style to CustomerAccountFormModal)
    # ------------------------------------------------------------------
    def _field(self, parent, label_text, field_key, show="", phone=False, postal=False, password=False):
        tk.Label(parent, text=label_text, font=FONT_SMALL_BOLD,
                 fg=MUTED, bg=BG_PANEL).pack(anchor="w", pady=(0, 4))

        wrap = tk.Frame(parent, bg=BG_INPUT, bd=0,
                        highlightthickness=1, highlightbackground=LINE)
        wrap.pack(fill="x")

        extra = {}
        if show:
            extra["show"] = show
        if phone:
            extra["validate"] = "key"
            extra["validatecommand"] = (
                self.register(
                    lambda act, p, char: self._on_phone_validate(field_key, act, p, char)
                ),
                '%d', '%P', '%S'
            )
        if postal:
            extra["validate"] = "key"
            extra["validatecommand"] = (
                self.register(
                    lambda act, p, char: self._on_postal_validate(field_key, act, p, char)
                ),
                '%d', '%P', '%S'
            )

        ent = tk.Entry(wrap, font=FONT_BODY, bg=BG_INPUT, fg=INK, bd=0, **extra)
        ent.pack(side="left", fill="x", expand=True, ipady=7, padx=10)

        if password:
            toggle = tk.Label(wrap, text="Show", font=("Segoe UI", 8, "bold"),
                              fg=MUTED, bg=BG_INPUT, cursor="hand2", padx=10)
            toggle.pack(side="right")

            def _toggle(e=ent, t=toggle):
                if e.cget("show") == "*":
                    e.configure(show="")
                    t.configure(text="Hide", fg=EMERALD)
                else:
                    e.configure(show="*")
                    t.configure(text="Show", fg=MUTED)

            toggle.bind("<Button-1>", lambda ev: _toggle())

        self.field_wrappers[field_key] = wrap
        self.field_errors[field_key] = tk.Label(
            parent, text="", font=("Segoe UI", 8), fg=RED, bg=BG_PANEL, anchor="w"
        )

        ent.bind("<FocusIn>",
                 lambda e, w=wrap: w.configure(highlightbackground=EMERALD, highlightcolor=EMERALD))
        ent.bind("<FocusOut>", lambda e, k=field_key, w=wrap: w.configure(
            highlightbackground=RED
            if self.field_errors.get(k) and self.field_errors[k].winfo_ismapped()
            else LINE
        ))
        return ent

    def _on_phone_validate(self, key, action, proposed, char):
        if action == '1':
            if any(c.isalpha() for c in char):
                self._show_field_error(key, "Contact number cannot contain letters.")
                return False
            if sum(c.isdigit() for c in proposed) > 11:
                self._show_field_error(key, "Contact number cannot exceed 11 digits.")
                return False
        return True

    def _on_postal_validate(self, key, action, proposed, char):
        if action == '1' and (not char.isdigit() or len(proposed) > 4):
            self._show_field_error(key, "Postal code must contain exactly 4 digits.")
            return False
        return True

    def _show_field_error(self, key, message):
        lbl = self.field_errors.get(key)
        if lbl is not None:
            lbl.configure(text=message)
            if not lbl.winfo_ismapped():
                lbl.pack(anchor="w", pady=(2, 0))
        wrap = self.field_wrappers.get(key)
        if wrap is not None:
            wrap.configure(highlightbackground=RED, highlightcolor=RED)

    def _clear_field_error(self, key):
        lbl = self.field_errors.get(key)
        if lbl is not None:
            lbl.configure(text="")
            lbl.pack_forget()
        wrap = self.field_wrappers.get(key)
        if wrap is not None:
            wrap.configure(highlightbackground=LINE_BRIGHT, highlightcolor=EMERALD)

    def _clear_all_field_errors(self):
        for key in list(self.field_errors.keys()):
            self._clear_field_error(key)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    @guard
    def _save(self):
        if not self.customer:
            messagebox.showerror(
                "Not Available",
                "New customers must be onboarded with a login account. "
                "Please close this window and use + Register Customer.",
                parent=self
            )
            return

        self._clear_all_field_errors()

        fname    = self.fname_ent.get().strip()
        lname    = self.lname_ent.get().strip()
        contact  = self.contact_ent.get().strip()
        uname    = self.uname_ent.get().strip() if self._linked_username != '—' and self.can_manage_accounts else ''
        email    = self.email_ent.get().strip()
        new_pwd  = self.pwd_ent.get().strip() if self._linked_username != '—' and self.can_manage_accounts else ''
        conf_pwd = self.cpwd_ent.get().strip() if self._linked_username != '—' and self.can_manage_accounts else ''
        do_password_reset = bool(new_pwd or conf_pwd)
        street   = self.street_ent.get().strip()
        unit     = self.unit_ent.get().strip()
        city     = self.city_ent.get().strip()
        state    = self.state_ent.get().strip()
        zip_code = self.zip_ent.get().strip()

        # ── Personal validation ─────────────────────────────────────────
        if not fname:
            self._switch_tab("personal")
            self._show_field_error("fname", "First name is required.")
            self.fname_ent.focus_set()
            return
        if not lname:
            self._switch_tab("personal")
            self._show_field_error("lname", "Last name is required.")
            self.lname_ent.focus_set()
            return
        if not contact:
            self._switch_tab("personal")
            self._show_field_error("contact", "Contact number is required.")
            self.contact_ent.focus_set()
            return
        try:
            from utils import valid_contact as _vc
            _vc(contact, "Contact number")
        except ValidationError as err:
            self._switch_tab("personal")
            self._show_field_error("contact", str(err))
            self.contact_ent.focus_set()
            return

        # ── Account validation ──────────────────────────────────────────
        if self._linked_username != '—' and self.can_manage_accounts:
            if not uname:
                self._switch_tab("account")
                self._show_field_error("uname", "Username is required.")
                self.uname_ent.focus_set()
                return
            if " " in uname or len(uname) < 3 or len(uname) > 20:
                self._switch_tab("account")
                self._show_field_error("uname", "Username must be 3-20 characters with no spaces.")
                self.uname_ent.focus_set()
                return
            if uname.lower() != self._linked_username.lower():
                if any(u['username'].lower() == uname.lower() for u in get_rows('users')):
                    self._switch_tab("account")
                    self._show_field_error("uname", f"Username '{uname}' is already taken.")
                    self.uname_ent.focus_set()
                    return

        if not email:
            self._switch_tab("account")
            self._show_field_error("email", "Email address is required.")
            self.email_ent.focus_set()
            return
        try:
            from utils import valid_email as _ve
            _ve(email, "Email address")
        except ValidationError as err:
            self._switch_tab("account")
            self._show_field_error("email", str(err))
            self.email_ent.focus_set()
            return

        # Optional password reset — validate only when at least one field is filled
        if do_password_reset:
            if len(new_pwd) < 8:
                self._switch_tab("account")
                self._show_field_error("pwd", "Password must be at least 8 characters.")
                self.pwd_ent.focus_set()
                return
            if new_pwd != conf_pwd:
                self._switch_tab("account")
                self._show_field_error("cpwd", "Passwords do not match.")
                self.cpwd_ent.focus_set()
                return

        # ── Address validation ──────────────────────────────────────────
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
        if not zip_code.isdigit() or len(zip_code) != 4:
            self._switch_tab("address")
            self._show_field_error("zip", "Postal code must contain exactly 4 digits.")
            self.zip_ent.focus_set()
            return

        full_name = compose_full_name(fname, lname)
        address = compose_address(street, unit, city, state, zip_code)

        edit_customer(self.customer['customer_id'], full_name, contact, email, address, self.acting_user)

        # Update username if changed
        username_updated = False
        if self._linked_username != '—' and self.can_manage_accounts and uname != self._linked_username:
            update_customer_account_username(self.customer['customer_id'], uname, self.acting_user)
            username_updated = True

        # Apply password reset if fields were filled
        if do_password_reset and self.can_manage_accounts:
            reset_customer_account_password(
                self.customer['customer_id'], new_pwd, conf_pwd, self.acting_user
            )

        msg_details = [f"Customer {self.customer['customer_id']} details saved."]
        if username_updated:
            msg_details.append(f"Username updated to: {uname}")
        if do_password_reset and self.can_manage_accounts:
            msg_details.append("Password has been reset successfully.")

        messagebox.showinfo("Profile Updated", "\n".join(msg_details), parent=self)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()


class CustomerHistoryModal(tk.Toplevel):
    """Displays customer's historical job tickets (FR-12)."""
    def __init__(self, parent, customer, on_open_job_callback=None):
        super().__init__(parent)
        self.customer = customer
        self.on_open_job_callback = on_open_job_callback

        self.title(f"Repair History: {customer['name']} ({customer['customer_id']})")
        self.geometry("720x460")
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")

        tk.Label(
            top_bar,
            text=f"Repair Dossier: {self.customer['name']}",
            font=FONT_TITLE,
            fg=INK,
            bg=BG_PANEL
        ).pack(anchor="w")

        tk.Label(
            top_bar,
            text=f"Customer ID: {self.customer['customer_id']}   |   Contact: {self.customer['contact_no']}",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w", pady=(2, 0))

        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")
        secondary_button(bot, "Close", command=self.destroy).pack(side="right")

        content = tk.Frame(self, bg=BG, padx=20, pady=16)
        content.pack(fill="both", expand=True)

        cols = ("job_id", "date_received", "device", "problem", "status")
        heads = ("Job ID", "Date Received", "Device Specs", "Reported Problem", "Current Status")
        widths = (90, 130, 160, 200, 110)

        t_frame, tree = make_table(content, cols, heads, widths, horizontal=True)
        t_frame.pack(fill="both", expand=True)

        jobs = customer_history(self.customer['customer_id'])
        s_map = status_map()

        rows = []
        for j in jobs:
            rows.append({
                'job_id': j['job_id'],
                'date_received': j['date_received'],
                'device': f"{j['device_type']} {j['brand']} {j['model']}",
                'problem': j['problem'],
                'status': s_map.get(j['job_id'], 'Received')
            })

        fill_table(tree, rows, cols)
