"""Q8 illustration: school children planting saplings and watering them in a garden."""
from PIL import Image, ImageDraw, ImageFont
import math, os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
OUT = os.path.join(_REPO, "uploads", "mock2026")
os.makedirs(OUT, exist_ok=True)
S=4                       # supersample
W,H=560,340
BLACK=(0,0,0)
SKIN=(255,224,189); SKIN2=(224,186,148)
SHIRT=(70,130,180); SHIRT2=(200,80,90); SHIRT3=(240,190,70)
SHORTS=(60,60,90)
GREEN=(60,150,70); GREEN_D=(40,110,55); LEAF=(90,175,90)
SOIL=(120,85,55); SOIL_D=(95,65,42)
GRASS=(150,205,140)
SKY=(226,244,255)
CAN=(150,155,160); CAN_D=(115,120,125)
WATER=(120,180,230)

im=Image.new('RGB',(W*S,H*S),SKY)
d=ImageDraw.Draw(im)

def P(*xy): return [c*S for c in xy]
def ell(box,**kw): d.ellipse(P(*box),**kw)
def rect(box,**kw): d.rectangle(P(*box),**kw)
def line(box,w=2,**kw): d.line(P(*box),width=w*S,**kw)
def poly(pts,**kw): d.polygon([c*S for p in pts for c in p],**kw)

def font(sz):
    for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/Library/Fonts/Arial.ttf']:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz*S)
            except Exception: pass
    return ImageFont.load_default()

# ── ground ───────────────────────────────────────────────────────────────────
rect((0,225,W,H),fill=GRASS)
# soil bed strip
poly([(0,250),(W,250),(W,286),(0,286)],fill=SOIL)
for x in range(0,W,14):
    line((x,252,x+7,258),w=1,fill=SOIL_D)

# ── sun ──────────────────────────────────────────────────────────────────────
ell((488,22,540,74),fill=(255,214,90))
for i in range(12):
    a=i*math.pi/6
    cx,cy=514,48
    line((cx+30*math.cos(a),cy+30*math.sin(a),cx+38*math.cos(a),cy+38*math.sin(a)),w=2,fill=(255,214,90))

# ── background tree (already grown) ──────────────────────────────────────────
rect((60,150,74,250),fill=(110,75,50))
ell((22,84,112,176),fill=GREEN_D)
ell((40,66,124,150),fill=GREEN)

def head(cx,cy,r=13,skin=SKIN):
    ell((cx-r,cy-r,cx+r,cy+r),fill=skin,outline=BLACK,width=1)
    # eyes + smile
    ell((cx-6,cy-4,cx-3,cy-1),fill=BLACK)
    ell((cx+3,cy-4,cx+6,cy-1),fill=BLACK)
    d.arc(P(cx-6,cy,cx+6,cy+8),start=10,end=170,fill=BLACK,width=1*S)

def sapling(cx,base,h=34,scale=1.0):
    """small young plant in a mound of soil"""
    ell((cx-16*scale,base-6,cx+16*scale,base+8),fill=SOIL_D)
    line((cx,base,cx,base-h),w=2,fill=(110,80,50))
    # leaf pair
    poly([(cx,base-h+4),(cx+15*scale,base-h-2),(cx+2,base-h+12)],fill=LEAF,outline=GREEN_D)
    poly([(cx,base-h+10),(cx-15*scale,base-h+4),(cx-2,base-h+18)],fill=LEAF,outline=GREEN_D)

# ── CHILD 1 (left): kneeling, PLANTING a sapling with hands in soil ─────────
c1x=150
head(c1x,164)
poly([(c1x-15,178),(c1x+15,178),(c1x+18,222),(c1x-18,222)],fill=SHIRT,outline=BLACK)   # torso
# kneeling: one shin flat on the ground, one knee up
poly([(c1x-18,222),(c1x+6,222),(c1x+10,250),(c1x-20,250)],fill=SHORTS,outline=BLACK)
poly([(c1x+6,222),(c1x+18,222),(c1x+40,246),(c1x+28,252)],fill=SHORTS,outline=BLACK)
# both arms reach down into the soil beside the sapling
line((c1x+13,188,c1x+44,234),w=5,fill=SKIN)
line((c1x-13,188,c1x+34,240),w=5,fill=SKIN)
ell((c1x+38,228,c1x+50,240),fill=SKIN,outline=BLACK,width=1)   # hand patting soil
ell((c1x+28,234,c1x+40,246),fill=SKIN,outline=BLACK,width=1)
sapling(c1x+64,252,h=30)

# ── CHILD 2 (middle): standing, holding a sapling ready to plant ────────────
c2x=286
head(c2x,140,skin=SKIN2)
poly([(c2x-15,154),(c2x+15,154),(c2x+17,206),(c2x-17,206)],fill=SHIRT2,outline=BLACK)
rect((c2x-16,206,c2x-3,252),fill=SHORTS,outline=BLACK)
rect((c2x+3,206,c2x+16,252),fill=SHORTS,outline=BLACK)
line((c2x-14,164,c2x-36,190),w=5,fill=SKIN2)      # arm out, cradling the pot
line((c2x+14,164,c2x+26,196),w=5,fill=SKIN2)
# sapling in a pot, resting in the hand
poly([(c2x-56,192),(c2x-30,192),(c2x-34,214),(c2x-52,214)],fill=SOIL_D,outline=BLACK)
line((c2x-43,192,c2x-43,168),w=2,fill=(110,80,50))
poly([(c2x-43,170,),(c2x-27,164),(c2x-41,178)],fill=LEAF,outline=GREEN_D)
poly([(c2x-43,175),(c2x-59,169),(c2x-45,183)],fill=LEAF,outline=GREEN_D)
ell((c2x-42,186,c2x-30,198),fill=SKIN2,outline=BLACK,width=1)   # hand on the pot rim

# ── CHILD 3 (right): WATERING a planted sapling with a watering can ────────
c3x=430
head(c3x,146)
poly([(c3x-15,160),(c3x+15,160),(c3x+17,210),(c3x-17,210)],fill=SHIRT3,outline=BLACK)
rect((c3x-16,210,c3x-3,252),fill=SHORTS,outline=BLACK)
rect((c3x+3,210,c3x+16,252),fill=SHORTS,outline=BLACK)
line((c3x-14,170,c3x-40,196),w=5,fill=SKIN)
ell((c3x-46,190,c3x-34,202),fill=SKIN,outline=BLACK,width=1)
# watering can
rect((c3x-78,196,c3x-42,226),fill=CAN,outline=BLACK,width=1)
poly([(c3x-78,202),(c3x-96,214),(c3x-78,214)],fill=CAN_D,outline=BLACK)   # spout
d.arc(P(c3x-70,182,c3x-48,206),start=180,end=360,fill=BLACK,width=2*S)     # handle
# water stream
for i in range(7):
    line((c3x-94-i*2, 214+i*4, c3x-98-i*2, 220+i*4), w=2, fill=WATER)
sapling(c3x-118,252,h=26)

# a couple more planted saplings along the bed
sapling(60,252,h=24)
sapling(360,252,h=22)

im=im.resize((W,H),Image.LANCZOS)
im.save(f'{OUT}/q8-picture.png')
print('wrote q8-picture.png',im.size)
