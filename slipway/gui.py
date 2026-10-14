"""Slipway window: the list of custom firmware, your firmware folder, installing on the FM-1, and the safety prompts.

Look: nautical, to match the other firmware names (Sloop, Felucca, Jangada...): navy and sea-green with brass trim,
a sailboat on a slipway for the logo, and the FM-1's own keyboard drawn along the quayside."""
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from tkinter import filedialog, simpledialog, ttk

from . import catalog, catalogue, dialogs, flasher, github, library, recovery_guide

COLS = (("tick", "On FM-1", 66), ("name", "Firmware", 130), ("author", "Made by", 150), ("version", "Latest", 80),
        ("released", "Released", 120), ("kind", "Type", 100), ("keys", "Keys it uses", 120), ("infolder", "In folder", 70), ("description", "What it is", 240))
FCOLS = (("name", "File", 200), ("version", "Version", 90), ("size", "Size", 80), ("note", "Note", 420))

# Day: sand and chart paper with navy ink.  Night: deep navy water with brass and sea-glass.
LIGHT = dict(bg="#f2ede1", panel="#fffdf7", ink="#0f2a3d", muted="#5d7686", accent="#1f6f8b", accent_ink="#ffffff",
             brass="#b8892b", line="#d6cdb8", ok="#1c8f6a", bad="#b83b2e", key_w="#fffdf7", key_b="#0f2a3d",
             row_alt="#f8f3e6", sel="#cfe3ea", sel_ink="#0f2a3d", head="#e7dfcb", sea="#2a8aa6", hull="#0f2a3d",
             sail="#fffdf7")
DARK = dict(bg="#151213", panel="#1f1a1b", ink="#f2ede9", muted="#a39a98", accent="#e0b04a", accent_ink="#1a1405",
            brass="#e0b04a", line="#362e30", ok="#4fd1a5", bad="#ff7a68", key_w="#e9e2de", key_b="#0b0909",
            row_alt="#1a1516", sel="#4a3a1e", sel_ink="#ffffff", head="#2a2325", sea="#2f7f95", hull="#0b0909",
            sail="#f2ede9")


