import os, sys, tempfile, unittest, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["SLIPWAY_DIR"] = tempfile.mkdtemp()
from slipway import github, library, catalog

UP = "/root/.claude/uploads/f01c4690-6d29-5c7e-8c8c-505a29ba4e6b"
REAL = sorted(glob.glob(UP + "/*.fwsc"))


def fake(url):
    if url.endswith("/repos/a/withrel"):
        return {"full_name": "a/withrel", "name": "withrel", "owner": {"login": "a"}, "description": "D", "html_url": "https://github.com/a/withrel"}
    if url.endswith("/repos/a/norel"):
        return {"full_name": "a/norel", "name": "norel", "owner": {"login": "a"}, "description": None, "html_url": "https://github.com/a/norel"}
    if "a/withrel/releases" in url:
        return [{"draft": True, "tag_name": "x"}, {"tag_name": "v1", "published_at": "2026-01-02T00:00:00Z",
                "assets": [{"name": "x.zip", "browser_download_url": "u0"}, {"name": "x.fwsc", "browser_download_url": "https://github.com/a/withrel/releases/download/v1/x.fwsc", "size": 5}]}]
    if "a/norel/releases" in url:
        return []
    return None


class Slipway(unittest.TestCase):
    def setUp(self):
        for f in glob.glob(library.data_dir() + "/**/*", recursive=True):
            if os.path.isfile(f): os.remove(f)

    def test_released_text(self):
        import datetime
        today = datetime.date(2026, 10, 13)
        self.assertEqual(library.released_text("2026-10-01", today), "2026-10-01  NEW")
        self.assertEqual(library.released_text("2026-10-13T09:00:00Z", today), "2026-10-13  NEW")
        self.assertEqual(library.released_text("2026-09-13", today), "2026-09-13  NEW")      # exactly 30 days
        self.assertEqual(library.released_text("2026-09-12", today), "2026-09-12")           # 31 days: not new
        self.assertEqual(library.released_text("2027-01-01", today), "2027-01-01")           # in the future: just the date
        self.assertEqual(library.released_text("", today), "")
        self.assertEqual(library.released_text("garbage", today), "")

    def test_parse_repo(self):
        self.assertEqual(github.parse_repo("https://github.com/hugelton/Felucca/releases"), "hugelton/Felucca")
        self.assertEqual(github.parse_repo("a/b"), "a/b")
        self.assertEqual(github.parse_repo("https://github.com/a/b.git"), "a/b")
        self.assertIsNone(github.parse_repo(""))
        self.assertIsNone(github.parse_repo("hello"))

    def test_describe(self):
        d = github.describe("a/withrel", fake)
        self.assertTrue(d["has_releases"]); self.assertEqual(d["version"], "v1")
        self.assertEqual(d["releases_url"], "https://github.com/a/withrel/releases")
        self.assertEqual([f["name"] for f in d["files"]], ["x.fwsc"])
        n = github.describe("a/norel", fake)
        self.assertFalse(n["has_releases"]); self.assertEqual(n["releases_url"], ""); self.assertEqual(n["description"], "")
        self.assertIsNone(github.describe("a/gone", fake))

    def test_search_filters_and_dedupes(self):
        g = lambda url: {"items": [{"full_name": "x/fm1-thing", "description": "for the FM-1"},
                                   {"full_name": "x/unrelated", "description": "a game"},
                                   {"full_name": "X/FM1-Thing", "description": "dup"}]}
        self.assertEqual(github.search(["q"], g), ["x/fm1-thing"])

    @unittest.skipUnless(REAL, "real firmware files not present")
    def test_all_real_files_accepted(self):
        for f in REAL:
            library.check_file(f)

    def test_bad_files_refused(self):
        d = tempfile.mkdtemp()
        for name, data in (("a.fwsc", b"x" * 10), ("b.fwsc", b"x" * 700000), ("c.txt", b"AC791N" * 200000)):
            p = os.path.join(d, name); open(p, "wb").write(data)
            with self.assertRaises(library.LibraryError): library.check_file(p)

    def _good(self):
        p = os.path.join(tempfile.mkdtemp(), "t-1.0.fwsc")
        open(p, "wb").write(b"\0" * 1060 + b"AC791N" + b"\1" * 300000)
        return p

    def test_unchecked_firmware_needs_ack(self):
        fw = {"name": "mystery", "repo": "z/mystery", "keys": [], "checked": False}
        self.assertTrue(library.needs_ack(fw))
        library.acknowledge(fw); self.assertFalse(library.needs_ack(fw))

    def test_ack_resets_if_warning_text_changes(self):
        fw = {"name": "m", "repo": "z/m", "keys": [], "checked": False}
        library.acknowledge(fw)
        fw["keys"] = ["HOME"]; fw["safety"] = "new"
        self.assertTrue(library.needs_ack(fw))

    def test_key_warning_for_fimba(self):
        fimba = dict(catalog.SEED[2], version="0.6.0")
        self.assertIn("OCT-", " ".join(library.warnings_for(fimba)))
        self.assertTrue(library.needs_ack(fimba))
        library.acknowledge(fimba); self.assertFalse(library.needs_ack(fimba))

    def test_stock_first_rule(self):
        st = {"stock": None, "installed": None}
        self.assertEqual(library.stock_first_block(True, st), "")                       # stock itself is always allowed
        self.assertEqual(library.stock_first_block(False, st), "nostock")               # no stock saved: no custom firmware
        st["stock"] = {"file": "x"}
        self.assertEqual(library.stock_first_block(False, st), "")                      # stock saved, nothing custom on it
        st["installed"] = {"name": "A", "stock": False}
        self.assertEqual(library.stock_first_block(False, st), "putback")               # a custom one is on: stock first
        self.assertEqual(library.stock_first_block(True, st), "")
        st["installed"] = {"name": "stock", "stock": True}
        self.assertEqual(library.stock_first_block(False, st), "")                      # stock is back: custom allowed again

    def test_stock_saved_and_checked(self):
        self.assertFalse(library.stock_ready())
        library.set_stock(self._good()); self.assertTrue(library.stock_ready())

    def test_download_only_github(self):
        for u in ("http://github.com/a", "https://evil.example.com/x.fwsc", "https://github.com.evil.com/x"):
            with self.assertRaises(library.LibraryError): library.download(u)

    def test_download_size_cap(self):
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s, n): return b"x" * n
        with self.assertRaises(library.LibraryError): library.download("https://github.com/a/b/x.fwsc", opener=lambda *a, **k: R())
        self.assertEqual([f for f in os.listdir(library.data_dir()) if f.endswith(".fwsc")], [])

    def test_guess_name(self):
        self.assertEqual(library.guess_name("dac7c6aa-sloop-2.6.fwsc"), ("sloop", "2.6"))
        self.assertEqual(library.guess_name("hortator-0.16.0.fwsc"), ("hortator", "0.16.0"))
        self.assertEqual(library.guess_name("FM-1.fwsc"), ("FM", "1"))



