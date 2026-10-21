#!/bin/bash
# Slipway installer for macOS. Double-click this file (first time: right-click it, choose Open, then Open).
# It finds Python, makes a private environment next to the app, installs the two MIDI libraries, makes the
# firmware folder, makes "Slipway" in your Applications folder (with the sailboat icon), and starts the app.
cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
echo
echo "  Slipway - installing"
echo "  ----------------------------------------"
echo
xattr -dr com.apple.quarantine "$HERE" 2>/dev/null     # so macOS stops asking about each file from the download

# ---- 1. find Python 3.10 or newer that has Tk 8.6 (the window toolkit) ----------------------
# Apple's own /usr/bin/python3 is skipped on purpose: it is old and its Tk is too old to draw the window.
PY=""
for c in /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
         /opt/homebrew/bin/python3 /usr/local/bin/python3 "$(command -v python3 2>/dev/null)"; do
    [ -n "$c" ] && [ -x "$c" ] && [ "$c" != "/usr/bin/python3" ] || continue
    if "$c" -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,10) and tkinter.TkVersion >= 8.6 else 1)" >/dev/null 2>&1; then
        PY="$c"; break
    fi
done
if [ -z "$PY" ]; then
    echo "  Slipway needs Python 3.10 or newer (with its window toolkit), and it was not found."
    echo
    echo "  1. Go to https://www.python.org/downloads/macos/ and download the macOS installer."
    echo "  2. Open it and click Continue until it is installed. (No PATH tick is needed on a Mac.)"
    echo "  3. Double-click install.command again."
    echo
    echo "  Using Homebrew instead?  brew install python python-tk"
    echo
    read -r -p "  Press Return to close. " _
    exit 1
fi
echo "  Python found: $PY"

# On Apple-silicon Macs, always run natively (arm64). Started through Rosetta, the MIDI library built here cannot be loaded.
RUN=""
if [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ] && arch -arm64 "$PY" -c "pass" >/dev/null 2>&1; then RUN="arch -arm64"; fi

# python.org's Python trusts no websites until this runs; without it Slipway cannot reach GitHub.
for cert in /Applications/Python\ 3*/Install\ Certificates.command; do
    [ -f "$cert" ] && { echo "  Setting up secure connections for Python..."; bash "$cert" >/dev/null 2>&1; }
done

# ---- 2. a private environment (so nothing touches the rest of your Mac) -----------------------
if ! "$HERE/.venv/bin/python" -c "import tkinter" >/dev/null 2>&1; then
    rm -rf "$HERE/.venv"
    $RUN "$PY" -m venv "$HERE/.venv" || { echo "  Could not make the environment."; read -r -p "  Press Return to close. " _; exit 1; }
fi
VPY="$HERE/.venv/bin/python"

# ---- 3. the firmware folder -----------------------------------------------------------------
mkdir -p "$HERE/firmware" && echo "  Firmware folder ready: $HERE/firmware"
echo

# ---- 4. the two MIDI libraries the installer needs ------------------------------------------
echo "  Installing the MIDI libraries (mido, python-rtmidi)..."
if ! $RUN "$VPY" -m pip install --disable-pip-version-check --quiet mido python-rtmidi; then
    echo
    echo "  The MIDI libraries did not install. Slipway will still start, and will offer to"
    echo "  try again the first time you press \"Launch on FM-1\". Continuing."
    echo "  If the messages above mention a compiler: type  xcode-select --install  in Terminal, let it finish,"
    echo "  then double-click install.command again."
fi
echo

# ---- 5. Slipway.app in your Applications folder, with the sailboat icon -----------------------
APP="$HOME/Applications/Slipway.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$HERE/slipway/slipway.icns" "$APP/Contents/Resources/Slipway.icns"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Slipway</string>
  <key>CFBundleDisplayName</key><string>Slipway</string>
  <key>CFBundleIdentifier</key><string>app.slipway.fm1</string>
  <key>CFBundleExecutable</key><string>slipway-launch</string>
  <key>CFBundleIconFile</key><string>Slipway</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
printf '#!/bin/bash\ncd %q || exit 1\nexec %s %q -m slipway\n' "$HERE" "$RUN" "$VPY" > "$APP/Contents/MacOS/slipway-launch"
chmod +x "$APP/Contents/MacOS/slipway-launch"
touch "$APP"
echo "  Made: $APP   (find it with Spotlight, or drag it to your Dock)"
echo
echo "  Starting Slipway. Next time, open Slipway from Applications."
echo "  (Keep this Slipway folder where it is: the app uses it.)"
open "$APP"
sleep 2
