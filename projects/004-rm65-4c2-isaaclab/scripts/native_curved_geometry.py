"""Finite-source-surface and convex-vertex geometry; no simulator or asset writes."""
import numpy as np
from scipy.spatial import ConvexHull


def closest_source_surface(point, triangles):
    p, t=np.asarray(point,float),np.asarray(triangles,float)
    if p.shape!=(3,) or t.ndim!=3 or t.shape[1:]!=(3,3) or not len(t) or not np.isfinite(np.r_[p,t.ravel()]).all():
        raise ValueError('finite point and nonempty triangles required')
    a,b,c=t[:,0],t[:,1],t[:,2];ab=b-a;ac=c-a;n=np.cross(ab,ac);nn=np.einsum('ij,ij->i',n,n)
    if np.any(nn<=0):raise ValueError('degenerate source triangle')
    ap=p-a;projection=ap-(np.einsum('ij,ij->i',ap,n)/nn)[:,None]*n
    beta=np.einsum('ij,ij->i',np.cross(projection,ac),n)/nn
    gamma=np.einsum('ij,ij->i',np.cross(ab,projection),n)/nn
    closest=a+projection;inside=(beta>=0)&(gamma>=0)&(beta+gamma<=1)
    distance2=np.where(inside,np.einsum('ij,ij->i',closest-p,closest-p),np.inf)
    for start,end in [(a,b),(b,c),(c,a)]:
        edge=end-start;f=np.einsum('ij,ij->i',p-start,edge)/np.einsum('ij,ij->i',edge,edge)
        candidate=start+np.clip(f,0,1)[:,None]*edge;d2=np.einsum('ij,ij->i',candidate-p,candidate-p)
        improve=d2<distance2;closest[improve]=candidate[improve];distance2=np.minimum(distance2,d2)
    i=int(np.argmin(distance2))
    return dict(distance_m=float(np.sqrt(distance2[i])),triangle_index=i,nearest_point=closest[i].tolist(),normal=(n[i]/np.sqrt(nn[i])).tolist())


def solid_winding_number(point, triangles):
    """Oriented solid-angle sum; requires separately verified closed mesh topology."""
    p,t=np.asarray(point,float),np.asarray(triangles,float)
    if p.shape!=(3,) or t.ndim!=3 or t.shape[1:]!=(3,3) or not np.isfinite(np.r_[p,t.ravel()]).all():
        raise ValueError('finite point and triangles required')
    a,b,c=(t[:,i]-p for i in range(3));la,lb,lc=(np.linalg.norm(x,axis=1) for x in (a,b,c))
    numerator=np.einsum('ij,ij->i',a,np.cross(b,c))
    denominator=la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb
    return float(np.sum(2*np.arctan2(numerator,denominator))/(4*np.pi))


def hull_from_vertices(vertices):
    v=np.asarray(vertices,float)
    if v.ndim!=2 or v.shape[1]!=3 or len(v)<4 or not np.isfinite(v).all():
        raise ValueError('finite 3-D hull vertices required')
    h=ConvexHull(v);tri=v[h.simplices].copy()
    reverse=np.einsum('ij,ij->i',np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),h.equations[:,:3])<0
    tri[reverse]=tri[reverse][:,[0,2,1]]
    return dict(vertices=v,planes=h.equations.copy(),triangles=tri)


def closest_normal_ray_interval(point, normal, hulls):
    """Nearest occupied interval along a normal line, from vertex support planes.

    Its upper endpoint is a directional surface offset, not Euclidean distance.
    Merge intervals before selecting one; internal hull faces are not boundaries.
    """
    p,n=np.asarray(point,float),np.asarray(normal,float)
    if p.shape!=(3,) or n.shape!=(3,) or not np.isfinite(np.r_[p,n]).all() or np.linalg.norm(n)<1e-12:
        raise ValueError('finite point and nonzero normal required')
    n=n/np.linalg.norm(n);intervals=[]
    for hull in hulls:
        planes=hull['planes'];den=planes[:,:3]@n;rhs=-(planes[:,:3]@p+planes[:,3])
        pos,neg,parallel=den>1e-12,den < -1e-12,np.abs(den)<=1e-12
        if np.any(rhs[parallel] < -1e-10):continue
        low=float(np.max(rhs[neg]/den[neg])) if neg.any() else -np.inf
        high=float(np.min(rhs[pos]/den[pos])) if pos.any() else np.inf
        if low<=high+1e-10 and np.isfinite([low,high]).all():intervals.append([low,high])
    if not intervals:return dict(hit=False,intervals=[],outward_boundary_offset_m=None,source_point_in_hull_union=False)
    merged=[]
    for lo,hi in sorted(intervals):
        if merged and lo<=merged[-1][1]+1e-10:merged[-1][1]=max(merged[-1][1],hi)
        else:merged.append([lo,hi])
    interval=min(merged,key=lambda x:max(x[0],-x[1],0.))
    return dict(hit=True,intervals=merged,outward_boundary_offset_m=interval[1],
                source_point_in_hull_union=any(lo<=1e-10 and hi>=-1e-10 for lo,hi in merged))
