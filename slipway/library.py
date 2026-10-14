"""Safety checks that stop a bad file or a risky key setup going onto the FM-1 unnoticed, plus downloads and the saved stock firmware.

Flashing itself is in flasher.py."""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request


MIN_BYTES, MAX_BYTES = 100 * 1024, 4 * 1024 * 1024
MARKER, MARKER_WITHIN = b"AC791N", 4096          # every FM-1 .fwsc seen (stock and custom) carries this near the start
ALLOWED_HOSTS = ("github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com", "raw.githubusercontent.com")


class LibraryError(Exception):
    pass


def data_dir():
    forced = os.environ.get("SLIPWAY_DIR")
    if forced:
        path = forced
    elif sys.platform.startswith("win"):
        path = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Slipway")
    elif sys.platform == "darwin":
        path = os.path.expanduser("~/Library/Application Support/Slipway")
    else:
        path = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"), "slipway")
    os.makedirs(path, exist_ok=True)
    return path


def _state_path():
    return os.path.join(data_dir(), "state.json")


def load_state():
    try:
        with open(_state_path(), "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    if not isinstance(d, dict):
        d = {}
    d.setdefault("stock", None)
    d.setdefault("installed", None)
    d.setdefault("dark", True)
    d.setdefault("folder", "")
    d.setdefault("acknowledged", {})
    return d


def save_state(d):
    tmp = _state_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, _state_path())


def package_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def firmware_dir():
    """The folder downloaded firmware goes in (and where you can drop your own .fwsc files). By default a
    'firmware' folder next to Slipway, so it is easy to find; it can be changed in the window."""
    chosen = load_state().get("folder") or ""
    path = chosen if chosen and os.path.isabs(chosen) else os.path.join(package_root(), "firmware")
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w") as f:
            f.write("x")
        os.remove(probe)
    except OSError:                           # read-only install location: fall back to the settings folder
        path = os.path.join(data_dir(), "downloads")
        os.makedirs(path, exist_ok=True)
    return path


def set_firmware_dir(path):
    if not path or not os.path.isdir(path):
        raise LibraryError("That folder doesn't exist.")
    s = load_state()
    s["folder"] = os.path.abspath(path)
    save_state(s)
    return firmware_dir()


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._+-]+", "_", text or "").strip("._") or "firmware"


def folder_files():
    """The .fwsc files sitting in the firmware folder: [{'path','name','version','size','ok','why'}], newest first."""
    out = []
    d = firmware_dir()
    for n in os.listdir(d):
        p = os.path.join(d, n)
        if not (os.path.isfile(p) and n.lower().endswith(".fwsc")):
            continue
        name, version = guess_name(n)
        try:
            size, _sha = check_file(p)
            ok, why = True, ""
        except LibraryError as e:
            size, ok, why = os.path.getsize(p), False, str(e)
        out.append({"path": p, "name": name, "version": version, "size": size, "ok": ok, "why": why,
                    "mtime": os.path.getmtime(p)})
    return sorted(out, key=lambda e: -e["mtime"])


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _ver(text):
    return re.sub(r"^v", "", (text or "").strip().lower())


def find_in_folder(names, version="", sha=None):
    """An existing file in the firmware folder that is the same firmware: identical contents (sha) if given,
    otherwise the same version and a name that matches any of `names`. Returns its entry or None."""
    for e in folder_files():
        if not e["ok"]:
            continue
        if sha and check_file(e["path"])[1] == sha:
            return e
        if not sha and version and _ver(e["version"]) == _ver(version):
            n = _norm(e["name"])
            if any(_norm(x) and (_norm(x) in n or n in _norm(x)) for x in names if x) and n:
                return e
    return None


def store_in_folder(src, name, version=""):
    """Copies a checked firmware file into the firmware folder unless an identical file is already there.
    Returns (path, was_new). Never overwrites a different file that happens to have the same name."""
    _size, sha = check_file(src)
    same = find_in_folder([], sha=sha)
    if same:
        return same["path"], False
    base = safe_name("%s-%s" % (name, _ver(version)) if version else name)
    dest = os.path.join(firmware_dir(), base + ".fwsc")
    if os.path.exists(dest):
        dest = os.path.join(firmware_dir(), "%s-%s.fwsc" % (base, sha[:6]))
    _store(src, dest)
    return dest, True


def mark_duplicates(entries):
    """Adds 'dup_of' to folder entries whose contents are identical to an earlier one (so the list can point it out)."""
    seen = {}
    for e in entries:
        if not e["ok"]:
            continue
        sha = check_file(e["path"])[1]
        e["sha"] = sha
        e["dup_of"] = os.path.basename(seen[sha]) if sha in seen else ""
        seen.setdefault(sha, e["path"])
    return entries


