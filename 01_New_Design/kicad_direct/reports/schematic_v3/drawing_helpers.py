def mm(v):return round(v*1.27,4)
def point(a):return [mm(x) for x in a]
def uid():return Q(str(uuid.uuid4()))
def fx(size=1.27,justify=('left','bottom')):return ['effects',['font',['size',size,size]],['justify',*justify]]
def place(ref,x,y,ang=0):
 o=objs[ref];one(o,'at')[1:]=[mm(x),mm(y),ang];positions[ref]=[x,y,ang]
 theta=math.radians(ang);pp=[]
 for u in children(libs[one(o,'lib_id')[1]],'symbol'):
  for p in children(u,'pin'):
   dx,dy,a=map(float,one(p,'at')[1:]);k=str(one(p,'number')[1])
   px=round(x+(dx*math.cos(theta)-dy*math.sin(theta))/1.27,6)
   py=round(y-(dx*math.sin(theta)+dy*math.cos(theta))/1.27,6)
   pins[(ref,k)]=(px,py,(a+ang)%360);pp.append((px,py))
 for prop in children(o,'property'):
  key=prop[1];at=one(prop,'at');e=one(prop,'effects');e[:]=fx(justify=('left',))
  at[1:]=[mm(x),mm(y),0]
  if key not in ['Reference','Value'] or ref.startswith('#'):e.append(['hide','yes']);continue
  if ref.startswith(('R','C')) and ang in (0,180):
   at[1:]=[mm(x+2),mm(y+(-1 if key=='Reference' else 1)),0]
   if ang==180:one(e,'justify')[1]='right'
  elif ref=='Q1':at[1:]=[mm(x+6),mm(y+(-1 if key=='Reference' else 1)),0]
  else:
   top=min(v[1] for v in pp)
   at[1:]=[mm(x),mm(top-(6 if key=='Reference' else 4)),90 if ang in (90,270) else 0]
   e.remove(one(e,'justify'))
def field(ref,x,y):
 for prop in children(objs[ref],'property'):
  if prop[1] in ['Reference','Value']:
   one(prop,'at')[1:]=[mm(x),mm(y+(0 if prop[1]=='Reference' else 2)),90 if positions[ref][2] in (90,270) else 0]
   one(prop,'effects')[:]=fx(justify=('left',))
def p(r,k):return pins[(r,str(k))][:2]
def n(r,k):return nets[(r,str(k))]
def seg(a,b,net):
 a=tuple(round(x,6) for x in a);b=tuple(round(x,6) for x in b)
 if a!=b:segments.append((a,b,net))
def path(net,*pts):
 for a,b in zip(pts,pts[1:]):seg(a,b,net)
def connect(a,b,*via):
 a=(a[0],str(a[1]));b=(b[0],str(b[1]))
 assert nets[a]==nets[b],(a,b,nets[a],nets[b])
 path(nets[a],p(*a),*via,p(*b));used.update([a,b])
def lead(a,*pts):
 a=(a[0],str(a[1]));path(nets[a],p(*a),*pts);used.add(a)
def lab(net,at,reason='net identifier',right=False):
 s.append(['label',Q(net),['at',*point(at),0],fx(justify=('right' if right else 'left','bottom')),['uuid',uid()]])
 label_reasons.append({'net':net,'at':at,'purpose':reason})
def rail(keys,y,tag=None):
 net=n(*keys[0]);xs=[]
 for a in keys:
  assert n(*a)==net
  q=p(*a);lead(a,(q[0],y));xs.append(q[0])
 path(net,(min(xs),y),(max(xs),y))
 if tag:lab(net,(min(xs),y),tag)
def note(x,y,value,size=1.27):
 s.append(['text',Q(value),['at',*point((x,y)),0],fx(size),['uuid',uid()]])
def heading(x,y,end,title):
 note(x,y,title,1.8)
 s.append(['polyline',['pts',['xy',*point((x,y+2))],['xy',*point((end,y+2))]],['stroke',['width',.254],['type','default']],['fill',['type','none']],['uuid',uid()]])
