"""Generate Redline PWA icons: 192, 512, maskable-512, apple-touch-180, favicon-64.
Design: dark-navy tile, white document with folded corner, gray text lines,
one solid red redaction bar — the product in one glyph.
"""
from PIL import Image, ImageDraw
import os, pathlib, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent / "icons")
os.makedirs(OUT, exist_ok=True)

BG = (10, 15, 30, 255)        # #0A0F1E app background
PAPER = (255, 255, 255, 255)
LINE = (201, 212, 227, 255)   # gray text lines
RED = (214, 69, 69, 255)      # #D64545 redline accent
FOLD = (227, 233, 241, 255)   # folded corner


def draw_icon(size, scale=1.0):
    """Document glyph centered; scale shrinks content into maskable safe zone."""
    im = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(im)
    s = size * scale
    ox = oy = (size - s) / 2
    # document with folded corner (fold = 22% of width, top-right)
    w, h = s * 0.54, s * 0.68
    x0, y0 = ox + (s - w) / 2, oy + (s - h) / 2
    x1, y1 = x0 + w, y0 + h
    f = w * 0.24
    r = s * 0.02
    # body: rounded rect minus top-right notch -> draw as polygon+arcs
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=PAPER)
    # folded corner
    d.polygon([(x1 - f, y0), (x1, y0 + f), (x1 - f, y0 + f)], fill=FOLD)
    d.line([(x1 - f, y0), (x1, y0 + f)], fill=(180, 195, 212, 255), width=max(1, int(s * 0.006)))
    # text lines (4), inset 14%
    lx0, lx1 = x0 + w * 0.16, x1 - w * 0.16
    lh = h * 0.058
    gap = h * 0.135
    ys = [y0 + h * 0.22, y0 + h * 0.22 + gap, y0 + h * 0.22 + 2 * gap, y0 + h * 0.22 + 3 * gap]
    widths = [0.68, 0.60, 0.66, 0.42]
    for (yy, ww) in zip(ys, widths):
        d.rounded_rectangle([lx0, yy, lx0 + w * ww, yy + lh], radius=lh / 2, fill=LINE)
    # the redline: solid red bar covering line 3, slightly wider than the text line
    ry = ys[2]
    pad = lh * 0.45
    d.rounded_rectangle([lx0 - pad, ry - pad, lx0 + w * 0.74 + pad, ry + lh + pad],
                        radius=(lh + 2 * pad) / 2, fill=RED)
    return im


for name, size, scale in [
    ("icon-192.png", 192, 1.0),
    ("icon-512.png", 512, 1.0),
    ("icon-maskable-512.png", 512, 0.78),
    ("apple-touch-icon.png", 180, 0.94),
    ("favicon-64.png", 64, 0.94),
]:
    draw_icon(size, scale).save(f"{OUT}/{name}")
    print(name, os.path.getsize(f"{OUT}/{name}"), "bytes")

# verify: non-blank, right sizes
from PIL import Image as I
for name in ["icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon-64.png"]:
    im = I.open(f"{OUT}/{name}").convert("RGB")
    px = list(im.getdata())
    reds = sum(1 for p in px if p[0] > 170 and p[1] < 110 and p[2] < 110)
    dark = sum(1 for p in px if sum(p) < 150)
    print(f"{name}: {im.size}, red px {reds}, dark px {dark}")
