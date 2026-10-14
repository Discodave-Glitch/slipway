"""What is known about FM-1 custom firmware, and the SAFETY NOTES about keys.

`keys` lists buttons/keys a firmware gives a special job that matters for getting back to the installer.
`safety` is the plain-English note shown before anything is put in a slot.
`checked` is True only where the note comes from that project's own README. Anything not checked is shown as
"not checked" and needs an extra confirmation. Add or correct entries here; nothing else needs changing.
"""

# Always kept, never removable: the way back.
STOCK = {
    "name": "Stock M-VAVE firmware (FM-1 V15)",
    "author": "M-VAVE",
    "description": "The official firmware. Every custom firmware's installer can put this back.",
    "url": "https://www.m-vave.com/download",
}

# Verified from the projects' own READMEs on 13 Oct 2026.
SEED = [
    {
        "repo": "hugelton/Felucca", "name": "Felucca",
        "keys": [],
        "safety": "No power-on key combination documented. HOME held opens its menu. To go back: run the web installer "
                  "again, or choose 'Return to official V15'. If an update is interrupted and the screen stays black, "
                  "the chip's own boot mode (a USB device called WL80UBOOT) still accepts the installer.",
        "checked": True,
    },
    {
        "repo": "charlesvestal/fm1-x0x", "name": "X0X",
        "keys": [],
        "safety": "No power-on key combination documented. If it keeps crashing it starts in a safe mode. The web "
                  "installer can put the stock firmware back.",
        "checked": True,
    },
    {
        "repo": "jadamsowers/fm1-fimba", "name": "FiMba-1",
        "keys": ["OCT-", "OCT+"],
        "safety": "USES OCT- and OCT+ TOGETHER. Hold both for 5 seconds = update mode (how you install the next "
                  "firmware). Hold both at power-on = hardware calibration instead. Do not remap or lock those two "
                  "buttons. After two failed starts it enters a safe mode, after four the chip's own update mode.",
        "checked": True,
    },
    {
        "repo": "charlesvestal/fm1-fomni", "name": "FoMni",
        "keys": [], "safety": "", "checked": False,
    },
]

# Firmware names you have as files but whose GitHub repo isn't known yet. Add the repo (+ Add repo) to link them.
KNOWN_NAMES = ["sloop", "melodee", "choralroot", "ghoulbox", "jangada", "hortator", "x0x", "felucca", "fimba", "fomni"]

SEARCHES = ["M-VAVE FM-1 firmware", "FM-1 custom firmware fwsc", "fm1 firmware M-VAVE"]
