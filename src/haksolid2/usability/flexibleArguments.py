from ..math import *


def getFlexibleExtent3(x, y, z):

	if isinstance(x, Iterable):
		extent = V(*x)
		if y is not None or z is not None:
			raise ValueError("ambiguous extent: vector and coordinates")
	else:
		if x is None:
			return ValueError("missing extent coordinate")
		if y is None and z is None:
			y = x
			z = x
		elif y is not None and z is not None:
			pass
		else:
			raise ValueError("missing extent coordinate")
		extent = V(x, y, z)
	return extent


def getFlexibleAxis3(x, y, z):

	if isinstance(x, Iterable):
		axis = V(*x)
		if y is not None or z is not None:
			raise ValueError("ambiguous axis: vector and coordinates")
	else:
		if x is None or y is None or z is None:
			raise ValueError("missing axis coordinate")
		axis = V(x, y, z)
	return axis


def getFlexibleExtent2(x, y):

	if isinstance(x, Iterable):
		if len(x) != 2: raise ValueError("two coordinates expected")
		x, y = x
		extent = V(x, y, 0)
	else:
		if x is None and y is None:
			raise ValueError("missing extent coordinate")
		if y is None: y = x
		extent = V(x, y, 0)
	return extent


def getFlexibleRadius(r, d):

	if r is None and d is None: raise ValueError("missing radius / diameter")
	if r is not None and d is not None: raise ValueError("ambiguous radius")

	if r is None:
		return d * 0.5
	else:
		return r


def getFlexibleMatrix(p=None, n=None, u=None, v=None, m=None, rectify=True):

	if m is None:
		if p is None: p = V(0, 0, 0)
		if n is not None and u is not None and v is None:
			v = n.cross(u)
		elif n is not None and u is None and v is not None:
			u = v.cross(n)
		elif n is None and u is not None and v is not None:
			n = u.cross(v)
		elif n is not None:
			u = V(0, 1, 0).cross(n)
			v = n.cross(u)
		elif u is not None:
			n = u.cross(V(0, 1, 0))
			v = n.cross(u)
		elif v is not None:
			n = V(1, 0, 0).cross(v)
			u = v.cross(n)
		else:
			n = V(0, 0, 1)
			u = V(1, 0, 0)
			v = V(0, 1, 0)
		if rectify:
			v = n.cross(u).normal
			u = v.cross(n).normal
			n = n.normal

		m = M((u.x, v.x, n.x, p.x), (u.y, v.y, n.y, p.y), (u.z, v.z, n.z, p.z),
		      (0, 0, 0, 1))
	return m