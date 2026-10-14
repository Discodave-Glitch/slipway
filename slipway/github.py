"""Talks to GitHub (public API, no sign-in needed; set GITHUB_TOKEN to lift the 60-requests-an-hour limit)."""
import json
import os
import re
import time
import urllib.error
import urllib.request

API = "https://api.github.com"


class GitHubError(Exception):
    pass


def fetch(url, timeout=20):
    """Returns parsed JSON, or None for a 404. Raises GitHubError with a plain-English reason otherwise."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Slipway"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (403, 429):
            raise GitHubError("GitHub says too many requests. Wait a few minutes (or set GITHUB_TOKEN) and press Refresh.")
        raise GitHubError("GitHub returned an error (%s)." % e.code)
    except (urllib.error.URLError, OSError, ValueError):
        raise GitHubError("Couldn't reach GitHub. Check the internet connection.")


def parse_repo(text):
    """'https://github.com/owner/repo/releases' or 'owner/repo' -> 'owner/repo', else None."""
    m = re.search(r"(?:github\.com/)?([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/.*)?$", (text or "").strip())
    if not m or m.group(1) in ("http:", "https:"):
        return None
    return "%s/%s" % (m.group(1), m.group(2))


def describe(repo, getter=fetch):
    """Everything the list shows for one repo. Never raises for a missing repo: returns None."""
    info = getter("%s/repos/%s" % (API, repo))
    if not info:
        return None
    releases = getter("%s/repos/%s/releases?per_page=5" % (API, repo)) or []
    releases = [r for r in releases if not r.get("draft")]
    latest = releases[0] if releases else None
    files = []
    if latest:
        files = [{"name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0)}
                 for a in latest.get("assets", []) if a["name"].lower().endswith(".fwsc")]
    base = info["html_url"]
    return {
        "repo": info["full_name"],
        "name": info["name"],
        "author": (info.get("owner") or {}).get("login", ""),
        "description": info.get("description") or "",
        "repo_url": base,
        "releases_url": base + "/releases" if latest else "",
        "has_releases": bool(latest),
        "version": (latest or {}).get("tag_name", ""),
        "published": ((latest or {}).get("published_at") or "")[:10],
        "files": files,
        "stars": info.get("stargazers_count", 0),
        "archived": bool(info.get("archived")),
    }


def search(queries, getter=fetch):
    """Repo names from GitHub search, best match first, no duplicates."""
    seen, out = set(), []
    for q in queries:
        data = getter("%s/search/repositories?q=%s&per_page=20" % (API, urllib.request.quote(q)))
        for item in (data or {}).get("items", []):
            name = item["full_name"]
            blob = ("%s %s" % (name, item.get("description") or "")).lower()
            if name.lower() not in seen and ("fm-1" in blob or "fm1" in blob or ".fwsc" in blob):
                seen.add(name.lower())
                out.append(name)
    return out


class Cache:
    def __init__(self, path, max_age=3600):
        self.path, self.max_age = path, max_age

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def fresh(self, entry):
        return bool(entry) and time.time() - entry.get("at", 0) < self.max_age

    def save(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, self.path)
