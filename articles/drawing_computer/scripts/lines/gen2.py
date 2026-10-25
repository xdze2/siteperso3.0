import numpy as np, math, random
from PIL import Image, ImageDraw
import os; HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, '..', 'scene') + '/'; O = os.path.join(HERE, '..', '..', 'images', 'lines_')
oid=np.load(S+'oid.npy'); H,W=oid.shape
rnd=random.Random(4); K=3
def bound(mask,n=90):
    ys,xs=np.nonzero(mask); cx,cy=xs.mean(),ys.mean()
    ang=np.arctan2(ys-cy,xs-cx); r=np.hypot(xs-cx,ys-cy)
    pts=[]
    for i in range(n):
        a0=-math.pi+2*math.pi*i/n; m=(ang>=a0)&(ang<a0+2*math.pi/n)
        rr=r[m].max() if m.any() else 0
        pts.append((cx+rr*math.cos(a0+math.pi/n),cy+rr*math.sin(a0+math.pi/n)))
    return pts
def smooth(v,k=3):
    n=len(v); return [tuple(sum(v[(i+j)%n][c] for j in range(-k,k+1))/(2*k+1) for c in (0,1)) for i in range(n)]
def wob(t,seed,amp,freq=3):
    return amp*(math.sin(freq*t+seed)+0.5*math.sin(2.3*freq*t+3*seed)+0.3*math.sin(5.1*freq*t+seed*7))
def stroke(d,pts,w0,jit,seed,col=20):
    # tapered, jittered polyline as short segments w/ varying width
    n=len(pts)
    for i in range(n-1):
        t=i/(n-1); w=w0*(0.35+0.65*math.sin(math.pi*t)**0.5)*(0.85+0.3*rnd.random())
        a=pts[i]; b=pts[i+1]
        d.line([(a[0]*K,a[1]*K),(b[0]*K,b[1]*K)],fill=col,width=max(1,int(w*K)))
def closed_sketch(d,P,w0,passes=2,over=0.12):
    n=len(P)
    for p in range(passes):
        seed=rnd.random()*10
        start=rnd.randint(0,n-1); m=int(n*(1+over*(1 if p==0 else 0.5)))
        pts=[]
        cx=sum(q[0] for q in P)/n; cy=sum(q[1] for q in P)/n
        for i in range(m+1):
            q=P[(start+i)%n]; t=i/n*2*math.pi
            dx,dy=q[0]-cx,q[1]-cy; L=math.hypot(dx,dy)+1e-6
            off=wob(t,seed,1.6)+ (rnd.random()-0.5)*0.5
            pts.append((q[0]+dx/L*off,q[1]+dy/L*off))
        # gap: drop a few points at the end for 2nd pass
        if p>0: pts=pts[:int(len(pts)*0.9)]
        stroke(d,pts,w0*(1.1 if p==0 else 0.7),0,seed)
def sketch(fn,sil_sph=True):
    im=Image.new('L',(W*K,H*K),245); d=ImageDraw.Draw(im)
    sph=smooth(bound(oid==1)); tor=smooth(bound(oid==2))
    closed_sketch(d,sph,3.2,2); closed_sketch(d,tor,3.0,2)
    # horizon & shadow lines, hand-drawn with overshoot
    y=np.nonzero((oid==3).any(axis=1))[0].max()
    def hline(x0,x1,y,w):
        n=60; pts=[(x0+(x1-x0)*i/n, y+wob(i/n*6,rnd.random()*9,0.9)) for i in range(n+1)]
        stroke(d,pts,w,0,0)
    hline(-5,W+5,y+1,1.6); hline(-5,W+5,y+4,0.9)
    # shadow: a few hatching strokes below objects
    for i in range(14):
        x0=150+i*18; yy=y+85+ (i%3)*5
        pts=[(x0+j*2.2,yy+j*-1.2+rnd.random()*0.6) for j in range(9)]
        stroke(d,pts,1.1,0,0)
    im=im.resize((W,H),Image.LANCZOS).crop((0,60,500,260)); im.save(O+fn)
sketch('sketchy.png')
# clean vs sketchy comparison reuse
# ---- depth demo
def trees(mode,fn):
    Wd,Hd=500,260; k=3
    im=Image.new('L',(Wd*k,Hd*k),245); d=ImageDraw.Draw(im)
    R=random.Random(11); hor=70; BG=245
    def line(p,w,g):
        for i in range(len(p)-1):
            d.line([(p[i][0]*k,p[i][1]*k),(p[i+1][0]*k,p[i+1][1]*k)],fill=int(g),width=max(1,int(w*k)))
    rules=(mode=='rules')
    for y in range(6,hor,7):
        line([(x,y) for x in (0,Wd)],0.5 if rules else 1.5,185 if rules else 25)
    zs=sorted([R.uniform(1.3,9) for _ in range(46)],reverse=True)
    for z in zs:
        x=R.uniform(0,Wd); base=hor+175/z; h=165/z; wd=h*0.36
        t=(z-1.3)/7.7
        g=25 if not rules else int(25+150*t**0.8)
        w=1.7 if not rules else max(0.4,2.4/z**0.75)
        tri=[(x,base-h),(x-wd,base),(x+wd,base)]
        d.polygon([(px*k,py*k) for px,py in tri],fill=BG)
        # ground tick
        line([(x-wd*1.4,base),(x+wd*1.4,base)],w*0.8,g)
        n=max(2,int(h/4)) if not rules else (int(h/4.5) if z<4.5 else (int(h/9) if z<7 else 0))
        for i in range(1,n):
            tt=i/n; y=base-h+h*tt; half=wd*tt
            a=0 if (not rules or z>=4.5) else R.uniform(-.5,.5)*half
            line([(x-half,y),(x+half,y+a)],w*0.7,g)
        if (not rules) or z<5.5:
            line(tri+[tri[0]],w,g)
        else:
            for q in range(3):
                p0,p1=tri[q],tri[(q+1)%3]
                for u in np.linspace(0,1,7):
                    px=p0[0]+(p1[0]-p0[0])*u; py=p0[1]+(p1[1]-p0[1])*u
                    d.ellipse([px*k-1.5,py*k-1.5,px*k+1.5,py*k+1.5],fill=175)
        line([(x,base),(x,base+4/z*2)],w*1.6,g)
    if rules:  # repoussoir: dark foreground bank + trunk
        poly=[(0,Hd),(0,170)]+[(i*12,185-18*math.sin(i*0.5)+R.uniform(-4,4)) for i in range(1,12)]+[(150,Hd)]
        d.polygon([(a*k,b*k) for a,b in poly],fill=18)
        d.rectangle([20*k,0,34*k,200*k],fill=18)
    else:
        poly=[(0,Hd),(0,170)]+[(i*12,185-18*math.sin(i*0.5)+R.uniform(-4,4)) for i in range(1,12)]+[(150,Hd)]
        d.polygon([(a*k,b*k) for a,b in poly],fill=BG); line(poly+[poly[0]],1.7,25)
        d.rectangle([20*k,0,34*k,200*k],fill=BG,outline=25,width=5)
    im.resize((Wd,Hd),Image.LANCZOS).save(O+fn)
trees('flat','depth_flat.png'); trees('rules','depth_rules.png')
