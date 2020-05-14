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
