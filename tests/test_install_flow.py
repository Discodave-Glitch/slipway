"""Real window (needs a display): pick a firmware in the list, press Install, check the whole chain runs."""
import os, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["SLIPWAY_DIR"] = tempfile.mkdtemp()
import tkinter as tk
import hashlib
from slipway import github, library, flasher, catalogue, dialogs

good = os.path.join(tempfile.mkdtemp(), "g.fwsc")
open(good, "wb").write(b"\0" * 1060 + b"AC791N" + b"\1" * 300000 + flasher.LOADER_MARKER)
SHA = hashlib.sha256(open(good, "rb").read()).hexdigest()
CAT = {"firmwares": [
    {"id": "felucca", "kind": ["synth", "groove"], "name": "Felucca", "author": "Leo", "repo": "hugelton/Felucca", "ident": "FM-1_91\\d",
     "what": "d", "site": "https://github.com/hugelton/Felucca", "version": "1.6", "date": "2026-10-13", "pkg": "fw/felucca-1.6.fwsc",
     "size": 300000, "sha256": SHA, "release": "https://github.com/hugelton/Felucca/releases/tag/v1.6", "tag": "v1.6", "beta": False},
    {"id": "bad", "kind": "drums", "name": "Mismatch", "author": "B", "repo": "b/mismatch", "what": "d", "version": "1", "pkg": "fw/m-1.fwsc",
     "sha256": "00" * 32, "release": "https://github.com/b/mismatch/releases/tag/v1", "tag": "v1", "beta": True}]}
catalogue.fetch = lambda *a, **k: CAT
def gfetch(url, timeout=20):
    if "hugelton/Felucca/releases/tags/v1.6" in url or "b/mismatch/releases/tags/v1" in url:
        return {"assets": [{"name": "x.fwsc", "browser_download_url": "https://github.com/x/x.fwsc"}]}
github.fetch = gfetch
calls = []
library.set_firmware_dir(tempfile.mkdtemp())
def fake_download(url, progress=None):
    calls.append(url)
    t = os.path.join(library.data_dir(), "dl.fwsc"); open(t, "wb").write(open(good, "rb").read()); return t
library.download = fake_download
ran = []
class P:
    def __init__(s, cmd, **k): ran.append(cmd); s.stdout = iter(["Writing\n", "Done\n"])
    def wait(s): return 0
orig_flash = flasher.flash
flasher.flash = lambda f, st=False, on_line=None, popen=P: orig_flash(f, st, on_line, popen)
flasher.tool_info = lambda: {"path": "x", "sha256": "y"}
flasher.tool_path = lambda: "/bin/true"
flasher.missing_modules = lambda: []
REAL = (dialogs.showinfo, dialogs.showwarning, dialogs.showerror, dialogs.askyesno)   # the real boxes, for the horn test below
shown = []
dialogs.askyesno = lambda *a, **k: True
dialogs.showinfo = lambda *a, **k: shown.append(("info", a))
dialogs.showwarning = lambda *a, **k: shown.append(("warn", a))
dialogs.showerror = lambda *a, **k: shown.append(("err", a))

from slipway.gui import Slipway
root = tk.Tk(); app = Slipway(root)
def pump(sec):
    end = time.time() + sec
    while time.time() < end: root.update(); time.sleep(0.02)
