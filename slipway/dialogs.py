"""Slipway's own message boxes. They look like the rest of the app (day/night colours) and, for warnings and errors, sound
a ship's bell instead of the Windows chime. The bell is ship_bell.wav, which ships with Slipway (nothing is downloaded). Replace it with any WAV to change the sound.

The same four calls as tkinter.messagebox, so the rest of the code reads the same:
    showinfo(title, message)   showwarning(title, message)   showerror(title, message)   askyesno(title, message, icon=...)
Set the environment variable SLIPWAY_QUIET=1 to turn the bell off."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

HORN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ship_bell.wav")


def horn():
    """Ring the ship's bell (and return at once). Silent if muted, if the file is missing, or if there's no way to play it."""
    if os.environ.get("SLIPWAY_QUIET") or not os.path.exists(HORN):
        return False
    try:
        if sys.platform.startswith("win"):
            import winsound
            winsound.PlaySound(HORN, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            return True
        for player in (["afplay"], ["paplay"], ["aplay", "-q"]):         # macOS / Linux: whatever is there
            try:
                subprocess.Popen(player + [HORN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except OSError:
                continue
    except Exception:
        pass
    return False


def _palette(win):
    st = ttk.Style(win)
    return dict(bg=st.lookup("TFrame", "background") or "#151213", ink=st.lookup("TLabel", "foreground") or "#f2ede9",
                warn=st.lookup("Warn.TLabel", "foreground") or "#ff7a68", accent=st.lookup("Accent.TButton", "background") or "#e0b04a")


def _glyph(canvas, kind, p):
    """A small drawn symbol (drawn, not typed, so it looks the same on every computer)."""
    canvas.delete("all")
    if kind in ("warning", "question"):
        col = p["accent"] if kind == "question" else p["warn"]
        canvas.create_polygon(26, 4, 49, 46, 3, 46, fill="", outline=col, width=3, joinstyle="round")
        canvas.create_line(26, 18, 26, 32, fill=col, width=4, capstyle="round")
        canvas.create_oval(24, 37, 29, 42, fill=col, outline="")
    elif kind == "error":
        canvas.create_oval(4, 4, 48, 48, outline=p["warn"], width=3)
        canvas.create_line(17, 17, 35, 35, fill=p["warn"], width=4, capstyle="round")
        canvas.create_line(35, 17, 17, 35, fill=p["warn"], width=4, capstyle="round")
    else:
        canvas.create_oval(4, 4, 48, 48, outline=p["accent"], width=3)
        canvas.create_line(26, 22, 26, 36, fill=p["accent"], width=4, capstyle="round")
        canvas.create_oval(24, 14, 29, 19, fill=p["accent"], outline="")


def _box(title, message, kind, buttons, loud, parent=None):
    """Shows a modal box. buttons = [(label, value)], the first is the default. Returns the value pressed
    (the last button's value if the window is closed or Escape is pressed)."""
    root = parent or tk._default_root
    if root is None:                                        # no window at all (shouldn't happen): fall back to the system box
        from tkinter import messagebox
        if len(buttons) > 1:
            return messagebox.askyesno(title, message)
        getattr(messagebox, {"warning": "showwarning", "error": "showerror"}.get(kind, "showinfo"))(title, message)
        return buttons[0][1]
    if loud:
        horn()
    win = tk.Toplevel(root)
    win.title(title)
    p = _palette(win)
    win.configure(bg=p["bg"])
    win.transient(root)
    win.resizable(False, False)
    result = {"v": buttons[-1][1]}
    body = ttk.Frame(win, padding=18)
    body.pack(fill="both", expand=True)
    top = ttk.Frame(body)
    top.pack(fill="x")
    icon = tk.Canvas(top, width=54, height=52, highlightthickness=0, bd=0, bg=p["bg"])
    icon.pack(side="left", anchor="n", padx=(0, 14))
    _glyph(icon, kind, p)
    ttk.Label(top, text=message, wraplength=480, justify="left").pack(side="left", fill="x", expand=True)
    row = ttk.Frame(body)
    row.pack(fill="x", pady=(16, 0))
    first = None

    def pick(v):
        result["v"] = v
        win.destroy()
    for i, (label, value) in enumerate(buttons):
        b = ttk.Button(row, text=label, command=lambda v=value: pick(v), style="Accent.TButton" if i == 0 else "TButton")
        b.pack(side="right" if len(buttons) > 1 else "left", padx=(8, 0))
        first = first or b
    win.bind("<Return>", lambda e: pick(buttons[0][1]))
    win.bind("<Escape>", lambda e: pick(buttons[-1][1]))
    win.protocol("WM_DELETE_WINDOW", lambda: pick(buttons[-1][1]))
    win.update_idletasks()
    x = root.winfo_rootx() + max(0, (root.winfo_width() - win.winfo_reqwidth()) // 2)
    y = root.winfo_rooty() + max(0, (root.winfo_height() - win.winfo_reqheight()) // 3)
    win.geometry("+%d+%d" % (x, y))
    try:
        win.grab_set()
    except tk.TclError:
        pass
    first.focus_set()
    win.wait_window()
    return result["v"]


def showinfo(title, message, **kw):
    _box(title, message, "info", [("OK", True)], loud=False, parent=kw.get("parent"))


def showwarning(title, message, **kw):
    _box(title, message, "warning", [("OK", True)], loud=True, parent=kw.get("parent"))


def showerror(title, message, **kw):
    _box(title, message, "error", [("OK", True)], loud=True, parent=kw.get("parent"))


def askyesno(title, message, icon="question", **kw):
    """Yes/No. icon='warning' (or 'error') rings the bell; a plain question is quiet."""
    kind = icon if icon in ("warning", "error") else "question"
    return bool(_box(title, message, kind, [("Yes", True), ("No", False)], loud=kind in ("warning", "error"),
                     parent=kw.get("parent")))
