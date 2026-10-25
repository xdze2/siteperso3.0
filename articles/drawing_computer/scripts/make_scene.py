# raytrace a tiny scene: ground plane, sphere, torus. outputs luminance, depth, normals, object id.
import numpy as np
from PIL import Image
W,H=500,360
import os; HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(HERE, 'scene') + '/'
os.makedirs(out, exist_ok=True)
ys,xs=np.mgrid[0:H,0:W]
u=(xs-W/2)/W*1.4; v=-(ys-H/2)/W*1.4
cam=np.array([0,1.2,4.0])
d=np.stack([u,v-0.25,-np.ones_like(u)],-1); d/=np.linalg.norm(d,axis=-1,keepdims=True)
def sd_scene(p):
    sph=np.linalg.norm(p-np.array([-0.7,0.6,0]),axis=-1)-0.6
    q=p-np.array([0.85,0.35,0.3])
    # torus tilted
    c,s=np.cos(0.6),np.sin(0.6)
    qx=q[...,0]; qy=c*q[...,1]-s*q[...,2]; qz=s*q[...,1]+c*q[...,2]
    tor=np.sqrt((np.sqrt(qx**2+qz**2)-0.45)**2+qy**2)-0.18
    gnd=p[...,1]+0.0
    stack=np.stack([gnd,sph,tor],-1)
    return stack.min(-1),stack.argmin(-1)
t=np.zeros((H,W)); hit=np.zeros((H,W),bool)
for i in range(200):
    p=cam+d*t[...,None]
    dist,_=sd_scene(p)
    hit|=dist<1e-3
    t=np.where(hit,t,t+dist*0.9)
t=np.minimum(t,30)
p=cam+d*t[...,None]
_,oid=sd_scene(p)
e=1e-3
n=np.stack([sd_scene(p+np.array(k))[0]-sd_scene(p-np.array(k))[0] for k in [[e,0,0],[0,e,0],[0,0,e]]],-1)
n/=np.linalg.norm(n,axis=-1,keepdims=True)+1e-9
L=np.array([-0.7,0.45,0.55]);L/=np.linalg.norm(L)
diff=np.clip((n*L).sum(-1),0,1)
# shadow
sh=np.ones((H,W)); ts=np.full((H,W),0.02)
for i in range(80):
    ps=p+n*2e-3+L*ts[...,None]
    dd,_=sd_scene(ps); sh=np.minimum(sh,np.clip(8*dd/ts,0,1)); ts+=np.clip(dd,0.01,0.3)
alb=np.where(oid==0,0.75,1.0)
lum=0.04+0.96*alb*diff*(0.25+0.75*sh)
sky=~hit|(t>25)
fog=1-np.exp(-0.06*t)
lum=lum*(1-fog)+0.9*fog
lum[sky]=0.92
oid[sky]=3
np.save(out+'lum.npy',lum.astype(np.float32)); np.save(out+'depth.npy',t.astype(np.float32))
np.save(out+'normal.npy',n.astype(np.float32)); np.save(out+'oid.npy',oid.astype(np.uint8))
Image.fromarray((lum*255).astype(np.uint8)).save(out+'lum.png')
Image.fromarray(((n*0.5+0.5)*255).astype(np.uint8)).save(out+'normal.png')
dn=np.clip(t/12,0,1); Image.fromarray((dn*255).astype(np.uint8)).save(out+'depth.png')
# ramp
r=np.tile(np.linspace(0,1,W),(60,1)); Image.fromarray((r*255).astype(np.uint8)).save(out+'ramp.png')
