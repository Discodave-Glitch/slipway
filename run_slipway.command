#!/bin/bash
# Starts Slipway without the Applications shortcut. Run install.command first.
cd "$(dirname "$0")" || exit 1
mkdir -p firmware
if [ ! -x .venv/bin/python ]; then
    echo "Run install.command first (double-click it)."; read -r -p "Press Return to close. " _; exit 1
fi
RUN=""
if [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ] && arch -arm64 .venv/bin/python -c "pass" >/dev/null 2>&1; then RUN="arch -arm64"; fi
exec $RUN .venv/bin/python -m slipway
