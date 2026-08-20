"""Generate the geometry/dice figures for the mock paper with Pillow."""
from PIL import Image, ImageDraw, ImageFont
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
OUT = os.path.join(_REPO, "uploads", "mock2026")
os.makedirs(OUT, exist_ok=True)
S=3  # supersample for smooth lines
BLACK=(0,0,0); WHITE=(255,255,255)

def font(sz):
    for p in ['/System/Library/Fonts/Supplemental/Arial.ttf','/Library/Fonts/Arial.ttf','/System/Library/Fonts/Helvetica.ttc']:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz*S)
            except Exception: pass
    return ImageFont.load_default()

def canvas(w,h):
    im=Image.new('RGB',(w*S,h*S),WHITE); return im, ImageDraw.Draw(im)

def save(im,name):
    im=im.resize((im.width//S,im.height//S),Image.LANCZOS)
    im.save(f'{OUT}/{name}'); print('  wrote',name,im.size)

def line(d,a,b,w=3): d.line([a[0]*S,a[1]*S,b[0]*S,b[1]*S],fill=BLACK,width=w*S)
def text(d,xy,s,sz=15,anchor='mm'): d.text((xy[0]*S,xy[1]*S),s,fill=BLACK,font=font(sz),anchor=anchor)

# ── Q70: rectangle ABCD with perpendicular PQ from P to side BC ──────────────
im,d=canvas(420,260)
# Label so that side BC is the RIGHT-hand vertical side, and PQ is a
# horizontal segment meeting it at 90 degrees — matching option 1 "PQ and BC".
A,B,C,D=(70,60),(330,60),(330,200),(70,200)
for p,q in [(A,B),(B,C),(C,D),(D,A)]: line(d,p,q)
text(d,(A[0]-16,A[1]-10),'A'); text(d,(B[0]+16,B[1]-10),'B')
text(d,(C[0]+16,C[1]+12),'C'); text(d,(D[0]-16,D[1]+12),'D')
P=(150,130); Q=(330,130)          # PQ horizontal, Q lands on side BC
line(d,P,Q)
text(d,(P[0]-16,P[1]),'P'); text(d,(Q[0]+16,Q[1]),'Q')
# right-angle marker at Q, between QP (pointing left) and QB (pointing up)
d.rectangle([(Q[0]-16)*S,(Q[1]-16)*S,Q[0]*S,Q[1]*S],outline=BLACK,width=2*S)
save(im,'q70-geom.png')

# ── Q71: asymmetric polygon + 4 transformed options ──────────────────────────
BASE=[(40,150),(40,40),(150,60),(95,85),(150,110),(80,110),(80,150)]  # asymmetric pennant, no self-symmetry
def poly(pts,name,w=200,h=200,dx=25,dy=25):
    im,d=canvas(w,h)
    d.polygon([((x+dx)*S,(y+dy)*S) for x,y in pts],outline=BLACK,fill=None,width=3*S)
    save(im,name)
def flipH(p,minx=40,maxx=150): return [(minx+maxx-x,y) for x,y in p]
def flipV(p,miny=40,maxy=150):  return [(x,miny+maxy-y) for x,y in p]
def rot90(p):
    """True 90-degree clockwise rotation, re-centred on the original bbox."""
    xs=[x for x,_ in p]; ys=[y for _,y in p]
    cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2
    r=[(cx-(y-cy), cy+(x-cx)) for x,y in p]
    rxs=[x for x,_ in r]; rys=[y for _,y in r]
    ox=cx-(min(rxs)+max(rxs))/2; oy=cy-(min(rys)+max(rys))/2
    return [(x+ox,y+oy) for x,y in r]
poly(BASE,'q71-stem.png')
poly(rot90(BASE),'q71-opt1.png')      # rotated 90 cw
poly(flipV(BASE),'q71-opt2.png')      # inverted vertically
poly(flipH(BASE),'q71-opt3.png')      # mirror  <-- correct (option 3)
poly(BASE,'q71-opt4.png')             # identical

# ── Q72: two 3D views of a die ───────────────────────────────────────────────
def pips(d,cx,cy,n,size=46):
    r=size/2; off=r*0.5; rr=size*0.075
    P={1:[(0,0)],2:[(-off,-off),(off,off)],3:[(-off,-off),(0,0),(off,off)],
       4:[(-off,-off),(off,-off),(-off,off),(off,off)],
       5:[(-off,-off),(off,-off),(0,0),(-off,off),(off,off)],
       6:[(-off,-off),(off,-off),(-off,0),(off,0),(-off,off),(off,off)]}[n]
    for dx,dy in P:
        d.ellipse([(cx+dx-rr)*S,(cy+dy-rr)*S,(cx+dx+rr)*S,(cy+dy+rr)*S],fill=BLACK)

def die(d,ox,oy,top,front,right,s=90,k=34):
    # front face
    f=[(ox,oy),(ox+s,oy),(ox+s,oy+s),(ox,oy+s)]
    d.polygon([(x*S,y*S) for x,y in f],outline=BLACK,width=3*S)
    # top face (parallelogram)
    t=[(ox,oy),(ox+k,oy-k),(ox+s+k,oy-k),(ox+s,oy)]
    d.polygon([(x*S,y*S) for x,y in t],outline=BLACK,width=3*S)
    # right face
    r=[(ox+s,oy),(ox+s+k,oy-k),(ox+s+k,oy+s-k),(ox+s,oy+s)]
    d.polygon([(x*S,y*S) for x,y in r],outline=BLACK,width=3*S)
    pips(d,ox+s/2,oy+s/2,front)
    pips(d,ox+s/2+k/2,oy-k/2,top,size=38)
    pips(d,ox+s+k/2,oy+s/2-k/2,right,size=38)

im,d=canvas(480,220)
die(d,60,70,top=4,front=2,right=3)
die(d,290,70,top=4,front=5,right=6)
text(d,(125,196),'View 1',13); text(d,(355,196),'View 2',13)
save(im,'q72-dice.png')

# Q8 is a scene illustration, not a geometric figure —
# see generate_q8_illustration.py.
