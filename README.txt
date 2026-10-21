SLIPWAY
========
Finds custom firmware for the M-VAVE FM-1 on GitHub, shows who made it and what it is, and installs it
on your FM-1 from the list.

WHERE THE LIST COMES FROM
  Slipway reads the public FM-1 firmware catalogue at thefirmwarehub.com (formerly fm1.designburgapps.com, which redirects there; its catalog.json, refreshed nightly by
  that site): about 33 firmwares with author, version, release page, size and SHA-256. It asks once an hour and keeps
  the answer. Files are downloaded from each project's own GitHub release and checked against the catalogue's
  SHA-256; if they differ (for example a newer release than the catalogue has seen) Slipway refuses and tells you.
  If the catalogue can't be reached, Slipway asks GitHub about the firmware it already knows. Projects you add with
  "+ Add repo" or "Find more on GitHub" are looked up on GitHub directly.
  Only a few firmwares have had their key use and recovery steps read (Felucca, X0X, FiMba-1). The rest say
  "not checked" and ask for an extra confirmation.

FIRST TIME (Windows) - four steps  (Mac? see FIRST TIME ON A MAC below. Android phone? see ON ANDROID below)
  1. Install Python (a free program Slipway runs on). Go to python.org/downloads and click the big yellow button.
     Open the file it downloads. On the FIRST screen of the installer, at the bottom, TICK the box
     "Add python.exe to PATH" (it is not ticked by default, and Slipway cannot find Python without it).
     Then click "Install Now". USE PYTHON 3.12 IF YOU CAN (python.org/downloads/windows, a 3.12.x release): the MIDI
     library (python-rtmidi) has ready-made builds for 3.12 but, on the one PC where this was tried, none for 3.13, and
     then "Couldn't install them" / "Unknown compiler" appears. install.bat picks 3.12, then 3.11, then 3.13.
     Python from the Microsoft Store can fail with "Access is denied": use the python.org installer instead.
     Already installed Python without ticking it? Run the installer again, choose
     "Modify", click Next, and tick "Add Python to environment variables".
  2. Unzip the Slipway zip somewhere you want to keep it (right-click it, "Extract All"). Don't run it from inside
     the zip.
  3. Double-click install.bat. It installs the two MIDI libraries, puts a "Slipway" shortcut with the sailboat logo
     on your Desktop and in the Start menu, and starts the app. If Windows says "Windows protected your PC", click
     "More info" then "Run anyway" (it is an unsigned script).
  4. After that, use the Desktop or Start-menu shortcut. (run_slipway.bat starts it without a shortcut.)
  The "firmware" folder next to the app is made straight away (the zip already contains an empty one).
  To remove Slipway, delete the two shortcuts and this folder.

FIRST TIME ON A MAC - four steps   (tested on a real MacBook Air, Apple silicon, Python from python.org; Intel Macs not yet tried - please report problems)
  1. Install Python: go to python.org/downloads/macos, download the macOS installer, open it and click Continue
     until it finishes. (No PATH box on a Mac. Apple's built-in python3 is too old for the window, so Slipway
     skips it. Homebrew users: brew install python python-tk)
  2. Unzip Slipway.zip somewhere you want to keep it (double-click it), e.g. your Documents folder.
  3. RIGHT-CLICK install.command, choose Open, then click Open again (macOS warns about unsigned scripts; a
     plain double-click is refused the first time). It makes a private environment, installs the two MIDI
     libraries, makes the firmware folder, puts "Slipway" (with the sailboat logo) in your Applications folder
     (~/Applications) and starts the app. If macOS still blocks it: System Settings -> Privacy & Security ->
     scroll down -> "Open Anyway".
  4. After that, open Slipway from Spotlight or Applications (drag it to the Dock if you like).
     run_slipway.command starts it without the app. Keep the Slipway folder where it is: the app uses it.
  Your saved stock firmware and settings live in ~/Library/Application Support/Slipway.
  The FM-1 is a normal USB-MIDI device, so no driver is needed. If "Launch on FM-1" cannot see it, try another
  cable/port, and make sure the FM-1 is in update mode as the firmware's README says.
  Black-screen recovery on a Mac: the recovery tool (jl-uboot-tool) does not support macOS. Use a Windows or
  Linux PC, or a Linux virtual machine (see "Plan C" in the Full recovery guide inside Stuck? Rescue).
  To remove Slipway: delete ~/Applications/Slipway.app and this folder.

