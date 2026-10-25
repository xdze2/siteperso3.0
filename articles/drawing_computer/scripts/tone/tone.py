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

# threshold / quantization
save(L>.5,'threshold')
q=np.round(L*3)/3; save(q,'quant4',bw=False)
save(L>rng.random(L.shape),'noise')
save(ordered(L,3),'bayer')
# working in linear: treat L as sRGB-ish display values (scene lum already display)
fs=diffuse(L,*FS); save(fs,'floyd')
save(diffuse(L,*ATK),'atkinson')
save(diffuse(L,*JJN),'jarvis')
# ramps
rows=[('threshold',ramp>.5),('noise',ramp>rng.random(ramp.shape)),('bayer',ordered(ramp,3)),
      ('floyd',diffuse(ramp,*FS)),('atkinson',diffuse(ramp,*ATK))]
stack=np.vstack([np.vstack([r[1],np.ones((6,500),bool)]) for r in rows])
save(stack,'ramp_compare')
# gamma: ramp 0..1 displayed values; correct = threshold in linear light
rl=lin(ramp)
wrong=diffuse(ramp,*FS)           # dithering sRGB values as if linear
right=diffuse(rl,*FS)             # target = linear light => dots density = linear
g=np.vstack([ramp, np.ones((6,500)), wrong, np.ones((6,500)), right])
save(np.where(np.arange(g.shape[0])[:,None]<60, g, g),'x_tmp',bw=False)  # unused
top=ramp; 
im=np.vstack([ramp,np.ones((6,500)),wrong.astype(float),np.ones((6,500)),right.astype(float)])
Image.fromarray((np.clip(im,0,1)*255).astype(np.uint8)).save(O+'gamma.png')
# blurred tone check: blur floyd, compare with source
bl=blurimg(fs.astype(float),2.5)
side=np.hstack([blurimg(L,0.01) if False else L, bl])
save(bl,'blur',bw=False)
# zoom crop (nearest)
def zoom(b,x,y,w,h,k,name):
    c=b[y:y+h,x:x+w]
    im=Image.fromarray((c*255).astype(np.uint8)).resize((w*k,h*k),Image.NEAREST); im.save(O+name+'.png')
zoom(fs,300,150,60,40,8,'zoom_floyd'); zoom(ordered(L,3),300,150,60,40,8,'zoom_bayer')
# compare pair for zoom (floyd | bayer) 
a=Image.open(O+'zoom_floyd.png'); b=Image.open(O+'zoom_bayer.png')
c=Image.new('L',(a.width+b.width+10,a.height),128); c.paste(a,(0,0)); c.paste(b,(a.width+10,0)); 
c=c.resize((c.width*500//c.width,c.height*500//c.width)) if c.width>500 else c
c.save(O+'zoom_pair.png')
import os; os.remove(O+'zoom_floyd.png'); os.remove(O+'zoom_bayer.png'); os.remove(O+'x_tmp.png')
# blue noise mask 64 (greedy void filling)
N=64; sig=1.5
fx=np.fft.fftfreq(N)*N
d=np.minimum(np.arange(N),N-np.arange(N)); D=d[:,None]**2+d[None,:]**2
ker=np.exp(-D/(2*sig*sig)); K=np.fft.rfft2(ker)
rank=np.zeros((N,N)); en=np.zeros((N,N)); filled=np.zeros((N,N),bool)
for i in range(N*N):
    if i==0: y,x=0,0
    else:
        e=np.where(filled,1e9,en); y,x=np.unravel_index(np.argmin(e+rng.random((N,N))*1e-6),e.shape)
    filled[y,x]=True; rank[y,x]=i
    en+=np.roll(np.roll(ker,y,0),x,1)
bn=(rank+.5)/(N*N)
T=np.tile(bn,(H//N+1,W//N+1))[:H,:W]
save(L>T,'bluenoise')
# halftone: clustered dot, rotated 45 deg, period 8
def halftone(a,p=7,ang=45):
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(float)
    t=np.deg2rad(ang); u=(xx*np.cos(t)+yy*np.sin(t))*np.pi/p*np.sqrt(2)/np.sqrt(2)
    v=(-xx*np.sin(t)+yy*np.cos(t))*np.pi/p
    s=(np.cos(u*1.0)+np.cos(v*1.0))/4+.5   # 0..1 spot function, high at centres of lattice
    # dark where a small: dot of ink grows with darkness; ink where (1-a)>= s'
    return (1-a)<(1-s)*0+ (1-s) if False else a>s
save(halftone(L,8),'halftone')
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
n=3500
# rejection sampling
pts=[]
while len(pts)<n:
    c=np.c_[rng.random(n*2)*W,rng.random(n*2)*H]
    k=rng.random(n*2)<dark[c[:,1].astype(int),c[:,0].astype(int)]
    pts.extend(c[k].tolist())
P=np.array(pts[:n])
for it in range(25):
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
for x,y in P: d2.ellipse([x-.9,y-.9,x+.9,y+.9],fill=0)
im2.point(lambda v:255 if v>127 else 0).convert('1').save(O+'stipple.png')
print('ok')
