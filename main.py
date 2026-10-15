"""
FLUX Repair Co. — Computer & Laptop Repair Service System
Course: IT Professional Elective 1 (ITEP310-T)
Language / GUI: Python 3 + Tkinter (Desktop GUI)
Storage: Local CSV files in data/
"""

import sys
import os

# Ensure current directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import init_storage
from logic.auth import seed_default_admin
from logic.catalog import seed_sample_services
from gui.app import App


def main():
    # Step 1: Initialize local storage folders and CSV files
    init_storage()

    # Step 2: Seed default Admin account if no users exist (FR-05a)
    seed_msg = seed_default_admin()
    if seed_msg:
        print(f"[BOOT] {seed_msg}")

    # Step 3: Seed standard sample repair services (FR-22)
    seed_sample_services()

    # Step 4: Launch Tkinter Desktop Application
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