ON ANDROID (test version) - nothing to install
  It runs as a web page in Chrome on Android. Tested on one real Android phone with a real FM-1: the firmware list
  loaded (79 firmwares), SLOOP 2.7.1 was downloaded from the list and installed, the official V15 was put back, and
  the FM-1 worked normally each time. Only one phone has been tried.
  You need: Chrome on the phone; a USB DATA cable (some only charge), with a USB-OTG adapter if your phone needs one;
  and the official FM-1.fwsc from M-VAVE's download page saved on the phone (your way back).
  1. In Chrome on the phone go to  https://discodave-glitch.github.io/slipway/app/
     For an app icon: Chrome's three-dot menu -> Add to Home screen (or Install app). The icon opens Slipway in
     Chrome and finds the FM-1 like the normal page (tested). There is no APK: a wrapper app that only opens this
     page was tried and Android blocked its MIDI permission, so use the Chrome shortcut.
  2. Plug the FM-1 into the phone and switch it on.
  3. Step 1 "Your FM-1": press "Find my FM-1" and allow MIDI (with SysEx) when Chrome asks. It should say
     FM-1_015 official V15, or the custom firmware that is on it now.
  4. Step 2 "Stock V15": press "Choose the official FM-1.fwsc" and pick the M-VAVE file. (M-VAVE's site may call it
     V16; inside the file it is FM-1_015, 699,956 bytes.) It is checked byte for byte and kept in the browser as your
     way back. A custom firmware cannot be installed until this is done.
  5. Step 3 "Pick a firmware": the list loads from the public catalogue. Search if you like, tap a firmware, read its
     note, press "Get this firmware". It is downloaded and checked against the catalogue's SHA-256. (Or use
     "Choose a firmware file from your phone" in step 4.)
  6. Step 4 "Install": read the firmware's own README (how to enter update mode, how to get back to stock), tick the
     box, press Install, confirm, and DO NOT unplug anything or let the screen sleep while it writes. Then press
     "Find my FM-1" to see what is on it.
  7. To go back: press "Put stock V15 back".
  If something goes wrong: an old page (open the address in an Incognito tab; the footer shows the page version);
  "Couldn't load the firmware list" (press Try again, see the Technical log at the bottom; you can still choose a
  file yourself); FM-1 not found (use a data cable, switch the FM-1 on first, allow MIDI with SysEx, use Chrome);
  no Downloads in the file picker on a work-profile phone (use the picker's Work tab); a write that stopped halfway
  (do not unplug: press Find my FM-1 and follow the message, or open Stuck? Rescue). Black-screen recovery needs a
  Windows or Linux PC. More: README_ANDROID.md. The web version is GPL-3.0 (it embeds Felucca's installer code).

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
  - SHIP'S BELL: warnings and errors ring a ship's bell (two chimes, slipway\ship_bell.wav) instead of the system chime (Windows, or afplay on a Mac).
    Plain information boxes stay quiet. The bell is "Ship Bell Two Chimes" by Sojan (Freesound, via Pixabay, Pixabay Content
    License), converted to WAV. To use a different sound, replace that file with another WAV. To turn the bell off, set an
    environment variable SLIPWAY_QUIET=1.
  - WINDOW SIZE: the window won't shrink below the size where every button stays whole and readable.
  - SORTING: click a column heading to sort by it, click again to reverse (an arrow shows which). For "On FM-1" and
    "In folder" the ticked ones come first. Your choice stays when the list refreshes.
  - STUCK? Press "Stuck? Rescue..." (by the stock V15 buttons). It walks you through USB rescue: switch the FM-1 off,
    hold OCT- while switching it on, then Install now puts the stock V15 you saved back on it (the same checked
    install as everything else). The steps come from the FM-1 firmware hub (thefirmwarehub.com).
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
  - V15 OR V16?: In Slipway, "stock V15" means the official FM-1 file whose contents match exactly (699,956 bytes, identifier FM-1_015 inside the file).
    M-VAVE's download page may label that same file V16: the website number is not the identifier inside the file. It was tested on a real Mac and
    FM-1 with the FM-1.fwsc from M-VAVE's site (labelled V16 there): Slipway accepted it and the FM-1 then reported FM-1_015. Slipway checks the
    contents, not the name or the label. A file it refuses shows its size and fingerprint: that is a different file, and it is untested.
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
