import tkinter as tk
from gui.theme import BG, apply_theme
from gui.login import LoginView
from gui.main_menu import MainMenuView
from storage import init_storage
from logic.auth import seed_default_admin
from logic.catalog import seed_sample_services


class App(tk.Tk):
    """
    Main Application Window (One Tk Root).
    Manages global user session, ttk styling, and screen transitions between
    Login and the Authenticated Main Menu (FR-01 - FR-06).
    """
    def __init__(self):
        super().__init__()
        self.title("FLUX Repair Co.")

        # Adaptively size and center on screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = min(1380, max(1240, screen_w - 40))
        h = min(780, max(600, screen_h - 70))
        x = max(0, (screen_w - w) // 2)
        y = max(0, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1180, 560)
        self.configure(bg=BG)

        # Apply custom Cleanroom Atelier ttk styles
        apply_theme(self)

        self.current_user = None
        self.current_frame = None

        # Show Login Screen initially
        self.show_login()

    def show_login(self):
        """Display the authentication screen (FR-01)."""
        self.title("FLUX Repair Co.")
        self.current_user = None
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = LoginView(self, on_login_success=self.on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def on_login_success(self, user):
        """Transition to role-based main menu upon successful authentication (FR-03)."""
        self.title("FLUX Repair Co.")
        self.current_user = user
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = MainMenuView(
            self,
            current_user=self.current_user,
            on_logout_callback=self.show_login
        )
        self.current_frame.pack(fill="both", expand=True)