class Slipway:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.items = {}                    # list iid -> firmware dict
        self.files = {}                    # folder-list iid -> file entry
        self.cache = github.Cache(os.path.join(library.data_dir(), "cache.json"))
        self.repos = self._repos()
        self.dark = bool(library.load_state().get("dark", True))
        self.pal = DARK if self.dark else LIGHT
        self.device = ("none", "Press Check FM-1 to see what is on it.")
        self._pending_record = None
        self._errors = []
        self.idents = []
        root.title("Slipway")
        sh = root.winfo_screenheight()
        root.geometry("1120x%d" % min(820, sh - 80))
        root.minsize(780, min(600, sh - 80))
        self.sort = None                   # (column key, reversed) once a column heading has been clicked
        self.status = tk.StringVar(value="Press Refresh to look up the firmwares on GitHub.")
        self._style()
        self._build()
        self._paint()
        self._fit_min_size()
        self._show_folder()
        self._update_banner()
        root.after(150, self._poll)
        self.refresh()
        root.after(900, self._auto_check)
        root.after(500, self._fit_min_size)         # measure again once the fonts have settled

    # ------------------------------------------------------------ repo list
    def _extra_path(self):
        return os.path.join(library.data_dir(), "extra_repos.txt")

    def _repos(self):
        repos = [s["repo"] for s in catalog.SEED]
        try:
            with open(self._extra_path(), "r", encoding="utf-8") as f:
                repos += [l.strip() for l in f if github.parse_repo(l)]
        except OSError:
            pass
        return list(dict.fromkeys(repos))

    # ------------------------------------------------------------ look
    def _pick_font(self):
        """A real UI font (so the tick marks and text are crisp), whatever the computer has."""
        try:
            have = set(tkfont.families(self.root))
            fam = next((f for f in ("Segoe UI", "Helvetica Neue", "Noto Sans", "DejaVu Sans", "Liberation Sans", "Arial") if f in have), None)
            if fam:
                for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
                    tkfont.nametofont(name).configure(family=fam, size=10)
            self.family = fam or "TkDefaultFont"
        except Exception:
            self.family = "TkDefaultFont"

    def _style(self):
        self._pick_font()
        p = self.pal
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        self.root.configure(bg=p["bg"])
        st.configure(".", background=p["bg"], foreground=p["ink"], fieldbackground=p["panel"], bordercolor=p["line"],
                     lightcolor=p["bg"], darkcolor=p["bg"], troughcolor=p["head"], focuscolor=p["brass"])
        st.configure("TFrame", background=p["bg"])
        st.configure("TLabel", background=p["bg"], foreground=p["ink"])
        st.configure("Muted.TLabel", foreground=p["muted"])
        st.configure("Warn.TLabel", foreground=p["bad"])
        st.configure("TLabelframe", background=p["bg"], bordercolor=p["line"])
        st.configure("TLabelframe.Label", background=p["bg"], foreground=p["brass"], font=("TkDefaultFont", 9, "bold"))
        st.configure("TButton", background=p["panel"], foreground=p["ink"], bordercolor=p["line"], padding=(10, 5))
        st.map("TButton", background=[("active", p["head"]), ("disabled", p["bg"])], foreground=[("disabled", p["muted"])])
        st.configure("Accent.TButton", background=p["accent"], foreground=p["accent_ink"], bordercolor=p["brass"],
                     padding=(16, 6), font=("TkDefaultFont", 10, "bold"))
        st.map("Accent.TButton", background=[("active", p["sea"]), ("disabled", p["line"])],
               foreground=[("disabled", p["muted"])])
        st.configure("Treeview", background=p["panel"], fieldbackground=p["panel"], foreground=p["ink"],
                     bordercolor=p["line"], rowheight=26)
        st.map("Treeview", background=[("selected", p["sel"])], foreground=[("selected", p["sel_ink"])])
        st.configure("Treeview.Heading", background=p["head"], foreground=p["ink"], bordercolor=p["line"],
                     relief="flat", font=("TkDefaultFont", 9, "bold"), padding=(6, 5))
        st.configure("Vertical.TScrollbar", background=p["head"], troughcolor=p["bg"], bordercolor=p["bg"],
                     arrowcolor=p["muted"])

    def _paint(self):
        """(Re)colours everything that is coloured by hand: the header drawing, the rows and the status chip."""
        p = self.pal
        self.chip.configure(bg=p["bg"], fg=self._chip_colour())
        self._draw_chip()
        self.header.configure(bg=p["bg"])
        self.tree.tag_configure("odd", background=p["row_alt"])
        self.tree.tag_configure("on", foreground=p["ok"])
        self.ftree.tag_configure("odd", background=p["row_alt"])
        self.ftree.tag_configure("bad", foreground=p["bad"])
        self._draw_header()
        self.dark_btn.configure(text="Day mode" if self.dark else "Night mode")

    def toggle_dark(self):
        self.dark = not self.dark
        self.pal = DARK if self.dark else LIGHT
        s = library.load_state()
        s["dark"] = self.dark
        library.save_state(s)
        self._style()
        self._paint()

    def _draw_header(self):
        c, p = self.header, self.pal
        c.delete("all")
        w = max(c.winfo_width(), 700)
        # logo: a sailboat on a slipway (a ramp of piano keys running into the water)
        x0, y0 = 14, 6
        c.create_oval(x0, y0, x0 + 64, y0 + 64, fill=p["sea"], outline=p["brass"], width=2)
        c.create_polygon(x0 + 18, y0 + 12, x0 + 18, y0 + 38, x0 + 40, y0 + 38, fill=p["sail"], outline="")      # mainsail
        c.create_polygon(x0 + 14, y0 + 16, x0 + 14, y0 + 38, x0 + 5, y0 + 38, fill=p["sail"], outline="")       # jib
        c.create_line(x0 + 18, y0 + 8, x0 + 18, y0 + 42, fill=p["hull"], width=2)                               # mast
        c.create_polygon(x0 + 6, y0 + 41, x0 + 44, y0 + 41, x0 + 38, y0 + 49, x0 + 12, y0 + 49, fill=p["hull"], outline="")   # hull
        for i in range(6):                                                                                      # keys on the ramp
            kx = x0 + 10 + i * 8
            c.create_rectangle(kx, y0 + 52, kx + 7, y0 + 58, fill=p["key_w"], outline=p["hull"])
        for i in (0, 1, 3, 4):
            kx = x0 + 10 + i * 8 + 5
            c.create_rectangle(kx, y0 + 52, kx + 5, y0 + 56, fill=p["key_b"], outline="")
        c.create_text(94, 28, text="Slipway", anchor="w", fill=p["ink"], font=(self.family, 22, "bold"))
        c.create_text(96, 54, text="launch firmware onto your FM-1", anchor="w", fill=p["muted"], font=(self.family, 10))
        # the quayside: the FM-1's own keyboard (16 white + 11 black) drawn along the water
        kx0, kx1, ky0, ky1 = 340, max(w - 24, 580), 12, 58
        kw = (kx1 - kx0) / 16.0
        for i in range(16):
            c.create_rectangle(kx0 + i * kw, ky0, kx0 + (i + 1) * kw, ky1, fill=p["key_w"], outline=p["line"])
        white = ["C", "D", "E", "F", "G", "A", "B"]
        for i in range(15):
            if white[i % 7] in ("C", "D", "F", "G", "A"):
                bx = kx0 + (i + 1) * kw
                c.create_rectangle(bx - kw * 0.3, ky0, bx + kw * 0.3, ky0 + (ky1 - ky0) * 0.62, fill=p["key_b"], outline="")
        for x in range(0, w, 24):                                    # a line of waves along the foot of the header
            c.create_arc(x, 66, x + 24, 82, start=0, extent=180, style="arc", outline=p["sea"], width=2)
        c.create_line(0, 77, w, 77, fill=p["brass"], width=2)

    # ------------------------------------------------------------ layout
    def _build(self):
        self.header = tk.Canvas(self.root, height=80, highlightthickness=0, bd=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", lambda e: self._draw_header())

        bar = ttk.Frame(self.root, padding=(14, 8))
        bar.pack(fill="x")
        self.bar = bar
        # The buttons are packed first, so they always keep their full size; the FM-1 status text takes what is left
        # (and wraps onto a second line when it is short of room) instead of the buttons being squeezed.
        self.bar_buttons = ttk.Frame(bar)
        self.bar_buttons.pack(side="right")
        ttk.Button(self.bar_buttons, text="Check FM-1", command=self.check_device).pack(side="left", padx=(3, 3))
        for text, cmd in (("+ Add repo", self.add_repo), ("Find more on GitHub", self.discover), ("Refresh", self.refresh)):
            ttk.Button(self.bar_buttons, text=text, command=cmd).pack(side="left", padx=3)
        self.dark_btn = ttk.Button(self.bar_buttons, text="Night mode", command=self.toggle_dark)
        self.dark_btn.pack(side="left", padx=3)
        self.chip_icon = tk.Canvas(bar, width=26, height=26, highlightthickness=0, bd=0)
        self.chip_icon.pack(side="left")
        self.chip = tk.Label(bar, text="FM-1:  not checked yet", anchor="w", justify="left", font=(self.family, 11, "bold"))
        self.chip.pack(side="left", padx=(4, 8), fill="x", expand=True)

        bf = ttk.Frame(self.root, padding=(14, 0, 14, 4))
        bf.pack(fill="x")
        self.banner = ttk.Label(bf, wraplength=900, style="Warn.TLabel", justify="left")
        self.banner.pack(side="left", fill="x", expand=True)
        self.banner_btn = ttk.Button(bf, text="Save stock V15 now...", command=self.add_stock)   # shown only while it is needed

        mid = ttk.Frame(self.root, padding=(14, 0))
        self.tree = ttk.Treeview(mid, columns=[c[0] for c in COLS], show="headings", height=5, selectmode="browse")
        for key, title, width in COLS:
            self.tree.heading(key, text=title, command=lambda k=key: self.sort_by(k))
            self.tree.column(key, width=width, minwidth=50, stretch=(key == "description"),
                             anchor="center" if key in ("tick", "infolder") else "w")
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda e: self.open_page())
        self.tree.bind("<Return>", lambda e: self.open_page())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._selected_changed())

        act = ttk.Frame(self.root, padding=(14, 6))
        self.detail = ttk.Label(act, text="", wraplength=1000, justify="left")
        self.detail.pack(fill="x")
        row = ttk.Frame(act)
        row.pack(fill="x", pady=(6, 0))
        self.install_btn = ttk.Button(row, text="Launch on FM-1", style="Accent.TButton", command=self.install_selected)
        self.install_btn.pack(side="left")
        self.download_btn = ttk.Button(row, text="Download to folder", command=self.download_selected)
        self.download_btn.pack(side="left", padx=(8, 0))
        ttk.Button(row, text="Open releases page", command=self.open_page).pack(side="left", padx=8)

        ff = ttk.LabelFrame(self.root, text="Your firmware folder (the boatyard)", padding=(10, 6))
        self.folder_label = ttk.Label(ff, text="", style="Muted.TLabel")
        self.folder_label.pack(anchor="w")
        fm = ttk.Frame(ff)
        fm.pack(fill="x", pady=4)
        self.ftree = ttk.Treeview(fm, columns=[c[0] for c in FCOLS], show="headings", height=3, selectmode="browse")
        for key, title, width in FCOLS:
            self.ftree.heading(key, text=title)
            self.ftree.column(key, width=width, minwidth=50, stretch=(key == "note"))
        fs = ttk.Scrollbar(fm, orient="vertical", command=self.ftree.yview)
        self.ftree.configure(yscrollcommand=fs.set)
        self.ftree.pack(side="left", fill="x", expand=True)
        fs.pack(side="right", fill="y")
        fr = ttk.Frame(ff)
        fr.pack(fill="x")
        ttk.Button(fr, text="Launch selected file", command=self.install_from_folder).pack(side="left")
        ttk.Button(fr, text="Open folder", command=self.open_folder).pack(side="left", padx=6)
        ttk.Button(fr, text="Change folder...", command=self.change_folder).pack(side="left")
        ttk.Button(fr, text="Add a .fwsc file...", command=self.import_file).pack(side="left", padx=6)
        wb = ttk.Frame(ff)                                   # its own row, so it can never run off the right edge
        wb.pack(fill="x", pady=(6, 0))
        ttk.Label(wb, text="The way back:", style="Muted.TLabel").pack(side="left")
        ttk.Button(wb, text="Save stock V15", command=self.add_stock).pack(side="left", padx=(8, 0))
        ttk.Button(wb, text="Put stock V15 back", command=self.flash_stock).pack(side="left", padx=6)
        ttk.Button(wb, text="Stuck? Rescue...", command=self.rescue).pack(side="left", padx=(14, 0))
        status = ttk.Label(self.root, textvariable=self.status, padding=(14, 5), anchor="w", style="Muted.TLabel")

        # Packing order matters: whatever is packed first gets its space first. The bottom panels go first so a short
        # window (or a scaled Windows display) squeezes the firmware list, never the folder box or the buttons.
        status.pack(fill="x", side="bottom")
        ff.pack(fill="x", side="bottom", padx=14, pady=(8, 4))
        act.pack(fill="x", side="bottom")
        mid.pack(fill="both", expand=True)
        self._wide_rows = [fr, wb, row]
        self.root.bind("<Configure>", self._rewrap, add="+")

    def _rewrap(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        w = self.root.winfo_width()
        self.banner.config(wraplength=max(300, w - 260))
        self.detail.config(wraplength=max(400, w - 40))
        # the status text wraps in whatever room the buttons leave
        self.chip.config(wraplength=max(160, w - self.bar_buttons.winfo_reqwidth() - 80))

    def _fit_min_size(self):
        """The window can't be made narrower than the widest row of buttons needs, so nothing is ever squeezed out of sight."""
        self.root.update_idletasks()
        need = 0
        for w in self._wide_rows:
            need = max(need, w.winfo_reqwidth())
        need += 70                                     # the margins around them
        need = max(780, need, self.bar_buttons.winfo_reqwidth() + 230)
        sh = self.root.winfo_screenheight()
        # tall enough that the firmware list keeps several rows (the root's natural height includes five of them)
        line = tkfont.Font(font="TkDefaultFont").metrics("linespace")
        tall = self.root.winfo_reqheight() - self.detail.winfo_reqheight() + 5 * line      # room for a 5-line description
        tall = min(tall, sh - 80)
        self.root.minsize(min(need, self.root.winfo_screenwidth()), tall)
        if self.root.winfo_ismapped() and (self.root.winfo_width() < need or self.root.winfo_height() < tall):
            self.root.geometry("%dx%d" % (max(need, self.root.winfo_width()), max(tall, self.root.winfo_height())))

    # ------------------------------------------------------------ data
    def refresh(self, discover=False):
        self.status.set("Looking up firmwares on GitHub...")
        threading.Thread(target=self._scan, args=(list(self.repos), discover), daemon=True).start()

    def discover(self):
        self.refresh(discover=True)

    def _scan(self, repos, discover):
        cache = self.cache.load()
        errors = []
        try:
            if discover:
                for name in github.search(catalog.SEARCHES):
                    if name.lower() not in [r.lower() for r in repos]:
                        repos.append(name)
                        with open(self._extra_path(), "a", encoding="utf-8") as f:
                            f.write(name + "\n")
        except github.GitHubError as e:
            errors.append(str(e))
        out = []
        cat, ent = None, cache.get("__catalogue__")
        if ent and self.cache.fresh(ent) and not discover:
            cat = ent["items"]
        else:
            data = catalogue.fetch()
            if data:
                cat = catalogue.entries(data)
                cache["__catalogue__"] = {"at": time.time(), "items": cat}
            elif ent:
                cat = ent["items"]                       # stale is better than nothing
            else:
                errors.append("Couldn't reach the firmware catalogue, so only the firmware Slipway already knows is listed.")
        out.extend(cat or [])
        have = {i["repo"].lower() for i in out}
        for repo in repos:                                # your own additions, and the fallback when there is no catalogue
            if repo.lower() in have:
                continue
            entry = cache.get(repo)
            if entry and self.cache.fresh(entry) and not discover:
                info = entry["info"]
            else:
                try:
                    info = github.describe(repo)
                    cache[repo] = {"at": time.time(), "info": info}
                except github.GitHubError as e:
                    errors.append(str(e))
                    info = entry.get("info") if entry else None
            if info:
                out.append(info)
        try:
            self.cache.save(cache)
        except OSError:
            pass
        self.q.put(("list", out, sorted(set(errors)), repos))

    def _poll(self):
        try:
            while True:
                kind, *rest = self.q.get_nowait()
                if kind == "list":
                    self.repos = list(dict.fromkeys(rest[2]))
                    self._show_list(rest[0], rest[1])
                elif kind == "status":
                    self.status.set(rest[0])
                elif kind == "mismatch":
                    self._pending_record = None
                elif kind == "device":
                    self._set_device(*rest)
                elif kind == "done_flash":
                    self._flash_done(*rest)
                elif kind == "done_download":
                    label, path, new = rest
                    self.download_btn.state(["!disabled"])
                    self._show_folder()
                    self._selected_changed()
                    self.refresh()
                    self.status.set("Downloaded %s into your firmware folder." % label if new else
                                    "%s was already in your firmware folder (identical file), so it wasn't saved twice." % label)
                elif kind == "fail_download":
                    self.download_btn.state(["!disabled"])
                    self.status.set("Stopped.")
                    dialogs.showerror("Slipway", rest[0])
                elif kind == "fail":
                    self._pending_record = None
                    self.status.set("Stopped.")
                    dialogs.showerror("Slipway", rest[0])
        except queue.Empty:
            pass
        self.root.after(150, self._poll)

    def _merge(self, info):
        known = {s["repo"].lower(): s for s in catalog.SEED}.get(info["repo"].lower(), {})
        fw = dict(info)
        fw["keys"] = known.get("keys", [])
        fw["safety"] = known.get("safety", "")
        fw["checked"] = known.get("checked", False)
        return fw

    def _in_folder(self, fw):
        """The copy already in the firmware folder, if any: exact (same SHA-256 as the catalogue) when known."""
        f = fw["files"][0] if fw.get("files") else {}
        sha = f.get("sha256") or None
        names = [fw["name"], fw["repo"].split("/")[-1], library.guess_name(f.get("name", ""))[0]]
        return library.find_in_folder(names, fw["version"], sha=sha) or (
            library.find_in_folder(names, fw["version"]) if not sha else None)

    def _show_list(self, infos, errors):
        rec = library.load_state().get("installed") or {}
        rows = []
        for info in infos:
            fw = self._merge(info)
            keys = " + ".join(fw["keys"]) if fw["keys"] else ("not checked" if not fw["checked"] else "none documented")
            on = bool(rec and not rec.get("stock") and rec.get("repo", "").lower() == fw["repo"].lower())
            have = self._in_folder(fw) if fw["files"] else None
            kind = ", ".join(fw.get("kinds") or []) + (" (beta)" if fw.get("beta") else "")
            rows.append((("✓" if on else "", fw["name"], fw["author"], fw["version"] or "no release",
                          library.released_text(fw.get("published", "")), kind, keys, "✓" if have else "",
                          fw["description"]), on, fw))
        self._rows = rows
        self._errors = errors
        self.idents = catalogue.idents(infos)
        self._fill_tree()
        self._update_banner()
        self.status.set("%d firmwares. Double-click one to open its releases page. Click a column heading to sort (Released: newest first)." % len(infos))

    @staticmethod
    def _sort_key(col_index, values):
        """Sort key for one cell: names without case, versions by their numbers (1.10 after 1.9), empty cells last."""
        v = values[col_index]
        if col_index == 4:                                    # released: by the date itself, ignoring the NEW tag
            return (0, v[:10])
        if col_index == 3:                                    # version
            nums = tuple(int(n) for n in re.findall(r"\d+", v)) if v != "no release" else ()
            return (0, nums, v) if nums else (1, (), v)
        return (1, v) if v == "" else (0, v.casefold())

    def _fill_tree(self):
        """(Re)build the firmware list from self._rows in the chosen order, keeping the selected row selected."""
        keep = None
        cur = self._current() if self.items else None
        if cur:
            keep = cur["repo"].lower()
        rows = list(self._rows)
        if self.sort:
            col, rev = self.sort
            idx = [c[0] for c in COLS].index(col)
            if col in ("tick", "infolder"):                       # the tick columns: ticked vs not ticked, flips on a second click
                rows.sort(key=lambda r: r[0][idx] != "", reverse=rev)
            else:
                full = [r for r in rows if r[0][idx] != "" and not (idx == 3 and r[0][idx] == "no release")]
                empty = [r for r in rows if r not in full]        # blanks always stay at the bottom, whichever way it sorts
                full.sort(key=lambda r: self._sort_key(idx, r[0]), reverse=rev)
                rows = full + empty
        self.tree.delete(*self.tree.get_children())
        self.items = {}
        reselect = None
        for i, (values, on, fw) in enumerate(rows):
            iid = self.tree.insert("", "end", values=values, tags=tuple(t for t, c in (("odd", i % 2), ("on", on)) if c))
            self.items[iid] = fw
            if keep and fw["repo"].lower() == keep:
                reselect = iid
        for key, title, _w in COLS:                               # an arrow on the heading that is sorting
            arrow = ""
            if self.sort and self.sort[0] == key:
                arrow = "  ▼" if self.sort[1] else "  ▲"
            self.tree.heading(key, text=title + arrow)
        if reselect:
            self.tree.selection_set(reselect)
            self.tree.see(reselect)

    def sort_by(self, col):
        """Clicking a heading sorts by it; clicking it again reverses. The two tick columns show the ticked rows first."""
        if self.sort and self.sort[0] == col:
            self.sort = (col, not self.sort[1])
        else:
            self.sort = (col, col in ("tick", "infolder", "released"))   # first click: ticked ones on top / newest first
        self._fill_tree()

    def _update_banner(self):
        msgs = list(self._errors)
        need_stock = not library.stock_ready()
        if need_stock:
            msgs.append("Save the stock V15 firmware (M-VAVE's own file) so you can always get back to port.")
        self.banner.config(text=" ".join(msgs))
        if need_stock:
            self.banner_btn.pack(side="right", padx=(8, 0))
        else:
            self.banner_btn.pack_forget()

    # ------------------------------------------------------------ the folder
    def _show_folder(self):
        self.ftree.delete(*self.ftree.get_children())
        self.files = {}
        self.folder_label.config(text=library.firmware_dir())
        try:
            entries = library.mark_duplicates(library.folder_files())
        except OSError:
            entries = []
        for i, e in enumerate(entries):
            note = e["why"] if not e["ok"] else ("Same file as %s: you can delete this copy." % e["dup_of"] if e.get("dup_of") else "")
            iid = self.ftree.insert("", "end", values=(os.path.basename(e["path"]), e["version"], "%d KB" % (e["size"] // 1024), note),
                                    tags=tuple(t for t, c in (("odd", i % 2), ("bad", not e["ok"])) if c))
            self.files[iid] = e
        if not entries:
            self.ftree.insert("", "end", values=("(empty: downloads and files you add appear here)", "", "", ""))

    def open_folder(self):
        path = library.firmware_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)                                   # noqa
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            dialogs.showinfo("Slipway", path)

    def change_folder(self):
        path = filedialog.askdirectory(title="Choose the folder for your firmware files", initialdir=library.firmware_dir())
        if not path:
            return
        try:
            library.set_firmware_dir(path)
        except library.LibraryError as e:
            dialogs.showerror("Slipway", str(e))
            return
        self._show_folder()
        self.refresh()

    # ------------------------------------------------------------ list actions
    def _current(self):
        sel = self.tree.selection()
        return self.items.get(sel[0]) if sel else None

    def _selected_changed(self):
        fw = self._current()
        if not fw:
            return
        parts = [fw["description"] or "No description.", "By %s." % fw["author"]]
        parts += library.warnings_for(fw)
        if not fw["files"]:
            parts.append("No .fwsc file attached to its latest release%s." % ("" if fw["has_releases"] else " (no releases)"))
        elif self._in_folder(fw):
            parts.append("Already in your firmware folder: Launch will use that copy instead of downloading it again.")
        self.detail.config(text="\n".join(parts))
        self.install_btn.state(["!disabled"] if fw["files"] else ["disabled"])
        self.download_btn.state(["!disabled"] if fw["files"] else ["disabled"])

    def open_page(self):
        fw = self._current()
        if fw:
            webbrowser.open(fw["releases_url"] if fw["has_releases"] else fw["repo_url"])

    def _confirm_safety(self, fw):
        if not library.needs_ack(fw):
            return True
        text = "\n\n".join(library.warnings_for(fw))
        if not library.stock_ready():
            text += "\n\nYou haven't saved the stock V15 firmware yet. Do that first so you can always go back."
        if dialogs.askyesno("Before you use %s" % fw["name"], text + "\n\nI've read this and I know how to get back. Continue?",
                               icon="warning"):
            library.acknowledge(fw)
            return True
        return False

    # ------------------------------------------------------------ installing
    def _ready_to_flash(self):
        """Makes sure the installer tool and its MIDI libraries are in place. False = stopped (person told why)."""
        try:
            if not flasher.tool_info():
                if not dialogs.askyesno("Installer tool", "Slipway installs by running Felucca's own installer script "
                                           "(fm1_install.py, GPL-3.0, by Leo Kuroshita). Download it from GitHub now?"):
                    return False
                info = flasher.fetch_tool()
                self.status.set("Installer saved (SHA-256 %s...)." % info["sha256"][:12])
        except library.LibraryError as e:
            dialogs.showerror("Slipway", str(e))
            return False
        need = flasher.missing_modules()
        if need:
            if not dialogs.askyesno("MIDI libraries", "The installer needs: %s.\nInstall them now with pip?" % ", ".join(need)):
                return False
            ok, out = flasher.install_modules()
            if not ok:
                dialogs.showerror("Slipway", "Couldn't install them:\n" + out)
                return False
        return True

    def _run_flasher(self, job, title):
        self.status.set(title)

        def work():
            try:
                self.q.put(("done_flash",) + tuple(job()))
            except library.LibraryError as e:
                self.q.put(("fail", str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _flash_done(self, ok, msg, lines):
        self.status.set(msg)
        if ok and self._pending_record:
            library.record_install(**self._pending_record)
            self._pending_record = None
            self.refresh()
            self._show_folder()
            self.root.after(2500, self.check_device_quiet)
        (dialogs.showinfo if ok else dialogs.showwarning)("Slipway", msg + "\n\n" + "\n".join(lines[-12:]))

    def check_device(self):
        if self._ready_to_flash():
            self.check_device_quiet()

    def check_device_quiet(self):
        self.status.set("Asking the FM-1 who it is (nothing is written)...")

        def work():
            try:
                _found, lines = flasher.device_info()
            except library.LibraryError as e:
                self.q.put(("device", "none", str(e)))
                return
            names = [s["name"] for s in catalog.SEED] + list(catalog.KNOWN_NAMES)
            kind, text = flasher.detect(lines, library.load_state().get("installed"), names, getattr(self, "idents", ()))
            self.q.put(("device", kind, text))
        threading.Thread(target=work, daemon=True).start()

    def _auto_check(self):
        """On start-up, look quietly if everything needed is already in place. Never prompts or downloads."""
        if flasher.tool_info() and not flasher.missing_modules():
            self.check_device_quiet()

    def _chip_colour(self):
        return {"original": self.pal["ok"], "original_guess": self.pal["ok"], "custom": self.pal["brass"],
                "loader": self.pal["bad"]}.get(self.device[0], self.pal["muted"])

    def _draw_chip(self):
        """The status mark, drawn (not typed) so it looks the same on every computer: a tick in a ring for the
        original firmware, a filled dot for custom firmware, a cross for an unfinished install, an empty ring otherwise."""
        c, kind, col = self.chip_icon, self.device[0], self._chip_colour()
        c.configure(bg=self.pal["bg"])
        c.delete("all")
        c.create_oval(2, 2, 24, 24, outline=col, width=2)
        if kind in ("original", "original_guess"):
            c.create_line(7, 14, 12, 19, 19, 8, fill=col, width=3, capstyle="round", joinstyle="round")
        elif kind == "custom":
            c.create_oval(8, 8, 18, 18, fill=col, outline="")
        elif kind == "loader":
            c.create_line(8, 8, 18, 18, fill=col, width=3)
            c.create_line(18, 8, 8, 18, fill=col, width=3)

    def _set_device(self, kind, text):
        self.device = (kind, text)
        self.chip.configure(text="FM-1:  %s" % text, fg=self._chip_colour())
        self._draw_chip()
        self.status.set(text)

    def _stock_gate(self, is_stock):
        """Stock first, every time: returns True when this install may go ahead. Otherwise explains, and for 'put it back'
        offers to flash the stock V15 right now."""
        block = library.stock_first_block(is_stock)
        if not block:
            return True
        if block == "nostock":
            dialogs.showwarning("Save the stock V15 first",
                                "Before any custom firmware goes on, Slipway needs the official M-VAVE V15 saved as your way back.\n\n"
                                "Use 'Save stock V15 now...' (below the folder list), then try again.")
            return False
        last = (library.load_state().get("installed") or {})
        what = ("%s %s" % (last.get("name", "A custom firmware"), last.get("version", ""))).strip()
        if dialogs.askyesno("Put stock V15 back first",
                            "%s is on the FM-1 now. To keep the way back safe, Slipway only installs a custom firmware on top "
                            "of the stock V15 - every time.\n\nPut the stock V15 back now? After that you can install this one."
                            % what, icon="warning"):
            self.flash_stock()
        return False

    def _install_file(self, path, name, version, repo, is_stock):
        """Common last steps for every install: the file is checked, the person confirms, then it is flashed."""
        why = flasher.can_flash(path, is_stock)
        if why:
            dialogs.showerror("Slipway", why)
            return
        if not self._stock_gate(is_stock):
            return
        if not self._ready_to_flash():
            return
        label = ("%s %s" % (name, version)).strip()
        if not dialogs.askyesno("Install %s" % label, "Install %s on the FM-1 now?\n\n- Do not unplug the FM-1 while it writes.\n"
                                   "- If it is interrupted, press Install again and it finishes.\n- It must be plugged in by USB." % label,
                                   icon="warning"):
            return
        self._pending_record = dict(name=name, repo=repo, version=version, stock=is_stock)
        self._run_flasher(lambda: flasher.flash(path, is_stock), "Installing %s... do not unplug the FM-1." % label)

    def install_selected(self):
        fw = self._current()
        if not fw or not fw["files"]:
            dialogs.showinfo("Slipway", "Select a firmware that has a release file first.")
            return
        if not self._stock_gate(False):            # before any download: no point fetching what can't be installed yet
            return
        if not self._confirm_safety(fw):
            return
        have = self._in_folder(fw)
        if have:                                   # already here: never download it twice
            self._install_file(have["path"], fw["name"], fw["version"], fw["repo"], False)
            return
        if not self._ready_to_flash():
            return
        label = "%s %s" % (fw["name"], fw["version"])
        if not dialogs.askyesno("Install %s" % label, "Download %s into your firmware folder and install it on the FM-1 now?\n\n"
                                   "- Do not unplug the FM-1 while it writes.\n- If it is interrupted, press Install again.\n"
                                   "- It must be plugged in by USB." % label, icon="warning"):
            return
        self._pending_record = dict(name=fw["name"], repo=fw["repo"], version=fw["version"], stock=False)

        def job():
            path, _new = self._fetch_to_folder(fw, "installed")
            self.q.put(("status", "Installing %s... do not unplug the FM-1." % label))
            return flasher.flash(path, False)
        self._run_flasher(job, "Downloading %s..." % label)

    def _fetch_to_folder(self, fw, verb):
        """Download a catalogue/GitHub firmware, check it against the catalogue SHA-256, and store it in the firmware
        folder (an identical file already there is reused, never saved twice). Runs on a worker thread.
        Returns (path, is_new_file). Raises LibraryError."""
        label = "%s %s" % (fw["name"], fw["version"])
        want_sha = (fw["files"][0].get("sha256") or "").lower()
        asset = fw["files"][0]
        if not asset.get("url"):                         # catalogue entries: find the real file on the project's GitHub release
            try:
                asset = catalogue.resolve_asset(fw, github.fetch)
            except github.GitHubError as e:
                raise library.LibraryError(str(e))
            if not asset:
                raise library.LibraryError("%s has no downloadable .fwsc on GitHub (use 'Open releases page')." % fw["name"])
        tmp = library.download(asset["url"])
        try:
            _size, sha = library.check_file(tmp)
            if want_sha and sha != want_sha:
                self.q.put(("mismatch", fw["name"]))
                raise library.LibraryError("The downloaded file doesn't match the catalogue's checksum for %s, so it was not "
                                           "%s. (It may be a newer release than the catalogue has seen. Open the "
                                           "releases page to get it yourself, then use 'Add a .fwsc file'.)" % (label, verb))
            return library.store_in_folder(tmp, fw["name"], fw["version"])      # identical file already there? reuse
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def download_selected(self):
        """Put the selected firmware in the firmware folder without installing it."""
        fw = self._current()
        if not fw or not fw["files"]:
            dialogs.showinfo("Slipway", "Select a firmware that has a release file first.")
            return
        have = self._in_folder(fw)
        if have:
            self.status.set("%s %s is already in your firmware folder." % (fw["name"], fw["version"]))
            dialogs.showinfo("Slipway", "%s %s is already in your firmware folder, so nothing was downloaded.\n\n%s"
                                % (fw["name"], fw["version"], have["path"]))
            return
        label = "%s %s" % (fw["name"], fw["version"])
        self.status.set("Downloading %s..." % label)
        self.download_btn.state(["disabled"])

        def work():
            try:
                path, new = self._fetch_to_folder(fw, "saved")
                self.q.put(("done_download", label, path, new))
            except library.LibraryError as e:
                self.q.put(("fail_download", str(e)))
            except Exception as e:                       # never leave the button stuck disabled
                self.q.put(("fail_download", "Download failed: %s" % e))
        threading.Thread(target=work, daemon=True).start()

    def install_from_folder(self):
        sel = self.ftree.selection()
        e = self.files.get(sel[0]) if sel else None
        if not e:
            dialogs.showinfo("Slipway", "Select a file in the folder list first.")
            return
        name, version = library.guess_name(e["path"])
        known = {s["name"].lower(): s for s in catalog.SEED}.get(name.lower(), {})
        fw = {"name": known.get("name", name), "version": version, "repo": known.get("repo", ""),
              "keys": known.get("keys", []), "safety": known.get("safety", ""), "checked": known.get("checked", False)}
        try:
            stock = library.load_state()["stock"]
            is_stock = bool(stock) and library.check_file(e["path"])[1] == stock["sha256"]
        except library.LibraryError as err:
            dialogs.showerror("Slipway", str(err))
            return
        if not self._stock_gate(is_stock):
            return
        if not is_stock and not self._confirm_safety(fw):
            return
        self._install_file(e["path"], fw["name"], version, fw["repo"], is_stock)

    def import_file(self):
        """Add a .fwsc from anywhere. It is copied into the firmware folder (unless an identical file is already there)."""
        path = filedialog.askopenfilename(title="Choose an FM-1 firmware file", initialdir=library.firmware_dir(),
                                          filetypes=[("FM-1 firmware", "*.fwsc")])
        if not path:
            return
        try:
            library.check_file(path)
            name, version = library.guess_name(path)
            _dest, new = library.store_in_folder(path, name, version)
        except library.LibraryError as e:
            dialogs.showerror("Slipway", str(e))
            return
        self._show_folder()
        self.refresh()
        self.status.set("Added to your firmware folder." if new else
                        "That file is already in your firmware folder, so it wasn't copied again.")

    def flash_stock(self):
        st = library.load_state()["stock"]
        if not st:
            dialogs.showinfo("Slipway", "Save the stock V15 firmware first.")
            return
        self._install_file(st["file"], "the stock V15 firmware", "", "", True)

    # ------------------------------------------------------------ rescue
    def _rescue_options(self):
        """What can be put on a stuck FM-1 right now: [(key, label)]. Nothing is offered that isn't actually available."""
        # Stock first, every time: a stuck FM-1 only ever gets the stock V15 back here. Custom firmware goes on afterwards
        # through the normal install buttons, once the stock is on.
        opts = []
        if library.stock_ready():
            opts.append(("stock", "The stock V15 firmware I saved (the only way back from here)"))
        return opts

    def rescue(self):
        """USB rescue: for an FM-1 that is stuck (black screen, install cut short). The person holds OCT- while switching
        it on, then Slipway installs a firmware the normal, checked way."""
        if getattr(self, "_rescue_win", None) and self._rescue_win.winfo_exists():
            self._rescue_win.lift()
            return
        p = self.pal
        win = tk.Toplevel(self.root)
        self._rescue_win = win
        win.title("Stuck? Rescue the FM-1")
        win.configure(bg=p["bg"])
        win.transient(self.root)
        win.resizable(False, False)
        body = ttk.Frame(win, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Stuck? Rescue the FM-1", font=(self.family, 14, "bold")).pack(anchor="w")
        ttk.Label(body, wraplength=520, justify="left", style="Muted.TLabel", text=(
            "Use this if the FM-1 will not start properly, stays on a black screen, or an install was cut short. "
            "USB rescue lets Slipway put a firmware on it again.")).pack(anchor="w", pady=(4, 10))
        steps = ("1.  Switch the FM-1 off. Leave the USB cable plugged in.",
                 "2.  Hold the OCT− button down, and while holding it, switch the FM-1 on. That is USB rescue.",
                 "3.  Choose what to put on it below, then press Install now.")
        for s in steps:
            ttk.Label(body, text=s, wraplength=520, justify="left").pack(anchor="w", pady=1)
        ttk.Label(body, text="What should go on the FM-1?", font=(self.family, 10, "bold")).pack(anchor="w", pady=(12, 2))
        self._rescue_choice = tk.StringVar()
        opts = self._rescue_options()
        for key, label in opts:
            ttk.Radiobutton(body, text=label, value=key, variable=self._rescue_choice).pack(anchor="w", pady=1)
        if opts:
            self._rescue_choice.set(opts[0][0])
        else:
            ttk.Label(body, wraplength=520, justify="left", style="Warn.TLabel", text=(
                "The stock V15 isn't saved yet, so there is nothing to put back. Use 'Save stock V15 now...' (below the folder "
                "list) with M-VAVE's FM-1.fwsc, then open Rescue again.")).pack(anchor="w", pady=2)
        ttk.Label(body, wraplength=520, justify="left", style="Muted.TLabel", text=(
            "Do not unplug the FM-1 while it writes. If Slipway cannot find the FM-1, switch it off and repeat step 2, "
            "then press Install now again.")).pack(anchor="w", pady=(10, 0))
        ttk.Label(body, wraplength=520, justify="left", style="Muted.TLabel", text=(
            "Slipway always goes back to the stock V15 first. Once it is on, you can install a custom firmware again.")
                  ).pack(anchor="w", pady=(6, 0))
        row = ttk.Frame(body)
        row.pack(fill="x", pady=(14, 0))
        go = ttk.Button(row, text="Install now", style="Accent.TButton", command=self._rescue_go)
        go.pack(side="left")
        if not opts:
            go.state(["disabled"])
        ttk.Button(row, text="Close", command=win.destroy).pack(side="left", padx=8)
        ttk.Separator(body).pack(fill="x", pady=(14, 8))
        ttk.Label(body, text="Black screen, and nothing above finds the FM-1?", font=(self.family, 10, "bold")).pack(anchor="w")
        ttk.Label(body, wraplength=520, justify="left", style="Muted.TLabel", text=(
            "If your computer lists the FM-1 as \"WL82 UBOOT1.00\", there is a full step-by-step recovery that works from "
            "the chip's own rescue mode, with backups and a byte-for-byte check.")).pack(anchor="w", pady=(2, 6))
        ttk.Button(body, text="Full recovery guide...", command=self.recovery_guide).pack(anchor="w")
        self._rescue_go_btn = go
        win.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - win.winfo_reqwidth()) // 2)
        y = self.root.winfo_rooty() + 60
        win.geometry("+%d+%d" % (x, y))

    def _rescue_go(self):
        """Install what was chosen in the rescue window. Each path asks its usual questions (safety notes, confirmation)."""
        choice = self._rescue_choice.get() if getattr(self, "_rescue_choice", None) else ""
        win = getattr(self, "_rescue_win", None)
        if not choice:
            return
        if win is not None and win.winfo_exists():
            win.destroy()
        {"stock": self.flash_stock, "folder": self.install_from_folder, "list": self.install_selected}[choice]()

    def recovery_guide(self):
        """The full USB recovery guide (recovery_guide.py) in a themed, scrollable, read-only window."""
        old = getattr(self, "_guide_win", None)
        if old is not None and old.winfo_exists():
            old.lift()
            return
        p = self.pal
        win = tk.Toplevel(self.root)
        self._guide_win = win
        win.title(recovery_guide.TITLE)
        win.configure(bg=p["bg"])
        win.transient(self.root)
        win.geometry("760x620+%d+%d" % (self.root.winfo_rootx() + 40, self.root.winfo_rooty() + 40))
        win.minsize(520, 360)
        bar = ttk.Frame(win, padding=(12, 10, 12, 10))
        bar.pack(side="bottom", fill="x")
        ttk.Button(bar, text="Copy all", command=lambda: self._guide_copy(win)).pack(side="left")
        ttk.Button(bar, text="Save as text file...", command=self._guide_save).pack(side="left", padx=8)
        ttk.Button(bar, text="Close", command=win.destroy).pack(side="right")
        frame = ttk.Frame(win, padding=(12, 12, 0, 0))
        frame.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical")
        sb.pack(side="right", fill="y")
        txt = tk.Text(frame, wrap="word", bg=p["panel"], fg=p["ink"], relief="flat", padx=14, pady=12, borderwidth=0,
                      highlightthickness=0, font=(self.family, 10), yscrollcommand=sb.set, cursor="arrow")
        txt.pack(side="left", fill="both", expand=True)
        sb.configure(command=txt.yview)
        mono = ("Consolas" if sys.platform.startswith("win") else "DejaVu Sans Mono", 10)
        txt.tag_configure("title", font=(self.family, 15, "bold"), foreground=p["brass"], spacing3=6)
        txt.tag_configure("head", font=(self.family, 11, "bold"), foreground=p["brass"], spacing1=14, spacing3=4)
        txt.tag_configure("code", font=mono, background=p["bg"], lmargin1=24, lmargin2=24, spacing1=2, spacing3=2)
        txt.tag_configure("body", spacing1=2, spacing3=2, lmargin2=14)
        txt.insert("end", recovery_guide.TITLE + "\n", "title")
        txt.insert("end", recovery_guide.INTRO + "\n", "body")
        for head, lines in recovery_guide.SECTIONS:
            txt.insert("end", head + "\n", "head")
            for ln in lines:
                if ln.startswith("  "):
                    txt.insert("end", ln.strip() + "\n", "code")
                else:
                    txt.insert("end", ln + "\n", "body")
        txt.configure(state="disabled")
        self._guide_text = txt

    def _guide_copy(self, win):
        win.clipboard_clear()
        win.clipboard_append(recovery_guide.as_text())
        self.status.set("Recovery guide copied.")

    def _guide_save(self):
        path = filedialog.asksaveasfilename(title="Save the recovery guide", defaultextension=".txt",
                                            initialfile="FM1_recovery_guide.txt", filetypes=[("Text file", "*.txt")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(recovery_guide.as_text())
        except OSError as e:
            dialogs.showerror("Slipway", "Could not save the guide: %s" % e)
            return
        self.status.set("Recovery guide saved to %s" % path)

    def add_stock(self):
        path = filedialog.askopenfilename(title="Choose M-VAVE's official FM-1 firmware", filetypes=[("FM-1 firmware", "*.fwsc")])
        if not path:
            return
        try:
            library.set_stock(path)
        except library.LibraryError as e:
            dialogs.showerror("Slipway", str(e))
            return
        self.status.set("Stock firmware saved. You can always put it back.")
        self._update_banner()

    def add_repo(self):
        text = simpledialog.askstring("Add a firmware", "Paste the GitHub address (or owner/name):", parent=self.root)
        repo = github.parse_repo(text or "")
        if not repo:
            if text:
                dialogs.showinfo("Slipway", "That doesn't look like a GitHub repository address.")
            return
        if repo.lower() not in [r.lower() for r in self.repos]:
            with open(self._extra_path(), "a", encoding="utf-8") as f:
                f.write(repo + "\n")
            self.repos.append(repo)
        self.refresh()
