# Slipway for Android (Slipway Web)

A web app version of Slipway for the M-VAVE FM-1. It runs in **Chrome on Android** (and Chrome/Edge on a computer) using Web MIDI over USB-OTG. Nothing to install from a store.

**Status: tested on one real phone.** Tested on one real Android phone (Chrome, USB-OTG cable) with a real FM-1: it found the FM-1, loaded the firmware list (79 firmwares), downloaded SLOOP 2.7.1 from the list (checksum checked), accepted the official `FM-1.fwsc` as the way back, put the official V15 back, and installed SLOOP 2.7.1 again; each time the FM-1 restarted and worked normally. Only one phone has been tried. It also passes the browser test against a simulated FM-1 (`tests/web/`). Only one phone has been tried, so please [open an issue](https://github.com/Discodave-Glitch/slipway/issues) if it behaves differently on yours.

## Use it
1. Put the files from `docs/app/` on GitHub Pages (Settings > Pages > branch `main`, folder `/docs`), then open `https://discodave-glitch.github.io/slipway/app/` in Chrome on the phone.
2. Chrome menu > **Add to Home screen** (or *Install app*) to get an app icon. This shortcut was tested and finds the FM-1.
3. Connect the FM-1 with a USB **data** cable through a USB-OTG adapter, switch it on, press **Find my FM-1** and allow MIDI (with SysEx).
4. Save the official V15 (`FM-1.fwsc`) once (step 2). M-VAVE's site may call it V16; inside the file it is `FM-1_015`, 699,956 bytes.
5. Step 3 lists the public firmware catalogue (thefirmwarehub.com, which the old fm1.designburgapps.com address redirects to). Tap a firmware, read its note, press **Get this firmware**: it is downloaded, checked against the catalogue's SHA-256 and loaded into step 4. You can also choose a `.fwsc` file you already have. Same stock-first rules as the desktop Slipway: no custom install until the official V15 is saved, and tick the README box.
6. If the list says "Couldn't load the firmware list", press Try again; the Technical log at the bottom shows why.

Black-screen recovery needs a Windows or Linux PC (see the recovery guide).

## Licence
`docs/app/` is **GPL-3.0** because it includes Felucca's `fm1ota.js` and `fm1pkg.js` (Leo Kuroshita, Hugelton Instruments). The desktop app stays MIT. Rebuild with `python3 tools/build_web.py`; test with `node tests/web/run_web_test.mjs` (needs Playwright; set `PLAYWRIGHT_PATH`).

## No APK
A wrapper APK (a Trusted Web Activity that just opens this page) was built and tried on a real phone. It loaded the page and the firmware list, but Android refused the MIDI permission, so it could not find the FM-1. Use Chrome's **Add to Home screen** shortcut instead: it was tested and finds the FM-1.
