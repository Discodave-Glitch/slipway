#!/bin/bash
# Starts Slipway without the Applications shortcut. Run install.command first.
cd "$(dirname "$0")" || exit 1
mkdir -p firmware
if [ ! -x .venv/bin/python ]; then
    echo "Run install.command first (double-click it)."; read -r -p "Press Return to close. " _; exit 1
fi
exec .venv/bin/python -m slipway
