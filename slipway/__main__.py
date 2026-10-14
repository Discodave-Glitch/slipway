import os
import tkinter as tk
from .gui import Slipway

ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slipway.ico")


def main():
    try:                                   # Windows: own taskbar entry (and icon) instead of Python's
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Slipway.FM1")
    except Exception:
        pass
    root = tk.Tk()
    try:                                   # the sailboat logo on the window and taskbar
        root.iconbitmap(default=ICON)
    except Exception:
        pass
    Slipway(root)
    root.mainloop()


main()