pump(1.5)
kid = app.tree.get_children()[0]; app.tree.selection_set(kid); pump(0.3)
# stock first: with no stock V15 saved, a custom firmware is refused before anything is downloaded
assert app.banner_btn.winfo_ismapped(), "stock banner button missing while stock is not saved"
app.install_selected(); pump(1.0)
assert not ran and not calls, "installed/downloaded a custom firmware with no stock saved"
assert any(k == "warn" and "stock V15 first" in a[0] for k, a in shown), shown
shown.clear()
stock_file = os.path.join(tempfile.mkdtemp(), "FM-1.fwsc")
open(stock_file, "wb").write(b"\0" * 1060 + b"AC791N" + b"\2" * 300000)
library.set_stock(stock_file); app._update_banner(); pump(0.3)
assert library.stock_first_block(False) == "" and library.stock_first_block(True) == ""
app.install_selected(); pump(2.0)
assert ran and "--force" not in ran[0] and ran[0][-1] == "--yes", ran
assert any(k == "info" and "Done" in a[1] for k, a in shown), shown
assert [f for f in os.listdir(library.firmware_dir()) if f.endswith(".fwsc")] == ["Felucca-1.6.fwsc"], os.listdir(library.firmware_dir())
assert len(calls) == 1
# second time: already in the folder, so nothing is downloaded again and no second file appears
ran.clear(); shown.clear()
app.refresh(); pump(1.5)
app.tree.selection_set(app.tree.get_children()[0]); pump(0.3)
assert app.tree.item(app.tree.get_children()[0], "values")[7] == "\u2713", app.tree.item(app.tree.get_children()[0], "values")
assert library.stock_first_block(False) == "putback", "a custom firmware is on the FM-1: stock must come back first"
app.install_selected(); pump(2.0)                                   # asks to put stock back (test answers yes) instead of installing
assert len(calls) == 1, "downloaded while stock was not back"
assert ran and library.load_state()["installed"]["stock"] is True, (ran, library.load_state()["installed"])
assert library.stock_first_block(False) == ""
ran.clear(); shown.clear()
app.install_selected(); pump(2.0)                                   # now the custom firmware goes on
assert len(calls) == 1, "downloaded twice"
assert ran and "--force" not in ran[0], ran
assert library.load_state()["installed"]["stock"] is False
assert len([f for f in os.listdir(library.firmware_dir()) if f.endswith(".fwsc")]) == 1
# the tick: Slipway installed Felucca, so the list shows it on the FM-1
assert app.tree.item(app.tree.get_children()[0], "values")[0] == "\u2713"
# stock first: with Felucca on the FM-1, another custom firmware is not installed - the stock V15 goes back instead
ran.clear(); shown.clear()
app.tree.selection_set(app.tree.get_children()[1]); pump(0.3)
n = len(calls)
app.install_selected(); pump(2.0)
assert len(calls) == n, "downloaded a custom firmware while Felucca (custom) was still on the FM-1"
assert library.load_state()["installed"]["stock"] is True, "stock V15 was not put back"
# a file that doesn't match the catalogue's checksum is refused and never reaches the installer
ran.clear(); shown.clear()
app.tree.selection_set(app.tree.get_children()[1]); pump(0.3)
app.install_selected(); pump(1.5)
assert not ran, "flashed a file whose checksum didn't match"
assert any(k == "err" and "checksum" in a[1] for k, a in shown), shown
assert [f for f in os.listdir(library.firmware_dir()) if f.endswith(".fwsc")] == ["Felucca-1.6.fwsc"]
# "Download to folder": a checksum mismatch saves nothing and never reaches the installer
ran.clear(); shown.clear()
app.tree.selection_set(app.tree.get_children()[1]); pump(0.3)
app.download_selected(); pump(1.5)
assert not ran and any(k == "err" and "checksum" in a[1] for k, a in shown), shown
assert [f for f in os.listdir(library.firmware_dir()) if f.endswith(".fwsc")] == ["Felucca-1.6.fwsc"]
assert "disabled" not in app.download_btn.state(), "button stuck disabled after a failed download"
# already in the folder: nothing is downloaded and the person is told
shown.clear(); n = len(calls)
app.tree.selection_set(app.tree.get_children()[0]); pump(0.3)
app.download_selected(); pump(0.5)
assert len(calls) == n and any(k == "info" and "already" in a[1] for k, a in shown), shown
# not in the folder: it is downloaded into the folder and NOT installed
os.remove(os.path.join(library.firmware_dir(), "Felucca-1.6.fwsc")); app.refresh(); pump(1.5)
app.tree.selection_set(app.tree.get_children()[0]); pump(0.3)
ran.clear(); n = len(calls)
app.download_selected(); pump(2.0)
assert len(calls) == n + 1 and not ran, (calls, ran)
assert [f for f in os.listdir(library.firmware_dir()) if f.endswith(".fwsc")] == ["Felucca-1.6.fwsc"]
assert "disabled" not in app.download_btn.state()
# put Felucca back on the FM-1 (stock is on, so it is allowed) so the tick sort below has something to sort
app.tree.selection_set(app.tree.get_children()[0]); pump(0.3)
assert app._current()["name"] == "Felucca"
app.install_selected(); pump(2.0)
assert library.load_state()["installed"]["stock"] is False
# sorting by clicking column headings
def names(): return [app.tree.item(i, "values")[1] for i in app.tree.get_children()]
app.tree.selection_set(app.tree.get_children()[0]); pump(0.2)
sel_before = app._current()["name"]
app.sort_by("name"); assert names() == ["Felucca", "Mismatch"], names()
assert app._current()["name"] == sel_before, "selection lost when sorting"
app.sort_by("name"); assert names() == ["Mismatch", "Felucca"], names()
assert "▼" in app.tree.heading("name", "text") and "▲" not in app.tree.heading("name", "text")
app.sort_by("tick"); assert names()[0] == "Felucca", names()           # the one on the FM-1 comes first
app.sort_by("tick"); assert names()[0] == "Mismatch", names()
app.sort_by("infolder"); assert names()[0] == "Felucca", names()       # the one already in the folder first
app.sort_by("version"); assert sorted(names()) == ["Felucca", "Mismatch"]
app.refresh(); pump(1.5); assert app.sort == ("version", False)       # the chosen order survives a refresh
assert app._sort_key(3, ("", "", "", "1.10")) > app._sort_key(3, ("", "", "", "1.9")), "1.10 must come after 1.9"
# the released column: newest first, undated last, and nothing squeezed in the narrowest window
app.sort_by("released"); assert names()[0] == "Felucca", names()
assert app.tree.item(app.tree.get_children()[0], "values")[4].startswith("2026-10-13"), app.tree.item(app.tree.get_children()[0], "values")
assert app.tree.item(app.tree.get_children()[1], "values")[4] == ""
root.geometry("200x200"); pump(0.8)                           # as small as the window will allow
assert root.winfo_width() >= 780, root.winfo_width()
assert app.tree.winfo_height() >= 120, "firmware list squashed to %d px" % app.tree.winfo_height()
squeezed = []
def scan(w):
    for c in w.winfo_children():
        if c.winfo_class() == "TButton" and c.winfo_viewable() and (c.winfo_width() < c.winfo_reqwidth() or not inside(c)):
            squeezed.append((c.cget("text"), c.winfo_width(), c.winfo_reqwidth()))
        scan(c)
