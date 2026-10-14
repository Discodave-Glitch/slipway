"""The public FM-1 firmware catalogue at fm1.designburgapps.com (catalog.json, refreshed nightly by that site).

One request lists every known firmware with its author, version, release page, size and SHA-256 and the device ID
it reports once installed. Slipway only reads that list. Files are still downloaded from each project's own GitHub
release, then checked against the catalogue's SHA-256. If the catalogue can't be reached, Slipway falls back to
asking GitHub about the firmware it already knows.
"""
import json
import re
import urllib.error
import urllib.request

URL = "https://fm1.designburgapps.com/catalog.json"
SITE = "https://fm1.designburgapps.com/"


def fetch(url=URL, timeout=20, opener=urllib.request.urlopen):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Slipway", "Accept": "application/json"})
        with opener(req, timeout=timeout) as r:
            data = json.loads(r.read(5 * 1024 * 1024).decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _kinds(k):
    if isinstance(k, str):
        return [k]
    return [x for x in (k or []) if isinstance(x, str)]


def entries(data):
    """Catalogue JSON -> the same shape github.describe() returns, plus the catalogue's extras. Bad entries are skipped."""
    out = []
    for e in (data or {}).get("firmwares", []):
        try:
            repo = e["repo"]
            name = e["name"]
        except (KeyError, TypeError):
            continue
        if not isinstance(repo, str) or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            continue
        pkg = e.get("pkg") or ""
        sha = e.get("sha256") or ""
        out.append({
            "repo": repo,
            "name": str(name),
            "author": str(e.get("author") or repo.split("/")[0]),
            "description": str(e.get("what") or ""),
            "repo_url": str(e.get("site") or "https://github.com/" + repo),
            "releases_url": str(e.get("release") or ""),
            "has_releases": bool(e.get("release")),
            "version": str(e.get("version") or ""),
            "tag": str(e.get("tag") or ""),
            "published": str(e.get("date") or ""),
            "files": [{"name": pkg.rsplit("/", 1)[-1], "url": "", "size": int(e.get("size") or 0), "sha256": sha}] if pkg else [],
            "kinds": _kinds(e.get("kind")),
            "beta": bool(e.get("beta")),
            "ident": str(e.get("ident") or ""),
            "loader": e.get("loader"),
            "source": "catalogue",
        })
    return out


def idents(items):
    """[(name, compiled regex)] for the device IDs the catalogue lists."""
    out = []
    for i in items:
        if i.get("ident"):
            try:
                out.append((i["name"], re.compile(i["ident"], re.I)))
            except re.error:
                pass
    return out


def resolve_asset(item, getter):
    """Finds the real .fwsc download on the project's GitHub release (one API call).
    Returns {'name','url','size'} or None. getter is github.fetch."""
    from . import github
    tag = item.get("tag")
    repo = item["repo"]
    rel = getter("%s/repos/%s/releases/tags/%s" % (github.API, repo, tag)) if tag else None
    if not rel:
        rels = getter("%s/repos/%s/releases?per_page=5" % (github.API, repo)) or []
        rel = next((r for r in rels if not r.get("draft")), None)
    if not rel:
        return None
    for a in rel.get("assets", []):
        if a["name"].lower().endswith(".fwsc"):
            return {"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)}
    return None
