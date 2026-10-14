SLIPWAY
========
Finds custom firmware for the M-VAVE FM-1 on GitHub, shows who made it and what it is, and installs it
on your FM-1 from the list.

WHERE THE LIST COMES FROM
  Slipway reads the public FM-1 firmware catalogue at fm1.designburgapps.com (its catalog.json, refreshed nightly by
  that site): about 33 firmwares with author, version, release page, size and SHA-256. It asks once an hour and keeps
  the answer. Files are downloaded from each project's own GitHub release and checked against the catalogue's
  SHA-256; if they differ (for example a newer release than the catalogue has seen) Slipway refuses and tells you.
  If the catalogue can't be reached, Slipway asks GitHub about the firmware it already knows. Projects you add with
  "+ Add repo" or "Find more on GitHub" are looked up on GitHub directly.
  Only a few firmwares have had their key use and recovery steps read (Felucca, X0X, FiMba-1). The rest say
  "not checked" and ask for an extra confirmation.

FIRST TIME (Windows): install Python 3.10+ (python.org, tick "Add python.exe to PATH"), unzip this folder somewhere
  you want to keep it, then double-click install.bat. It installs the two MIDI libraries, puts a "Slipway" shortcut
  with the sailboat logo on your Desktop and in the Start menu, and starts the app. After that, use the shortcut.
  It also makes the "firmware" folder next to the app straight away (run_slipway.bat does too, and the zip already
  contains an empty one). (run_slipway.bat still starts it without a shortcut.) To remove it, delete the two shortcuts and this folder.

USING IT
  - The top list: firmware, who made it, latest version, KEYS IT USES, whether it is already in your folder, and
    a tick under "On FM-1" for the one Slipway last put on your FM-1.
  - "Download to folder" (next to Launch on FM-1) saves the selected firmware into your firmware folder without
    installing it. It is checked against the catalogue's SHA-256 first, and nothing is downloaded if it is already there.
  - Double-click a row (or "Open releases page") to open its GitHub Releases page. With no releases yet, the
    project's main GitHub page opens instead.
  - Select a row and press "Launch on FM-1". Slipway shows the safety notes, then uses the copy in your folder, or
    downloads it into the folder first, and installs it.
  - THE FIRMWARE FOLDER ("the boatyard"): a folder called "firmware" next to Slipway by default. Downloads go there, and
    you can drop your own .fwsc files in it (or use "Add a .fwsc file..."). "Open folder" and "Change folder..." do
    what they say. "Launch selected file" installs the file you pick in that list.
  - NO DOUBLES: if a firmware (same name and version) is already in the folder, Launch uses it and nothing is downloaded.
    After any download or "Add a file", a file with identical contents is never saved twice, and a different file
    is never overwritten. If duplicates are already in the folder, the list says so.
  - FM-1 STATUS (top left): "Check FM-1" asks the FM-1 what it is running (nothing is written). A green ring with a
    tick means original firmware. A brass dot means custom firmware. A red cross means an unfinished install.
    Slipway also checks quietly when it starts, if the installer is already set up.
  - NIGHT MODE / DAY MODE: top right. Night (a warm near-black) is the default, like the catalogue site. It remembers your choice.
  - "Find more on GitHub" searches for other FM-1 firmware. "+ Add repo" adds one by address.
  - NEW ONES: the "Released" column shows each firmware's release date, with NEW beside anything from the last 30 days.
    Click "Released" to put the newest first (click again to reverse). Firmware with no date always stays at the bottom.
  - SHIP'S BELL: warnings and errors ring a ship's bell (two chimes, slipway\ship_bell.wav) instead of the Windows chime.
    Plain information boxes stay quiet. The bell is a Freesound community recording ("ship-bell-two-chimes-102730"),
    converted to WAV. To use a different sound, replace that file with another WAV. To turn the bell off, set an
    environment variable SLIPWAY_QUIET=1.
  - WINDOW SIZE: the window won't shrink below the size where every button stays whole and readable.
  - SORTING: click a column heading to sort by it, click again to reverse (an arrow shows which). For "On FM-1" and
    "In folder" the ticked ones come first. Your choice stays when the list refreshes.
  - STUCK? Press "Stuck? Rescue..." (by the stock V15 buttons). It walks you through USB rescue: switch the FM-1 off,
    hold OCT- while switching it on, then Install now puts the stock V15 you saved back on it (the same checked
    install as everything else). The steps come from the FM-1 firmware hub (fm1.designburgapps.com).
  - BLACK SCREEN, FM-1 NOT FOUND? The Rescue window has "Full recovery guide...": the complete method that recovered
    a real soft-bricked FM-1 (it shows on the PC as "WL82 UBOOT1.00"). It writes the official V15 at address 0x4000 only,
    with two identical backups first and a byte-for-byte check after, using jl-uboot-tool by kagaimiq. It includes
    "Plan B" for Windows PCs that answer "Access is denied": run the same tool in an Ubuntu virtual machine
    (VirtualBox), no restart needed. Use "Copy all" or "Save as text file..." to keep it. The helper that makes the
    file to write (fm1_extract_app.py, by Acrawf1) is linked in the guide; it is not included with Slipway.
  - STOCK FIRST, EVERY TIME: Slipway will not install a custom firmware until the stock V15 is saved, and once a custom
    firmware is on the FM-1 the next custom install (an update, or a different firmware) is refused until the stock V15
    has been put back. It offers to put stock back right then. This keeps the way back clean and avoids stale data
    from one custom firmware confusing the next. (It goes by what Slipway last installed.)
  - THE WAY BACK: "Save stock V15" keeps M-VAVE's own file. "Put stock V15 back" installs it. Do the first one first.
  GitHub allows 60 lookups an hour without signing in. Results are kept for an hour. If you hit the limit, set
  an environment variable GITHUB_TOKEN (a free GitHub token) or wait.