from slipway import flasher


class FakeProc:
    def __init__(self, lines, rc): self.stdout = iter(l + "\n" for l in lines); self._rc = rc
    def wait(self): return self._rc


class Flash(unittest.TestCase):
    def setUp(self):
        for f in glob.glob(library.data_dir() + "/**/*", recursive=True):
            if os.path.isfile(f): os.remove(f)

    def _file(self, loader=True):
        p = os.path.join(tempfile.mkdtemp(), "t-1.0.fwsc")
        with open(p, "wb") as f:
            f.write(b"\0" * 1060 + b"AC791N" + b"\1" * 300000 + (flasher.LOADER_MARKER if loader else b""))
        return p

    def _tool(self):
        with open(flasher.tool_path(), "w") as f: f.write("x")

    def test_marker_rule(self):
        self.assertIsNone(flasher.can_flash(self._file(True)))
        self.assertIn("loader marker", flasher.can_flash(self._file(False)))
        self.assertIsNone(flasher.can_flash(self._file(False), is_stock=True))

    @unittest.skipUnless(REAL, "real files not present")
    def test_real_files(self):
        for f in REAL:
            stock = f.endswith("FM-1.fwsc")
            self.assertIsNone(flasher.can_flash(f, stock), f)
            if stock: self.assertIsNotNone(flasher.can_flash(f, False))

    def test_flash_never_forces_and_reports(self):
        self._tool(); seen = []
        def popen(cmd, **k): seen.append(cmd); return FakeProc(["Writing...", "Done"], 0)
        ok, msg, lines = flasher.flash(self._file(), False, popen=popen)
        self.assertTrue(ok); self.assertNotIn("--force", seen[0]); self.assertIn("--yes", seen[0]); self.assertEqual(lines[-1], "Done")
        ok, msg, _ = flasher.flash(self._file(), False, popen=lambda c, **k: FakeProc(["no device"], 3))
        self.assertFalse(ok); self.assertIn("No FM-1", msg)
        ok, msg, _ = flasher.flash(self._file(), False, popen=lambda c, **k: FakeProc([], 4))
        self.assertIn("press Install again", msg)

    def test_refused_file_never_reaches_installer(self):
        self._tool(); called = []
        ok, msg, _ = flasher.flash(self._file(False), False, popen=lambda *a, **k: called.append(1))
        self.assertFalse(ok); self.assertEqual(called, [])

    def test_no_tool_no_flash(self):
        with self.assertRaises(library.LibraryError): flasher.flash(self._file(), False)

    def test_device_info(self):
        self._tool()
        self.assertEqual(flasher.device_info(popen=lambda c, **k: FakeProc(["FM-1_906"], 0)), (True, ["FM-1_906"]))
        self.assertEqual(flasher.device_info(popen=lambda c, **k: FakeProc([], 3))[0], False)

    def test_fetch_tool_validates(self):
        class R:
            def __init__(s, d): s.d = d
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def read(s, n): return s.d
        good = b"# SPDX-License-Identifier: GPL-3.0-only\nFELUCCA-LOADER-1 --info"
        self.assertTrue(flasher.fetch_tool(lambda *a, **k: R(good))["sha256"])
        os.remove(flasher.tool_path())
        for bad in (b"print('hi')", b"x" * 3000000):
            with self.assertRaises(library.LibraryError): flasher.fetch_tool(lambda *a, **k: R(bad))
        self.assertIsNone(flasher.tool_info())




