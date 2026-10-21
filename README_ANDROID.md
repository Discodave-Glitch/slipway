# Slipway for Android (Slipway Web)

A web app version of Slipway for the M-VAVE FM-1. It runs in **Chrome on Android** (and Chrome/Edge on a computer) using Web MIDI over USB-OTG. Nothing to install from a store.

**Status: simulated only.** It passes the browser test against a simulated FM-1 (`tests/web/`). It has not been tried on a real phone or a real FM-1 yet. Treat it as a test version.

## Use it
1. Put the files from `docs/app/` on GitHub Pages (Settings > Pages > branch `main`, folder `/docs`), then open `https://discodave-glitch.github.io/slipway/app/` in Chrome on the phone.
2. Chrome menu > **Add to Home screen** to get an app icon.
3. Connect the FM-1 with a USB **data** cable through a USB-OTG adapter, switch it on, press **Find my FM-1** and allow MIDI (with SysEx).
4. Save the official V15 (`FM-1.fwsc`) once, then pick a custom `.fwsc`. Same stock-first rules as the desktop Slipway.

Black-screen recovery needs a Windows or Linux PC (see the recovery guide).

## Licence
`docs/app/` is **GPL-3.0** because it includes Felucca's `fm1ota.js` and `fm1pkg.js` (Leo Kuroshita, Hugelton Instruments). The desktop app stays MIT. Rebuild with `python3 tools/build_web.py`; test with `node tests/web/run_web_test.mjs` (needs Playwright; set `PLAYWRIGHT_PATH`).

## APK later
A real APK can wrap this page (Trusted Web Activity via Bubblewrap and a GitHub Actions build). It needs the same Web MIDI support, so the web version has to work on a phone first.
