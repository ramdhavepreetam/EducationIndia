"""
Redraw Class 8 Paper I, Q65 option 4.

The vendor shipped opt4 byte-identical to opt1 (same cube, dot on the left face),
so the question effectively offered three choices instead of four. The key is
opt3, so it stayed answerable — but two indistinguishable distractors are a
defect either way.

The net carries three marked faces: shaded, dot and plus. The options show:
    opt1  left dot     right plain
    opt2  left plain   right plus
    opt3  left shaded  right plus     <- correct
    opt4  left shaded  right dot      <- redrawn here, a new combination

Style is matched to the vendor artwork: 435x435, isometric cube, same greys.
Deterministic — re-running produces a byte-identical PNG.
"""
import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
OUT = os.path.join(_REPO, "uploads", "mock2026c8p1")
os.makedirs(OUT, exist_ok=True)

S = 4                       # supersample factor
W = H = 435
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TOP = (245, 245, 245)       # sampled from the vendor images
SHADED = (120, 144, 156)
RIGHT = (189, 189, 189)
PLAIN = (224, 224, 224)

im = Image.new("RGB", (W * S, H * S), WHITE)
d = ImageDraw.Draw(im)

def poly(pts, fill):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=BLACK, width=3 * S)

# isometric cube geometry, matched to the vendor framing
cx, top_y = 217, 52
half, side, drop = 122, 165, 63
apex   = (cx, top_y)
left_t = (cx - half, top_y + drop)
right_t= (cx + half, top_y + drop)
mid    = (cx, top_y + 2 * drop)
left_b = (cx - half, top_y + drop + side)
right_b= (cx + half, top_y + drop + side)
mid_b  = (cx, top_y + 2 * drop + side)

poly([apex, right_t, mid, left_t], TOP)              # top face
poly([left_t, mid, mid_b, left_b], SHADED)           # left face  -> shaded
poly([mid, right_t, right_b, mid_b], RIGHT)          # right face -> carries the dot

# dot on the RIGHT face (opt1 puts it on the left; this is the new combination)
dot_c = ((mid[0] + right_b[0]) // 2, (right_t[1] + mid_b[1]) // 2)
r = 9
d.ellipse([(dot_c[0] - r) * S, (dot_c[1] - r) * S,
           (dot_c[0] + r) * S, (dot_c[1] + r) * S], fill=BLACK)

im = im.resize((W, H), Image.LANCZOS)
path = os.path.join(OUT, "q65_c8-opt4.png")
im.save(path)
print("wrote", path, im.size)
