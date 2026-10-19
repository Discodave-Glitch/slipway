"""The step-by-step USB recovery guide shown in Stuck? Rescue -> "Black screen? Full recovery guide".

For an FM-1 that does not start at all (black screen) and shows up on the computer as "WL82 UBOOT1.00".
Based on the method that recovered a real soft-bricked FM-1 (jl-uboot-tool by kagaimiq, written to flash 0x4000 only),
plus the Linux-in-VirtualBox route for Windows PCs that refuse raw USB access ("Access is denied").
"""

TITLE = "Black screen? Full USB recovery guide"

INTRO = ("Use this when the FM-1 shows nothing at all, Slipway cannot find it, and the computer lists it as "
         "\"WL82 UBOOT1.00\" (a USB drive with no size). That is the chip's built-in rescue mode. This guide puts the "
         "official V15 firmware back by writing it at address 0x4000 ONLY. Nothing below 0x4000 is ever written, so the "
         "chip can always be recovered again. At your own risk. It worked on a real unit.")

# (heading, [lines]). A line starting with "  " is shown as a command / code line.
SECTIONS = [
    ("Before you start", [
        "Use a USB DATA cable, plugged straight into the computer (no hub).",
        "Only ever type the commands in this guide. Never type erase, erasechip, or a write at any other address.",
        "Letters l and 1 look alike in a terminal. Type commands exactly, or copy and paste them.",
        "You need: this PC, Python (python.org, tick \"Add python.exe to PATH\"), M-VAVE's official FM-1.fwsc "
        "(m-vave.com, product FM-1), and jl-uboot-tool by kagaimiq (github.com/kagaimiq/jl-uboot-tool, Code -> Download ZIP).",
        "fm1_extract_app.py, a small script that pulls the right image out of the .fwsc, by Acrawf1: "
        "gist.github.com/Acrawf1/ae2b9930b49231db397568cfc2abc2a8 (use Download ZIP, or the Raw button and Save As).",
        "Unzip jl-uboot-tool to a short folder like C:\\fm1\\jl-uboot-tool-main. Put FM-1.fwsc AND fm1_extract_app.py "
        "in that same folder.",
    ]),
    ("Step 1 - Make the file to write (Windows PowerShell as Administrator)", [
        "Right-click Start -> Terminal (Admin).",
        "  cd C:\\fm1\\jl-uboot-tool-main",
        "  python -m pip install -r requirements.txt",
        "  python fm1_extract_app.py FM-1.fwsc app_v15.bin",
        "It must print:  identity: FM-1_015   and   app sha256: 6edf3c37fb5bbbc33607c89375ee024d5477c17914d72221c8c68e58a8255686",
        "If that hash is different, STOP: the .fwsc is not the genuine V15, or is damaged.",
    ]),
    ("Step 2 - Find the FM-1 (Windows)", [
        "Switch the FM-1 ON, then plug it in. If Windows offers to format a disk, press Cancel.",
        "  Get-CimInstance Win32_DiskDrive | Format-Table Index, Model, InterfaceType",
        "Look for \"WL82 UBOOT1.00 USB Device\" and note its Index number. Never point the tool at any other disk.",
        "Quick test that Windows will let you talk to it (replace 6 with your Index):",
        "  python -c \"from scsiio import SCSIDev; d=SCSIDev(r'\\\\.\\PhysicalDrive6'); b=bytearray(36); d.execute(b'\\x12\\x00\\x00\\x00\\x24\\x00', None, b); print(bytes(b))\"",
        "If it prints bytes containing UBOOT, carry on at Step 3. If it says \"[WinError 5] Access is denied\" "
        "even as Administrator, some Windows 11 PCs simply refuse - go to \"Plan B\" below. (Antivirus was not the cause in the case this "
        "guide came from, and rebooting did not help.)",
    ]),
    ("Step 3 - Connect (Windows)", [
        "  python jluboottool.py --device \"\\\\.\\PhysicalDrive6\"",
        "The Quick info MUST show  Chip key: 0x980F  and  ID: 0x856014. If not, type exit and stop.",
    ]),
    ("Step 4 - Back up the whole flash. Do NOT skip", [
        "At the =>JL: prompt, one line at a time, waiting for the prompt to come back each time:",
        "  read 0 0x100000 backup.bin",
        "  read 0 0x100000 backup2.bin",
        "  exit",
        "Check both copies are identical (the hashes must match; this proves the connection is reliable):",
        "  Get-FileHash backup.bin, backup2.bin",
        "Keep backup.bin somewhere safe. It is your undo button, and your saved projects are in it.",
    ]),
    ("Step 5 - Write V15", [
        "Connect again (Step 3), then type exactly:",
        "  write 0x4000 app_v15.bin",
        "You see Erasing, then Writing. Do not unplug anything until =>JL: comes back (about 10 seconds).",
    ]),
    ("Step 6 - Check every byte", [
        "  read 0x4000 0x8F000 verify.bin",
        "  exit",
        "Back at the normal prompt (PS ...>, not =>JL:):",
        "  Get-FileHash verify.bin",
        "It must be 6EDF3C37FB5BBBC33607C89375EE024D5477C17914D72221C8C68E58A8255686. If not, run the write again.",
    ]),
    ("Step 7 - Restart", [
        "Unplug USB, switch the FM-1 off, wait 5 seconds, switch it on. It should start on stock V15.",
        "Then open Slipway: Save stock V15 now (if you have not), and the FM-1 is back where it began.",
    ]),
    ("Plan B - Windows says \"Access is denied\": use Linux inside VirtualBox (worked, no restart needed)", [
        "1. Install VirtualBox AND its Extension Pack (virtualbox.org/wiki/Downloads, same version number). Download an Ubuntu "
        "Desktop ISO (ubuntu.com/download/desktop).",
        "2. VirtualBox -> New. Name FM1, pick the ISO, TICK \"Skip Unattended Installation\" (otherwise Finish stays greyed out), "
        "4096 MB memory, 2-4 CPUs, 25 GB disk. If Finish is still greyed out, cancel and start the wizard again, "
        "filling in only the top section.",
        "3. Settings -> Display: Video Memory 128 MB, Graphics Controller VMSVGA, 3D acceleration OFF. "
        "Settings -> System: tick Enable EFI. Settings -> USB: enable the controller, USB 3.0 (xHCI). "
        "(If Settings shows too few options, switch it to Expert mode.)",
        "4. Start the VM. Pick \"Ubuntu (safe graphics)\" if the normal one freezes on the splash screen. It can sit on the "
        "logo for several minutes. Choose \"Try Ubuntu\" (NOT Install).",
        "5. Share your jl-uboot-tool folder: Devices -> Shared Folders -> Shared Folders Settings -> Add, folder = your "
        "C:\\fm1\\jl-uboot-tool-main (with app_v15.bin made in Step 1), name fm1, Make Permanent. Backups saved there stay on Windows.",
        "6. In Ubuntu press Ctrl+Alt+T for a terminal and type:",
        "  sudo mkdir -p /mnt/fm1 && sudo mount -t vboxsf fm1 /mnt/fm1",
        "  cd /mnt/fm1",
        "  sudo apt update && sudo apt install -y python3-pip",
        "  sudo pip install --break-system-packages -r requirements.txt",
        "  sudo modprobe sg",
        "7. Switch the FM-1 on, plug it in, and in the VM menu choose Devices -> USB -> tick \"WL82 UBOOT1.00\".",
        "8. Run (on Linux the tool finds the FM-1 by itself, give no path):",
        "  sudo python3 jluboottool.py",
        "Then do Step 4 (backups), Step 5 (write) and Step 6 (verify) exactly as above, using  sha256sum  instead of Get-FileHash:",
        "  sha256sum backup.bin backup2.bin app_v15.bin verify.bin",
        "Power the FM-1 off and on without the cable (Step 7). Delete the VM when you are happy.",
    ]),
    ("Plan C - You only have a Mac (macOS is not supported by the tool)", [
        "jl-uboot-tool does not work on macOS, so the steps above cannot be run directly on a Mac. NOT tested by the author. Options:",
        "1. Easiest: borrow a Windows or Linux PC for 20 minutes and follow Steps 1-7 there.",
        "2. Intel Mac: do Plan B with VirtualBox for macOS (virtualbox.org). Use the same VM settings and Ubuntu commands; "
        "the shared folder is your Mac folder with app_v15.bin (make that file on any PC, or on the Mac with "
        "python3 fm1_extract_app.py FM-1.fwsc app_v15.bin). macOS may ask you to allow VirtualBox in "
        "System Settings -> Privacy & Security, and to allow USB access.",
        "3. Apple Silicon Mac (M1 and newer): VirtualBox is not suitable. UTM (mac.getutm.app) with an Ubuntu ARM image "
        "can pass a USB device through (UTM: USB icon -> choose WL82 UBOOT1.00). Then follow Plan B from step 6 inside Ubuntu. "
        "This is the least certain route; if it will not see the device, use option 1.",
        "In every case the golden rules stay: back up twice and compare hashes, write at 0x4000 only, verify the hash.",
    ]),
    ("If the FM-1 still will not start afterwards", [
        "A known cause: leftover data from an old Felucca 0.9-beta stops newer Felucca firmware from starting. The fix "
        "(after the backup above) is to erase two small data areas, then power-cycle:",
        "  erase 0x97000 0x8000",
        "  erase 0xFC000 0x2000",
        "This erases Felucca's saved projects and settings (they stay in your backup). Use it only for that case.",
        "Not showing as WL82 UBOOT1.00 at all? Then this guide does not apply; the hardware route is the FM-1 Transporter "
        "(github.com/kurogedelic/FM-1-transporter).",
    ]),
    ("Credits", [
        "jl-uboot-tool by kagaimiq (MIT). Felucca and FM-1 Transporter by Leo Kuroshita / Hugelton Instruments. "
        "fm1_extract_app.py by Acrawf1. Method first written up in the r/MVaveFM1 \"Unbricking a softbricked FM-1\" guide.",
    ]),
]


def as_text():
    """The whole guide as plain text (for 'Save as text file')."""
    out = [TITLE, "=" * len(TITLE), "", INTRO, ""]
    for head, lines in SECTIONS:
        out += [head, "-" * len(head)]
        out += lines
        out.append("")
    return "\n".join(out)
