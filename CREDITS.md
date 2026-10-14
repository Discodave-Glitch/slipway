# Credits and licences

Slipway itself is MIT licensed (see `LICENSE`). It stands on other people's work. Here is what is used, who made it,
and how it is used.

## Used while Slipway runs (downloaded, not included in this repository)

| What | Who | Licence | How Slipway uses it |
|---|---|---|---|
| `fm1_install.py`, the FM-1 installer | Leo Kuroshita / Hugelton Instruments ([Felucca](https://github.com/hugelton/Felucca)) | GPL-3.0 | Downloaded from the Felucca repository on first use, checked, and run as a separate program. Slipway does not copy or modify it. |
| Firmware list | The community FM-1 firmware hub, [fm1.designburgapps.com](https://fm1.designburgapps.com) | n/a (public data) | The catalogue (`catalog.json`) is read at run time. |
| Firmware files (`.fwsc`) | Their individual authors | Each project's own licence | Downloaded from the authors' GitHub releases, only when you ask. Never included here. |
| Python and tkinter | Python Software Foundation | PSF | The runtime. |

## Referenced in the recovery guide (not included)

| What | Who | Licence |
|---|---|---|
| [jl-uboot-tool](https://github.com/kagaimiq/jl-uboot-tool) | kagaimiq | MIT |
| [FM-1 Transporter](https://github.com/kurogedelic/FM-1-transporter) (hardware route) | kurogedelic | MIT |
| `fm1_extract_app.py` ([gist](https://gist.github.com/Acrawf1/ae2b9930b49231db397568cfc2abc2a8)) | Acrawf1 | none stated, so it is linked, not copied |
| "Unbricking a softbricked FM-1" guide, r/MVaveFM1 | the Reddit author and u/International-Soup24 | n/a |

M-VAVE's official V15 firmware is theirs. It is not included; you supply your own copy and Slipway keeps it
on your computer only.

## Included in this repository

| What | Who | Licence |
|---|---|---|
| `slipway/ship_bell.wav` | Freesound community, "ship-bell-two-chimes-102730" | See the source page for its terms (see below) |
| Code, sailboat logo and icon | the Slipway author | MIT |

### About the ship bell
The bell was downloaded as `freesound_community-ship-bell-two-chimes-102730.mp3` and converted to WAV. Check its page
for the current licence before redistributing. If its terms do not allow it, delete `ship_bell.wav`:
Slipway runs fine without it, it just stays quiet.

## Not affiliated
Slipway is not made, endorsed or supported by M-VAVE or by the Felucca project. "M-VAVE", "FM-1" and "Felucca" are
their owners' names, used here only to say what the software works with. Flashing firmware can leave a device
unusable. Use at your own risk, and keep a backup.
