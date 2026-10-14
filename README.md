# Slipway

A small Windows app for the **M-VAVE FM-1**. It finds custom firmware, shows who made it and what it does, checks
the file, and installs it from a list. Built on a nautical theme.

- Lists firmware from the community catalogue and GitHub, with author, version, release date and a NEW tag.
- Downloads into a folder you can see, and never twice.
- **Stock first, every time:** a custom firmware only goes on after the official V15 is saved, and after one custom
  install the next needs the stock V15 put back first.
- **Stuck? Rescue** and a full **USB recovery guide** for a black-screen FM-1 (the "WL82 UBOOT1.00" case), including a
  route for Windows PCs that answer "Access is denied".
- Plain, themed warnings with a ship's bell instead of the Windows chime.

## Install
1. Download the latest **Slipway.zip** from the [Releases](../../releases) page and unzip it.
2. Double-click `install.bat`. It installs what it needs, makes a Desktop and Start-menu shortcut with the sailboat
   logo, and starts the app.
3. Needs Windows and Python 3.10 or newer (python.org, tick "Add python.exe to PATH").

See `README.txt` for the full guide.

## Safety
Flashing firmware can leave a device unusable. Slipway installs only through Felucca's own installer, and the
recovery guide always takes two checked backups first. Use it at your own risk.
Not made by or affiliated with M-VAVE or the Felucca project.

## Licence and credits
MIT, see [LICENSE](LICENSE). Everything it relies on is in [CREDITS.md](CREDITS.md).
