import numpy as np
from PIL import Image, ImageDraw
import os; HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, '..', 'scene') + '/'
O = os.path.join(HERE, '..', '..', 'images', 'tone_')
rng=np.random.default_rng(3)
L=np.load(S+'lum.npy').astype(float); H,W=L.shape
ramp=np.tile(np.linspace(0,1,500),(60,1))
def save(a,n,bw=True):
    a=np.asarray(a)
    if a.dtype==bool: im=Image.fromarray((a*255).astype(np.uint8)).convert('L')
    else: im=Image.fromarray(np.clip(a*255+.5,0,255).astype(np.uint8))
    if bw: im=im.point(lambda v:255 if v>127 else 0).convert('1')
    im.save(O+n+'.png')
def lin(x): return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x): return np.where(x<=.0031308,x*12.92,1.055*np.power(np.clip(x,0,1),1/2.4)-.055)
def bayer(n):
    m=np.array([[0]])
    for _ in range(n):
        m=np.block([[4*m,4*m+2],[4*m+3,4*m+1]])
    return m
def ordered(a,n=3):
    m=bayer(n); k=m.shape[0]; t=(m+.5)/(k*k)
    T=np.tile(t,(a.shape[0]//k+1,a.shape[1]//k+1))[:a.shape[0],:a.shape[1]]
    return a>T
def diffuse(a,kernel,div,serp=True):
    a=a.copy(); h,w=a.shape; out=np.zeros((h,w),bool)
    for y in range(h):
        rev=serp and y%2==1
        xs=range(w-1,-1,-1) if rev else range(w)
        for x in xs:
            o=a[y,x]>.5; out[y,x]=o
            e=a[y,x]-(1.0 if o else 0.0)
            for dx,dy,wt in kernel:
                xx=x+(-dx if rev else dx); yy=y+dy
                if 0<=xx<w and yy<h: a[yy,xx]+=e*wt/div
    return out
FS=([(1,0,7),(-1,1,3),(0,1,5),(1,1,1)],16)
JJN=([(1,0,7),(2,0,5),(-2,1,3),(-1,1,5),(0,1,7),(1,1,5),(2,1,3),(-2,2,1),(-1,2,3),(0,2,5),(1,2,3),(2,2,1)],48)
ATK=([(1,0,1),(2,0,1),(-1,1,1),(0,1,1),(1,1,1),(0,2,1)],8)
def blurimg(a,s):
    r=int(3*s); x=np.arange(-r,r+1); g=np.exp(-x**2/(2*s*s)); g/=g.sum()
    p=np.pad(a,r,mode='edge')
    p=np.apply_along_axis(lambda v:np.convolve(v,g,'valid'),0,p)
    return np.apply_along_axis(lambda v:np.convolve(v,g,'valid'),1,p)

# halftone: clustered dot, rotated 45 deg, period 8
def halftone(a,p=7,ang=45):
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(float)
    t=np.deg2rad(ang); u=(xx*np.cos(t)+yy*np.sin(t))*np.pi/p*np.sqrt(2)/np.sqrt(2)
    v=(-xx*np.sin(t)+yy*np.cos(t))*np.pi/p
    s=(np.cos(u*1.0)+np.cos(v*1.0))/4+.5   # 0..1 spot function, high at centres of lattice
    # dark where a small: dot of ink grows with darkness; ink where (1-a)>= s'
    return (1-a)<(1-s)*0+ (1-s) if False else a>s

# line screen
def linescreen(a,p=6,ang=45):
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(float); t=np.deg2rad(ang)
    u=(xx*np.cos(t)+yy*np.sin(t))*2*np.pi/p
    s=(np.cos(u)+1)/2
    return a>s
save(linescreen(L,6),'linescreen')
# weighted voronoi stippling
Ls=L; dark=1-np.clip(Ls,0,1)+0.02
ys,xs=np.mgrid[0:H:2,0:W:2]; px=np.c_[xs.ravel(),ys.ravel()].astype(float); wt=dark[0:H:2,0:W:2].ravel()
n=4000
# rejection sampling
pts=[]
while len(pts)<n:
    c=np.c_[rng.random(n*2)*W,rng.random(n*2)*H]
    k=rng.random(n*2)<dark[c[:,1].astype(int),c[:,0].astype(int)]
    pts.extend(c[k].tolist())
P=np.array(pts[:n])
for it in range(30):
    idx=np.empty(len(px),int)
    for s in range(0,len(px),6000):
        d2=((px[s:s+6000,None,:]-P[None,:,:])**2).sum(2); idx[s:s+6000]=d2.argmin(1)
    m=np.bincount(idx,wt,n); cx=np.bincount(idx,wt*px[:,0],n); cy=np.bincount(idx,wt*px[:,1],n)
    ok=m>1e-9; P[ok,0]=cx[ok]/m[ok]; P[ok,1]=cy[ok]/m[ok]
S4=3
im=Image.new('1',(W*S4,H*S4),1); dr=ImageDraw.Draw(im)
for x,y in P:
    r=0.9*S4/1.0; dr.ellipse([x*S4-r,y*S4-r,x*S4+r,y*S4+r],fill=0)
im=im.resize((W,H),Image.LANCZOS).convert('L')
# render dots at 1px-ish at native res for crispness
im2=Image.new('L',(W,H),255); d2=ImageDraw.Draw(im2)
for x,y in P: d2.ellipse([x-1.1,y-1.1,x+1.1,y+1.1],fill=0)
im2.point(lambda v:255 if v>127 else 0).convert('1').save(O+'stipple.png')
print('ok')
