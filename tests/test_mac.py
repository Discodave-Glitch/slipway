import os, sys, subprocess, unittest
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from slipway import recovery_guide


class Mac(unittest.TestCase):
    def test_scripts_valid_and_executable(self):
        for n in ("install.command", "run_slipway.command"):
            p = os.path.join(ROOT, n)
            self.assertTrue(os.access(p, os.X_OK), n)
            data = open(p, "rb").read()
            self.assertNotIn(b"\r\n", data, n + " must have LF endings")
            self.assertEqual(subprocess.call(["bash", "-n", p]), 0, n)

    def test_icons(self):
        self.assertEqual(open(os.path.join(ROOT, "slipway", "slipway.icns"), "rb").read(4), b"icns")
        self.assertEqual(open(os.path.join(ROOT, "slipway", "slipway.png"), "rb").read(4), b"\x89PNG")

    def test_guide_has_mac_plan(self):
        self.assertIn("Plan C", recovery_guide.as_text())

    def test_installer_builds_app_bundle(self):
        # run the app-bundle part of install.command with a fake HOME to check the plist and launcher are written
        import tempfile, shutil
        home = tempfile.mkdtemp()
        py = sys.executable
        env = dict(os.environ, HOME=home, PATH=os.path.dirname(py) + ":" + os.environ["PATH"])
        work = tempfile.mkdtemp()
        shutil.copytree(ROOT, work + "/s", ignore=shutil.ignore_patterns(".venv", "firmware", "__pycache__"))
        fake = work + "/bin"; os.makedirs(fake)
        open(fake + "/open", "w").write("#!/bin/sh\nexit 0\n"); os.chmod(fake + "/open", 0o755)
        env["PATH"] = fake + ":" + env["PATH"]
        r = subprocess.run(["bash", work + "/s/install.command"], env=env, capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)
        app = home + "/Applications/Slipway.app/Contents"
        self.assertTrue(os.path.exists(app + "/Info.plist"), r.stdout + r.stderr)
        self.assertTrue(os.access(app + "/MacOS/slipway-launch", os.X_OK))
        self.assertTrue(os.path.exists(app + "/Resources/Slipway.icns"))
        self.assertIn("-m slipway", open(app + "/MacOS/slipway-launch").read())


if __name__ == "__main__":
    unittest.main()