class Folder(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        library.set_firmware_dir(self.d)

    def _mk(self, fill=b"\1", name="x.fwsc"):
        p = os.path.join(tempfile.mkdtemp(), name)
        with open(p, "wb") as f:
            f.write(b"\0" * 1060 + b"AC791N" + fill * 300000)
        return p

    def test_store_then_same_file_not_doubled(self):
        a, new = library.store_in_folder(self._mk(), "Felucca", "v1.6")
        self.assertTrue(new); self.assertEqual(os.path.basename(a), "Felucca-1.6.fwsc")
        b, new2 = library.store_in_folder(self._mk(name="other-name.fwsc"), "Felucca", "v1.6")
        self.assertFalse(new2); self.assertEqual(a, b)
        self.assertEqual(len(os.listdir(self.d)), 1)

    def test_different_file_same_name_is_not_overwritten(self):
        a, _ = library.store_in_folder(self._mk(b"\1"), "Felucca", "1.6")
        b, new = library.store_in_folder(self._mk(b"\2"), "Felucca", "1.6")
        self.assertTrue(new); self.assertNotEqual(a, b); self.assertTrue(os.path.exists(a))

    def test_find_before_download(self):
        library.store_in_folder(self._mk(), "Felucca", "v1.6")
        self.assertIsNotNone(library.find_in_folder(["Felucca", "felucca"], "v1.6"))
        self.assertIsNotNone(library.find_in_folder(["hugelton-felucca"], "1.6"))
        self.assertIsNone(library.find_in_folder(["Felucca"], "1.7"))
        self.assertIsNone(library.find_in_folder(["X0X"], "v1.6"))

    def test_duplicates_in_folder_are_flagged(self):
        import shutil
        a = self._mk(); shutil.copy(a, os.path.join(self.d, "a-1.0.fwsc")); shutil.copy(a, os.path.join(self.d, "b-1.0.fwsc"))
        es = library.mark_duplicates(library.folder_files())
        self.assertEqual(sorted(bool(e["dup_of"]) for e in es), [False, True])

    def test_bad_files_listed_but_marked(self):
        open(os.path.join(self.d, "junk-1.fwsc"), "wb").write(b"x" * 10)
        es = library.folder_files(); self.assertFalse(es[0]["ok"]); self.assertTrue(es[0]["why"])

    def test_folder_must_exist(self):
        with self.assertRaises(library.LibraryError): library.set_firmware_dir("/nonexistent/zzz")


class Detect(unittest.TestCase):
    NAMES = ["Felucca", "X0X", "FiMba-1"]

    def test_parse(self):
        i = flasher.parse_info(["noise", "FM-1_906 [running] port: FM-1 MIDI 1"])
        self.assertEqual((i["ident"], i["mode"], i["port"]), ("FM-1_906", "running", "FM-1 MIDI 1"))
        self.assertIsNone(flasher.parse_info(["error: FM-1 not found"]))

    def test_kinds(self):
        d = lambda lines, rec=None: flasher.detect(lines, rec, self.NAMES)[0]
        self.assertEqual(d([]), "none")
        self.assertEqual(d(["FM-1_906 [update loader (update not finished)] port: x"]), "loader")
        self.assertEqual(d(["ota-FM-1_906 [running] port: x"]), "loader")
        self.assertEqual(d(["FM-1_906 [running] port: FM-1 MIDI"]), "original_guess")
        self.assertEqual(d(["FM-1_906 [running] port: Felucca"]), "custom")
        self.assertEqual(d(["FM-1_906 [running] port: FM-1"], {"name": "X0X", "stock": False}), "custom")
        self.assertEqual(d(["FM-1_906 [running] port: FM-1"], {"name": "stock", "stock": True}), "original")
        self.assertEqual(d(["weird [running] port: ?"]), "unknown")


from slipway import catalogue

SAMPLE = {"updated": "x", "firmwares": [
    {"id": "felucca", "kind": ["synth", "groove"], "name": "Felucca", "author": "Leo", "repo": "hugelton/Felucca",
     "ident": "FM-1_91\\d", "what": "The custom firmware", "site": "https://github.com/hugelton/Felucca", "version": "1.6",
     "date": "2026-10-13", "pkg": "fw/felucca-1.6.fwsc", "size": 610086, "sha256": "ab" * 32,
     "release": "https://github.com/hugelton/Felucca/releases/tag/v1.6", "tag": "v1.6", "beta": False, "loader": None},
    {"id": "x", "kind": "drums", "name": "Single", "author": "A", "repo": "a/b", "version": "1", "pkg": "", "beta": True},
    {"name": "no repo"}, {"name": "bad", "repo": "../etc/passwd"}, "junk"]}


class Catalogue(unittest.TestCase):
    def test_entries(self):
        es = catalogue.entries(SAMPLE)
        self.assertEqual([e["name"] for e in es], ["Felucca", "Single"])
        f = es[0]
        self.assertEqual(f["kinds"], ["synth", "groove"]); self.assertEqual(f["files"][0]["name"], "felucca-1.6.fwsc")
        self.assertEqual(f["files"][0]["sha256"], "ab" * 32); self.assertTrue(f["has_releases"])
        self.assertEqual(f["releases_url"], "https://github.com/hugelton/Felucca/releases/tag/v1.6")
        self.assertEqual(es[1]["kinds"], ["drums"]); self.assertEqual(es[1]["files"], []); self.assertFalse(es[1]["has_releases"])
        self.assertEqual(catalogue.entries(None), []); self.assertEqual(catalogue.entries({"firmwares": "x"}), [])

    def test_fetch_failure_is_quiet(self):
        def boom(*a, **k): raise OSError("no network")
        self.assertIsNone(catalogue.fetch(opener=boom))

    def test_resolve_asset(self):
        item = catalogue.entries(SAMPLE)[0]
        def g(url):
            if url.endswith("/releases/tags/v1.6"):
                return {"assets": [{"name": "n.zip", "browser_download_url": "z"}, {"name": "f.fwsc", "browser_download_url": "https://github.com/a/f.fwsc", "size": 5}]}
        self.assertEqual(catalogue.resolve_asset(item, g)["url"], "https://github.com/a/f.fwsc")
        self.assertIsNone(catalogue.resolve_asset(item, lambda u: None))

    def test_detect_uses_catalogue_ids(self):
        ids = catalogue.idents(catalogue.entries(SAMPLE))
        d = lambda line: flasher.detect([line], None, [], ids)
        self.assertEqual(d("FM-1_916 [running] port: FM-1")[0], "custom")
        self.assertEqual(d("FM-1_906 [running] port: FM-1")[0], "original_guess")
        self.assertEqual(d("FM-1_777 [running] port: FM-1")[0], "unknown")


if __name__ == "__main__":
    unittest.main()
