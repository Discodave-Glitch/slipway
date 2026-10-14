"""Draws the Slipway logo (the same shapes as the app header) and saves slipway/slipway.ico.
Needs Pillow (pip install pillow). Only for developers: the finished .ico is shipped, so users don't need this."""
import os
from PIL import Image, ImageDraw

SEA, BRASS, SAIL, HULL, KEY_W, KEY_B = "#2f7f95", "#e0b04a", "#f2ede9", "#0b0909", "#e9e2de", "#0b0909"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "slipway", "slipway.ico")


def logo(size):
    S = 2048                       # draw big, shrink for smooth edges
    k = S / 66.0                   # the header logo is a 64-unit circle; 1 unit of margin each side
    off = 1

    def P(*pts):
        return [((v + off) * k) for v in pts]

    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse(P(0, 0, 64, 64), fill=SEA, outline=BRASS, width=int(3 * k))
    d.polygon(P(18, 12, 18, 38, 40, 38), fill=SAIL)                       # mainsail
    d.polygon(P(14, 16, 14, 38, 5, 38), fill=SAIL)                        # jib
    d.line(P(18, 8, 18, 42), fill=HULL, width=int(2 * k))                  # mast
    d.polygon(P(6, 41, 44, 41, 38, 49, 12, 49), fill=HULL)                # hull
    for i in range(6):                                                    # keys on the ramp
        kx = 10 + i * 8
        d.rectangle(P(kx, 52, kx + 7, 58), fill=KEY_W, outline=HULL, width=max(1, int(0.6 * k)))
    for i in (0, 1, 3, 4):
        kx = 10 + i * 8 + 5
        d.rectangle(P(kx, 52, kx + 5, 56), fill=KEY_B)
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [logo(s) for s in sizes]
    imgs[-1].save(OUT, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
    print("saved", os.path.normpath(OUT), os.path.getsize(OUT), "bytes")
