import os
import sys
import tkinter as tk
from .gui import Slipway

ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slipway.ico")
PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slipway.png")


def main():
    try:                                   # Windows: own taskbar entry (and icon) instead of Python's
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Slipway.FM1")
    except Exception:
        pass
    root = tk.Tk()
    try:                                   # the sailboat logo on the window and taskbar (Windows) / Dock (macOS, Linux)
        if sys.platform.startswith("win"):
            root.iconbitmap(default=ICON)
        else:
            root._logo = tk.PhotoImage(file=PNG)
            root.iconphoto(True, root._logo)
    except Exception:
        pass
    Slipway(root)
    root.mainloop()


main()