# the buttons that matter are all on screen, even in a small window
def inside(w):
    return w.winfo_rooty() >= root.winfo_rooty() and w.winfo_rooty() + w.winfo_height() <= root.winfo_rooty() + root.winfo_height() \
        and w.winfo_rootx() + w.winfo_width() <= root.winfo_rootx() + root.winfo_width()
assert inside(app.install_btn) and inside(app.download_btn), "action buttons clipped"
btns = []
def walk(w):
    for c in w.winfo_children():
        if c.winfo_class() == "TButton" and c.cget("text") in ("Save stock V15", "Put stock V15 back", "Launch selected file", "Stuck? Rescue..."): btns.append(c)
        walk(c)
walk(root)
assert len(btns) == 4 and all(inside(b) for b in btns), [(b.cget("text"), inside(b)) for b in btns]
scan(root); assert not squeezed, squeezed
# Rescue: only the stock V15 is offered (stock first, every time), and Install now goes through the normal checked install
ran.clear(); shown.clear()
app.rescue(); pump(0.3)
win = app._rescue_win; assert win.winfo_exists()
keys = [k for k, _l in app._rescue_options()]
assert keys == ["stock"], keys
assert app._rescue_choice.get() == "stock"
app.rescue(); assert str(app._rescue_win) == str(win)                  # a second click re-uses the open window
def find_btn(w, label):
    for c in w.winfo_children():
        if c.winfo_class() == "TButton" and c.cget("text") == label: return c
        f = find_btn(c, label)
        if f: return f
gb = find_btn(win, "Full recovery guide..."); assert gb is not None, "guide button missing in Rescue"
gb.invoke(); pump(0.4)
gw = app._guide_win; assert gw.winfo_exists()
body = app._guide_text.get("1.0", "end")
for must in ("write 0x4000 app_v15.bin", "read 0 0x100000 backup.bin", "0x980F", "VirtualBox", "6edf3c37fb5bbbc33607c89375ee024d5477c17914d72221c8c68e58a8255686"):
    assert must in body, must
app.recovery_guide(); assert str(app._guide_win) == str(gw)
from slipway import recovery_guide as rg
assert "write 0x4000" in rg.as_text() and "erasechip" in rg.as_text()   # the warning names it, the steps never use it
for _h, lines in rg.SECTIONS:
    for ln in lines:
        assert not ln.strip().startswith("erasechip"), ln
gw.destroy()
app._rescue_go(); pump(2.0)
assert not win.winfo_exists(), "rescue window left open"
assert ran and "--force" not in ran[0] and ran[0][-1] == "--yes", ran
assert any(k == "info" and "Done" in a[1] for k, a in shown), shown
assert library.load_state()["installed"]["stock"] is True
# the real boxes: warnings, errors and warning-questions sound the ship bell; info and plain questions don't
r_info, r_warn, r_err, r_ask = REAL
horns = []; orig_horn = dialogs.horn; dialogs.horn = lambda: horns.append(1)
def press(label, delay=250):
    def go():
        tops = [w for w in root.winfo_children() if w.winfo_class() == "Toplevel"]
        assert tops, "dialog did not open"
        def find(w):
            for c in w.winfo_children():
                if c.winfo_class() == "TButton" and c.cget("text") == label: return c
                f = find(c)
                if f: return f
        b = find(tops[-1]); assert b is not None, label; b.invoke()
    root.after(delay, go)
press("OK"); r_warn("t", "careful"); assert len(horns) == 1, horns
press("OK"); r_err("t", "broken"); assert len(horns) == 2, horns
press("OK"); r_info("t", "fyi"); assert len(horns) == 2, "info must be quiet"
press("Yes"); assert r_ask("t", "sure?", icon="warning") is True and len(horns) == 3
press("No"); assert r_ask("t", "sure?", icon="warning") is False and len(horns) == 4
press("Yes"); assert r_ask("t", "plain question") is True and len(horns) == 4, "a plain question must be quiet"
def close_it():
    top = [w for w in root.winfo_children() if w.winfo_class() == "Toplevel"][-1]
    top.tk.call(top.protocol("WM_DELETE_WINDOW"))              # the window's own close button
root.after(250, close_it)
assert r_ask("t", "closing means no", icon="warning") is False
assert not [w for w in root.winfo_children() if w.winfo_class() == "Toplevel"], "a dialog was left open"
dialogs.horn = orig_horn
assert os.path.getsize(dialogs.HORN) > 10000, "ship_bell.wav missing"
# dark mode toggles and persists
app.toggle_dark(); pump(0.3)
assert library.load_state()["dark"] is False   # dark is the default, so the first toggle goes to day
app.toggle_dark()
print("install flow OK")
root.destroy()