def stock_first_block(is_stock, state=None):
    """The 'stock first, every time' rule. A custom firmware may only go on the FM-1 when (a) the stock V15 file is saved
    as the way back, and (b) the last thing Slipway put on the FM-1 was the stock V15, not another custom firmware.
    Returns "" when allowed, otherwise "nostock" or "putback"."""
    if is_stock:
        return ""
    state = state or load_state()
    if not state.get("stock"):
        return "nostock"
    last = state.get("installed")
    if last and not last.get("stock"):
        return "putback"
    return ""


def record_install(name, repo="", version="", stock=False):
    s = load_state()
    s["installed"] = {"name": name, "repo": repo, "version": version, "stock": bool(stock)}
    save_state(s)


def check_file(path):
    """Raises LibraryError unless this really looks like an FM-1 firmware file. Returns (size, sha256)."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read(MAX_BYTES + 1)
    except OSError:
        raise LibraryError("That file can't be opened.")
    if not path.lower().endswith(".fwsc"):
        raise LibraryError("Firmware files end in .fwsc.")
    if size < MIN_BYTES or size > MAX_BYTES or len(data) > MAX_BYTES:
        raise LibraryError("That file is the wrong size for FM-1 firmware (%d KB), so it was not saved." % (size // 1024))
    if MARKER not in data[:MARKER_WITHIN]:
        raise LibraryError("That doesn't look like FM-1 firmware (the chip marker is missing), so it was not saved.")
    return size, hashlib.sha256(data).hexdigest()


def guess_name(filename):
    """'sloop-2.6.fwsc' -> ('sloop', '2.6'); anything unparseable -> (stem, '')."""
    stem = re.sub(r"^[0-9a-f]{8}-", "", os.path.splitext(os.path.basename(filename))[0])
    m = re.match(r"^(.*?)[-_ ]v?(\d+(?:\.\d+)*)$", stem)
    return (m.group(1), m.group(2)) if m else (stem, "")


def warnings_for(fw):
    """Plain-English things the person must see (and tick) before this goes on the FM-1. fw is a catalog/discovery dict."""
    out = []
    keys = fw.get("keys") or []
    if keys:
        out.append("This firmware gives a job to: %s. %s" % (" + ".join(keys), fw.get("safety", "")))
    if not fw.get("checked"):
        out.append("Nobody has checked this firmware's key use or recovery steps yet. Read its README for how to "
                   "enter update mode and how to get back to stock BEFORE installing it.")
    elif fw.get("safety") and not keys:
        out.append(fw["safety"])
    return out


def stock_ready(state=None):
    return bool((state or load_state()).get("stock"))


def needs_ack(fw, state=None):
    """True when the person has not yet confirmed the warnings for this firmware."""
    state = state or load_state()
    w = warnings_for(fw)
    return bool(w) and state["acknowledged"].get(fw.get("repo") or fw.get("name")) != "|".join(w)


def acknowledge(fw):
    s = load_state()
    s["acknowledged"][fw.get("repo") or fw.get("name")] = "|".join(warnings_for(fw))
    save_state(s)


def _store(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dest)


def set_stock(src):
    """Keeps a copy of the official firmware as the way back. Always checked the same way."""
    size, sha = check_file(src)
    dest = os.path.join(data_dir(), "stock", "FM-1-stock.fwsc")
    _store(src, dest)
    state = load_state()
    state["stock"] = {"file": dest, "sha256": sha, "size": size, "name": os.path.basename(src)}
    save_state(state)
    return state["stock"]


def download(url, progress=None, opener=urllib.request.urlopen):
    """Downloads a release file to a temp file and returns its path. Only GitHub addresses are allowed."""
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or not (u.hostname or "").endswith(ALLOWED_HOSTS):
        raise LibraryError("Only downloads from GitHub are allowed.")
    fd, tmp = tempfile.mkstemp(suffix=".fwsc", dir=data_dir())
    try:
        with os.fdopen(fd, "wb") as out, opener(urllib.request.Request(url, headers={"User-Agent": "Slipway"}), timeout=60) as r:
            total = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise LibraryError("That download is far too big for FM-1 firmware, so it was stopped.")
                out.write(chunk)
                if progress:
                    progress(total)
        return tmp
    except LibraryError:
        os.remove(tmp)
        raise
    except OSError:
        os.remove(tmp)
        raise LibraryError("The download failed. Check the internet connection and try again.")


NEW_DAYS = 30


def released_text(published, today=None):
    """The 'Released' cell for a firmware: its release date, with NEW added if it came out in the last 30 days.
    published is the catalogue/GitHub timestamp ('2026-10-13' or '2026-10-13T09:00:00Z'). Returns '' when unknown."""
    import datetime
    day = (published or "")[:10]
    try:
        d = datetime.date.fromisoformat(day)
    except ValueError:
        return ""
    today = today or datetime.date.today()
    return day + ("  NEW" if 0 <= (today - d).days <= NEW_DAYS else "")
