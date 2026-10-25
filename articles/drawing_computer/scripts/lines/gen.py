import numpy as np, random, math, shutil
from PIL import Image, ImageDraw, ImageFilter
import os; HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, '..', 'scene') + '/'; O = os.path.join(HERE, '..', '..', 'images', 'lines_')
lum=np.load(S+'lum.npy'); nor=np.load(S+'normal.npy'); dep=np.load(S+'depth.npy'); oid=np.load(S+'oid.npy')
H,W=lum.shape
shutil.copy(S+'depth.png',O+'depth.png'); shutil.copy(S+'normal.png',O+'normal.png')
def save(a,n): Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8)).save(O+n+'.png')
def pad(a): return np.pad(a,1,mode='edge')
def conv(a,k):
    r=k.shape[0]//2; p=np.pad(a,r,mode='edge'); out=np.zeros_like(a)
    for i in range(k.shape[0]):
        for j in range(k.shape[1]): out+=k[i,j]*p[i:i+a.shape[0],j:j+a.shape[1]]
    return out
def gauss(a,s):
    r=int(3*s)+1; x=np.arange(-r,r+1); g=np.exp(-x**2/(2*s*s)); g/=g.sum()
    p=np.pad(a,((0,0),(r,r)),mode='edge'); t=sum(g[i]*p[:,i:i+a.shape[1]] for i in range(len(g)))
    p=np.pad(t,((r,r),(0,0)),mode='edge'); return sum(g[i]*p[i:i+a.shape[0],:] for i in range(len(g)))
def sobel(a):
    p=pad(a)
    gx=-p[:-2,:-2]+p[:-2,2:]-2*p[1:-1,:-2]+2*p[1:-1,2:]-p[2:,:-2]+p[2:,2:]
    gy=-p[:-2,:-2]-2*p[:-2,1:-1]-p[:-2,2:]+p[2:,:-2]+2*p[2:,1:-1]+p[2:,2:]
    return np.hypot(gx,gy)
rng=np.random.default_rng(1)
# 2 sobel on noisy-ish luminance
g=sobel(lum); save(1-np.clip((g-0.04)*9,0,1),'sobel')
# 3 g-buffer edges
idp=1/dep; lap=np.abs(conv(idp,np.array([[0,1,0],[1,-4,1],[0,1,0]],float))); ed=lap*30; en=sobel(nor[...,0])+sobel(nor[...,1])+sobel(nor[...,2])
eo=sobel(oid.astype(float))
E=(ed>0.5)|(en>1.2)|(eo>0.5)
Ef=E.astype(float); save(1-Ef,'gbuf_edges')
# 4 DoG / XDoG
s=1.2; k=1.6; dd=gauss(lum,s)-gauss(lum,s*k)
dog=np.where(dd<-0.0012,0.0,1.0); save(dog,'dog')
u=dd*40; eps=-0.03; phi=6
x=np.where(u>=eps,1.0,1+np.tanh(phi*(u-eps)))
save(x,'xdog')
# 5 variable weight: edges with width by depth and by type
img=Image.new('L',(W,H),255); 
def disk(a,r):
    r=int(r); 
    return a
yy,xx=np.nonzero(E)
sil=(eo>0.5)
canvas=np.zeros((H,W))
for y,x in zip(yy,xx):
    z=dep[y,x]; z=min(z,30)
    w=1.0+ (2.2 if sil[y,x] else 0)*np.clip((14-z)/10,0.3,1) + 1.2*np.clip((12-z)/10,0,1)
    r=w/2
    y0,y1,x0,x1=int(max(0,y-2)),int(min(H,y+3)),int(max(0,x-2)),int(min(W,x+3))
    Y,X=np.mgrid[y0:y1,x0:x1]; m=np.clip(r+0.5-np.hypot(Y-y,X-x),0,1)
    canvas[y0:y1,x0:x1]=np.maximum(canvas[y0:y1,x0:x1],m)
save(1-canvas,'weight')
np.save(os.path.join(HERE, 'E.npy'), E)
