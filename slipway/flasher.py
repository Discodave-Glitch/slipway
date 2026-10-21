"""Flashes the FM-1 by running the Felucca project's own installer (tools/fm1_install.py, GPL-3.0, by Leo Kuroshita).

Slipway does not re-implement the update protocol. It downloads that script once, keeps it (and its SHA-256) in its
data folder, and runs it exactly as the project documents:  fm1_install.py FILE.fwsc --yes   and   --info.
Slipway never passes --force. The installer's own checks (right model, loader marker, bounds, checksums) therefore
still apply, and an interrupted install can be finished by running the same step again.
"""
import hashlib
import os
import re
import subprocess
import sys
import urllib.request

from . import library

TOOL_URL = "https://github.com/hugelton/Felucca/raw/refs/heads/main/tools/fm1_install.py"
LOADER_MARKER = b"FELUCCA-LOADER-1"
NEEDS = ("mido", "rtmidi")           # pip install mido python-rtmidi

EXIT_TEXT = {
    0: "Done. The FM-1 has restarted on the new firmware.",
    1: "Cancelled, or the installer reported an error.",
    2: "The installer didn't accept that file or its arguments.",
    3: "No FM-1 was found. Plug it in with a USB data cable, and close other programs that use MIDI.",
    4: "The connection to the FM-1 was lost. Don't unplug it: press Install again to finish.",
    5: "The FM-1 didn't answer in time. Press Install again; an interrupted install picks up where it stopped.",
    6: "That firmware is for a different model, or the FM-1 reported the wrong identity afterwards.",
}


def tool_path():
    d = os.path.join(library.data_dir(), "tools")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "fm1_install.py")


def tool_info():
    p = tool_path()
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        data = f.read()
    return {"path": p, "sha256": hashlib.sha256(data).hexdigest()}


def fetch_tool(opener=urllib.request.urlopen):
    """Downloads the installer script. Refuses anything that doesn't look like the real thing."""
    try:
        with opener(urllib.request.Request(TOOL_URL, headers={"User-Agent": "Slipway"}), timeout=30) as r:
            data = r.read(2 * 1024 * 1024 + 1)
    except OSError:
        raise library.LibraryError("Couldn't download the installer tool. Check the internet connection.")
    if len(data) > 2 * 1024 * 1024 or b"SPDX-License-Identifier: GPL-3.0" not in data or LOADER_MARKER not in data \
            or b"--info" not in data:
        raise library.LibraryError("The downloaded installer doesn't look like Felucca's fm1_install.py, so it was not kept.")
    p = tool_path()
    with open(p + ".part", "wb") as f:
        f.write(data)
    os.replace(p + ".part", p)
    return tool_info()


def missing_modules():
    out = []
    for m in NEEDS:
        try:
            __import__(m)
        except Exception:
            out.append({"mido": "mido", "rtmidi": "python-rtmidi"}[m])
    return out


def install_modules(run=subprocess.run):
    """pip install of the two MIDI libraries the installer needs. Returns (ok, output)."""
    r = run([sys.executable, "-m", "pip", "install", "mido", "python-rtmidi"], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-1500:]


def can_flash(file, is_stock=False):
    """None when this file may be flashed, otherwise the reason it may not. Mirrors the installer's own rule."""
    try:
        library.check_file(file)
        with open(file, "rb") as f:
            has_loader = LOADER_MARKER in f.read()
    except (library.LibraryError, OSError) as e:
        return str(e)
    if not has_loader and not is_stock:
        return ("This file has no Felucca loader marker, so the installer would refuse it (and Slipway never forces it). "
                "Only the official V15 file is allowed without it.")
    return None


_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def _run(args, on_line=None, popen=subprocess.Popen):
    if not tool_info():
        raise library.LibraryError("The installer tool isn't downloaded yet.")
    p = popen([sys.executable, tool_path()] + args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
              stderr=subprocess.STDOUT, text=True, cwd=os.path.dirname(tool_path()))
    lines = []
    for line in p.stdout:
        line = _ANSI.sub("", line).replace("\r", "").rstrip()
        lines.append(line)
        if on_line:
            on_line(line)
    return p.wait(), lines


def device_info(on_line=None, popen=subprocess.Popen):
    """Asks the FM-1 who it is (writes nothing). Returns (found, lines)."""
    rc, lines = _run(["--info"], on_line, popen)
    return rc == 0, lines


def flash(file, is_stock=False, on_line=None, popen=subprocess.Popen):
    """Installs file onto the FM-1. Returns (ok, message, lines). Never uses --force."""
    why = can_flash(file, is_stock)
    if why:
        return False, why, []
    rc, lines = _run([file, "--yes"], on_line, popen)
    return rc == 0, EXIT_TEXT.get(rc, "The installer stopped with code %d." % rc), lines


def parse_info(lines):
    """The installer's --info line looks like:  FM-1_906 [running] port: FM-1 ...  ->  dict, or None if not found."""
    for line in lines:
        m = re.match(r"^\s*(\S+)\s+\[(.+?)\]\s+port:\s*(.*)$", line)
        if m:
            return {"ident": m.group(1), "mode": m.group(2), "port": m.group(3).strip(), "raw": line.strip()}
    return None


def detect(lines, record=None, known_names=(), idents=()):
    """Works out what the FM-1 is running. Returns (kind, text) with kind one of:
    none | loader | original | original_guess | custom | unknown.
    What Slipway itself last installed (record) is certain. Otherwise it goes by the ID the FM-1 reports:
    FM-1_90x is the original V15 family; FM-1_91x belongs to the custom firmware. `idents` is [(name, regex)] from the
    catalogue, used to name the firmware when only one matches."""
    info = parse_info(lines)
    if not info:
        return "none", "No FM-1 found."
    if "update" in info["mode"].lower() or info["ident"].lower().startswith("ota-"):
        return "loader", "In update mode (an install wasn't finished). Press Install again."
    ident = info["ident"]
    blob = (ident + " " + info["port"]).lower()
    for n in known_names:
        if n and n.lower() in blob:
            return "custom", "Running %s." % n
    if record and record.get("stock"):
        return "original", "Original M-VAVE firmware (put back by Slipway)."
    if record and record.get("name"):
        return "custom", "Running %s (installed by Slipway)." % record["name"]
    if re.fullmatch(r"FM-1_90\d", ident, re.I):
        return "original_guess", "Original firmware detected (%s)." % ident
    matches = sorted({n for n, rx in idents if rx.fullmatch(ident)})
    if matches:
        return "custom", "Custom firmware (%s)." % ident
    return "unknown", "Connected: %s." % info["raw"]
