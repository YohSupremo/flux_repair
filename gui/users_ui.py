import tkinter as tk
from tkinter import ttk, messagebox
from gui.theme import (
    BG, BG_PANEL, BG_HOVER, BG_INPUT, LINE, INK, MUTED, DIM,
    EMERALD, EMERALD_HOVER, RED, FONT_TITLE, FONT_HEADING, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_MONO
)
from gui.widgets import (
    primary_button, secondary_button, danger_button, make_table,
    fill_table, labeled_field, guard, confirm
)
from logic.auth import list_users, add_user, edit_user, delete_user
from models import ROLES


class UsersView(tk.Frame):
    """
    User Account Administration (FR-05, FR-05a).
    Restricted to Admin: manages credentials, role assignments, and account lifecycles.
    """
    def __init__(self, parent, acting_user):
        super().__init__(parent, bg=BG)
        self.acting_user = acting_user

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16, bd=0, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG_PANEL)
        title_box.pack(side="left")

        tk.Label(title_box, text="User & Staff Administration", font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")
        tk.Label(
            title_box,
            text="Manage system operator credentials, roles (Admin, Staff, Technician), and permissions.",
            font=FONT_SMALL,
            fg=DIM,
            bg=BG_PANEL
        ).pack(anchor="w")

        btn_box = tk.Frame(header, bg=BG_PANEL)
        btn_box.pack(side="right")

        primary_button(btn_box, "+ Add User Account", command=self._open_add_modal).pack(side="left")

        # Table Container
        table_wrap = tk.Frame(self, bg=BG, padx=24, pady=16)
        table_wrap.pack(fill="both", expand=True)

        cols = ("user_id", "username", "role", "full_name")
        heads = ("User ID", "Login Username", "System Role", "Operator Full Name")
        widths = (110, 180, 150, 280)

        self.table_frame, self.tree = make_table(table_wrap, cols, heads, widths)
        self.table_frame.pack(fill="both", expand=True)

        # Bottom Bar
        bottom_bar = tk.Frame(self, bg=BG_PANEL, padx=24, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bottom_bar.pack(fill="x", side="bottom")

        secondary_button(bottom_bar, "Edit User Account", command=self._open_edit_modal).pack(side="left", padx=(0, 8))
        danger_button(bottom_bar, "Delete Account", command=self._handle_delete).pack(side="left")

    def refresh(self):
        users = list_users()
        cols = ("user_id", "username", "role", "full_name")
        fill_table(self.tree, users, cols)

    def _get_selected_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Please select a user account from the table.")
            return None
        uid = self.tree.item(sel[0], "values")[0]
        users = list_users()
        return next((u for u in users if u['user_id'] == uid), None)

    def _open_add_modal(self):
        UserFormModal(self, "Add User Account", self.acting_user, on_save_callback=self.refresh)

    def _open_edit_modal(self):
        u = self._get_selected_user()
        if u:
            UserFormModal(self, "Edit User Account", self.acting_user, user=u, on_save_callback=self.refresh)

    @guard
    def _handle_delete(self):
        u = self._get_selected_user()
        if not u:
            return
        uid = u['user_id']
        uname = u['username']

        if confirm("Confirm Deletion", f"Are you sure you want to delete user account '{uname}' ({uid})?"):
            delete_user(uid, self.acting_user)
            messagebox.showinfo("Account Deleted", f"User {uid} successfully deleted.")
            self.refresh()


class UserFormModal(tk.Toplevel):
    """Modal dialog for creating and modifying user accounts."""
    def __init__(self, parent, title_text, acting_user, user=None, on_save_callback=None):
        super().__init__(parent)
        self.acting_user = acting_user
        self.user = user
        self.on_save_callback = on_save_callback

        self.title(title_text)
        self.geometry("460x420")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.transient(parent)
        self.grab_set()

        self._build_ui(title_text)

    def _build_ui(self, title_text):
        top_bar = tk.Frame(self, bg=BG_PANEL, padx=20, pady=14, bd=0, highlightthickness=1, highlightbackground=LINE)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text=title_text, font=FONT_TITLE, fg=INK, bg=BG_PANEL).pack(anchor="w")

        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill="both", expand=True)

        card = tk.Frame(body, bg=BG_PANEL, bd=0, highlightthickness=1, highlightbackground=LINE, padx=16, pady=16)
        card.pack(fill="both", expand=True)

        f1, self.uname_entry = labeled_field(card, "USERNAME * (3-20 characters, no spaces)", widget_class=tk.Entry)
        f1.pack(fill="x", pady=(0, 10))

        pwd_label = "PASSWORD *" if not self.user else "NEW PASSWORD (leave blank to keep current)"
        f2, self.pwd_entry = labeled_field(card, pwd_label, widget_class=tk.Entry, show="*")
        f2.pack(fill="x", pady=(0, 10))

        f3, self.role_combo = labeled_field(card, "SYSTEM ROLE *", widget_class=ttk.Combobox)
        self.role_combo['values'] = list(ROLES)
        self.role_combo.set("Staff" if not self.user else self.user['role'])
        f3.pack(fill="x", pady=(0, 10))

        f4, self.name_entry = labeled_field(card, "OPERATOR FULL NAME *", widget_class=tk.Entry)
        f4.pack(fill="x", pady=(0, 10))

        if self.user:
            self.uname_entry.insert(0, self.user['username'])
            self.name_entry.insert(0, self.user['full_name'])

        bot = tk.Frame(self, bg=BG_PANEL, padx=20, pady=12, bd=0, highlightthickness=1, highlightbackground=LINE)
        bot.pack(fill="x", side="bottom")

        secondary_button(bot, "Cancel", command=self.destroy).pack(side="left")
        primary_button(bot, "Save Account", command=self._save).pack(side="right")

    @guard
    def _save(self):
        uname = self.uname_entry.get().strip()
        pwd = self.pwd_entry.get()
        role = self.role_combo.get()
        fname = self.name_entry.get().strip()

        if self.user:
            edit_user(self.user['user_id'], uname, pwd, role, fname, self.acting_user)
            messagebox.showinfo("User Updated", f"User account {self.user['user_id']} updated.")
        else:
            new_u = add_user(uname, pwd, role, fname, self.acting_user)
            messagebox.showinfo("User Created", f"Account created with User ID: {new_u['user_id']}.")

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