HOW IT INSTALLS
  Slipway runs Felucca's own installer script (fm1_install.py, GPL-3.0, by Leo Kuroshita) exactly as that project
  documents it. The first time, Slipway asks to download it from GitHub and to pip-install the two MIDI libraries it
  needs (mido, python-rtmidi). It never uses --force, so the installer's own checks always apply (right model,
  loader marker, bounds, checksums), and Slipway refuses any file the installer would refuse.
  Do not unplug the FM-1 while it writes. If it is interrupted, press Install again and it finishes the job.
  Confirmed working on a real FM-1 with Felucca. Other firmware has not been tried here, so keep the stock
  V15 file saved.

KEY SAFETY (so the FM-1 can't end up impossible to update)
  Some firmware gives special jobs to certain buttons. The list shows them under "Keys it uses".
  - FiMba-1 uses OCT- + OCT+ together: held 5 seconds = update mode; held at power-on = calibration.
  - Felucca and X0X document no power-on or update key combination.
  - Anything not checked is marked "not checked".
  Before any firmware is installed you must read its notes and confirm them. If a project's notes change, you are
  asked again. The app warns until the stock V15 file is saved.
  Files are refused if they aren't the right size or lack the chip marker every FM-1 firmware has. Downloads are
  only allowed from GitHub, capped in size.
  Recovery per the projects' READMEs: re-run the installer; if the screen stays black the chip's own boot mode
  (USB device "WL80UBOOT") still accepts the installer; installers can restore stock V15.

ADDING WHAT YOU KNOW
  Edit slipway\catalog.py: add a repo to SEED with its keys and safety note, set checked to True once verified.
  Your files sloop, melodee, choralroot, ghoulbox, jangada, hortator: their GitHub repos weren't known, so add them
  with "+ Add repo" (or "Find more on GitHub") and import the files meanwhile.

ABOUT "ORIGINAL FIRMWARE DETECTED"
  The installer tool can't say outright whether the FM-1 runs original or custom firmware, so Slipway works it out:
  what Slipway itself last installed is certain; otherwise it goes by the ID the FM-1 reports (FM-1_90x looks like the original, FM-1_91x like custom firmware, from the catalogue's list of IDs). If a custom firmware
  you installed some other way reports the same name as the original, Slipway could call it original. Use
  "Check FM-1" after a change and tell the maker if it ever gets it wrong.

LICENCE AND CREDITS
  Slipway is free software under the MIT licence (see LICENSE). It is not made by or connected to M-VAVE or to the
  Felucca project. Use it at your own risk. Everything and everyone it relies on is listed in CREDITS.md.
