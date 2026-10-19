<p align="center">
  <img src="docs/slipway-dark.png" alt="Slipway: the firmware list, with release dates, NEW tags and the firmware folder" width="860">
</p>

# Slipway

**Find, check and install custom firmware on your M-VAVE FM-1, from one small app for Windows and Mac.**

Slipway lists the community's FM-1 firmware with who made it, what it does and when it was released, checks the file,
and puts it on your FM-1 in a click. It always keeps a way back to the stock V15, and if something goes wrong it
walks you through getting the FM-1 running again, even from a black screen.

## What you get

- **A live list of firmware.** Author, version, release date, a **NEW** tag for the last 30 days, and which keys it
  uses. Click any heading to sort.
- **One-click install** through Felucca's own installer, with the file checked first.
- **Download to folder.** Files land in a "boatyard" folder you can see, and are never downloaded twice.
- **Stock first, every time.** A custom firmware only goes on after the official V15 is saved, and between two custom
  installs the stock V15 goes back first, so the way back is always clean.
- **Stuck? Rescue.** Step-by-step USB rescue that puts the stock V15 back.
- **A full recovery guide** for a black-screen FM-1 (the "WL82 UBOOT1.00" case), with two checked backups and a
  byte-for-byte verify. It includes a route for Windows PCs that answer "Access is denied".
- **Nautical, readable, quiet.** Night and day modes, plain warnings, and a ship's bell instead of the system chime.

<p align="center">
  <img src="docs/slipway-light.png" alt="Slipway in day mode" width="640">
</p>

## Install (Windows)
1. **Install Python** (free). Download it from [python.org/downloads](https://www.python.org/downloads/) and open it.
   On the **first screen** of the installer, tick the box **"Add python.exe to PATH"** at the bottom. It is not ticked
   by default, and Slipway can't find Python without it. Then click **Install Now**.
2. **Download Slipway.** Get **Slipway.zip** from [Releases](../../releases) and unzip it somewhere you want to keep it
   (right-click, *Extract All*).
3. **Double-click `install.bat`.** It sets up what it needs, makes a Desktop and Start-menu shortcut with the sailboat
   logo, and starts the app. If Windows says "Windows protected your PC", click **More info**, then **Run anyway**.
4. Next time, just use the shortcut.

## Install (Mac)
> Written for macOS 11+. **Not yet tested on a real Mac** - please [open an issue](../../issues) if anything goes wrong.

1. **Install Python** from [python.org/downloads/macos](https://www.python.org/downloads/macos/) (open the installer and
   click Continue). Apple's built-in python3 is too old; Slipway skips it. Homebrew: `brew install python python-tk`.
2. **Download Slipway.zip** from [Releases](../../releases) and unzip it somewhere you want to keep it.
3. **Right-click `install.command` -> Open -> Open.** (A plain double-click is refused the first time because the script
   is unsigned. Still blocked? System Settings -> Privacy & Security -> *Open Anyway*.) It sets up a private
   environment, makes the firmware folder, adds **Slipway** (with the sailboat logo) to your Applications folder and starts it.
4. Next time, open Slipway from Spotlight or Applications.

The black-screen USB recovery tool does not support macOS: use a Windows/Linux PC or a Linux virtual machine
(see the in-app recovery guide, *Plan C*).

> **Need more detail?** The full, step-by-step guide is **[README.txt](README.txt)**: how the list works, safety
> confirmations, the firmware folder, Stuck? Rescue, and what to do if your FM-1 shows a black screen.

## Safety
Flashing firmware can leave a device unusable. Slipway installs only through Felucca's own installer, and the recovery
guide always takes two checked backups first. Use it at your own risk. Slipway is not made by or affiliated with
M-VAVE or the Felucca project.

## Licence and credits
MIT, see [LICENSE](LICENSE). Everything Slipway relies on is credited in [CREDITS.md](CREDITS.md).

Sound: the ship's bell is ["Ship Bell Two Chimes"](https://pixabay.com/sound-effects/film-special-effects-ship-bell-two-chimes-102730/)
by Sojan (Freesound, via Pixabay), used under the [Pixabay Content License](https://pixabay.com/service/license-summary/).
It is not covered by Slipway's MIT licence.
