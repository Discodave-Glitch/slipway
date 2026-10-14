import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["SLIPWAY_DIR"] = tempfile.mkdtemp()
import tkinter as tk
from slipway import github, library, catalog, catalogue
library.set_firmware_dir(tempfile.mkdtemp())
if len(sys.argv) > 3 and sys.argv[3] == "dark":
    st = library.load_state(); st["dark"] = True; library.save_state(st)
GOOD = os.path.join(tempfile.mkdtemp(), "x.fwsc"); open(GOOD, "wb").write(b"\0"*1060 + b"AC791N" + b"\1"*300000)
library.store_in_folder(GOOD, "Felucca", "v1.0")
library.record_install("FiMba-1", "jadamsowers/fm1-fimba", "v1.0", False)

def fake(url, timeout=20):
    repo = {"hugelton/Felucca": ("Felucca", "hugelton", "Multi-engine synthesizer firmware for the M-VAVE FM-1", True),
            "charlesvestal/fm1-x0x": ("fm1-x0x", "charlesvestal", "X0X for FM-1", True),
            "jadamsowers/fm1-fimba": ("fm1-fimba", "jadamsowers", "FiMba-1 physically modelled kalimba", True),
            "charlesvestal/fm1-fomni": ("fm1-fomni", "charlesvestal", "Omnichord-style chord harp", False)}
    for r, (n, o, d, rel) in repo.items():
        if url.endswith("/repos/" + r):
            return {"full_name": r, "name": n, "owner": {"login": o}, "description": d, "html_url": "https://github.com/" + r}
        if ("/repos/%s/releases" % r) in url:
            return [{"tag_name": "v1.0", "published_at": "2026-09-01T00:00:00Z", "assets": [{"name": n + ".fwsc", "browser_download_url": "https://github.com/x/y/z.fwsc"}]}] if rel else []
    return None
NAMES = [("Felucca","Leo Kuroshita (Hügelton Instruments)","hugelton/Felucca","1.6",["synth","groove","dev"],False),
 ("SLOOP","isod89","isod89/sloop-fm1","2.6",["groove"],False),("X0X","Charles Vestal","charlesvestal/fm1-x0x","1.0.6",["groove"],False),
 ("FiMba-1","jadamsowers","jadamsowers/fm1-fimba","0.6.1",["synth","chords"],False),("Hortator","DEADACTIVE","deadactive/hortator","0.16.0",["drums"],False),
 ("Jangada","zednaked","zednaked/jangada","0.9.9",["synth","groove"],False),("Melodee","keremimo","keremimo/melodee","1.4.0-rc.1",["synth","groove"],False),
 ("ChoralRoot","Quixotic7","Quixotic7/ChoralRootFM1","0.21",["chords"],False),("GHOULBOX","Jason Persinger","jasonpersinger/ghoulbox-fm1-dungeon-synth","2.1",["synth","groove"],False),
 ("TRIBE","apiel","apiel/fm1-tribe","0.1-beta",["groove","drums"],True)]
catalogue.fetch = lambda *a, **k: {"firmwares": [{"id": n.lower(), "kind": k, "name": n, "author": a, "repo": r, "what": "Custom firmware for the FM-1 (%s)." % n,
    "version": v, "pkg": "fw/%s-%s.fwsc" % (n.lower(), v), "sha256": "ab"*32, "release": "https://github.com/%s/releases" % r, "tag": "v"+v, "beta": b} for n,a,r,v,k,b in NAMES]}
github.fetch = fake; github.describe.__defaults__ = (fake,); github.search.__defaults__ = (fake,)
sys.modules.pop("slipway.gui", None)
from slipway.gui import Slipway
root = tk.Tk()
sw, sh = int(sys.argv[1]), int(sys.argv[2])
h = Slipway(root)
root.geometry("%dx%d+0+0" % (sw, sh))
for _ in range(30): root.update(); __import__("time").sleep(0.05)
kids = h.tree.get_children(); h.tree.selection_set(kids[3]); h.tree.event_generate("<<TreeviewSelect>>")
h._set_device("original_guess", "Original firmware detected (FM-1_906)."); h._show_folder()
for _ in range(10): root.update()
open("/tmp/hub_ok.txt", "w").write(repr([h.tree.item(k, "values")[:6] for k in kids]) + " family=" + h.family)
os.system("import -window root /tmp/shots/hub_%d.png 2>/dev/null || true")
open("/tmp/shot_now","w").write("1")
root.update()
import subprocess; subprocess.run(["python3","-c","from PIL import ImageGrab; ImageGrab.grab(xdisplay=\":77\").save(\"/tmp/shots/hub_%s.png" % (sys.argv[3] if len(sys.argv) > 3 else "light") + "\")"])
sys.exit(0)
from PIL import ImageGrab
ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save("/tmp/shots/hub_%d.png" % sw)
root.destroy()
