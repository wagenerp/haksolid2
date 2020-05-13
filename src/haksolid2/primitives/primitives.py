from .. import dag
from .. import usability
from .. import transform
from ..math import *


class Primitive(dag.DAGNode):
	def __init__(s, extent):
		dag.DAGNode.__init__(s)
		s.extent = extent

	def __str__(s):
		return f"{s.__class__.__name__}({s.extent})"


class CuboidPrimitive(Primitive):
	def __init__(s, x=None, y=None, z=None):
		extent = None
		if isinstance(x, Iterable):
			extent = V(*x)
		else:
			if x is None:
				return ValueError("missing extent coordinate")
			if y is None and z is None:
				y = x
				z = x
			elif y is not None and z is not None:
				pass
			else:
				return ValueError("missing extent coordinate")
			extent = V(x, y, z)

		Primitive.__init__(s, extent)


class SpherePrimitive(Primitive):
	def __init__(s, r=None, d=None, segments=32):
		s.segments = segments

		if r is None and d is None: raise ValueError("missing radius / diameter")
		if r is not None and d is not None: raise ValueError("ambiguous radius")

		if r is None:
			extent = V(d, d, d)
		else:
			extent = V(r, r, r) * 2

		Primitive.__init__(s, extent)


class CylinderPrimitive(Primitive):
	def __init__(s, r=None, h=None, d=None, segments=32):
		s.segments = segments

		if r is None and d is None: raise ValueError("missing radius / diameter")
		if r is not None and d is not None: raise ValueError("ambiguous radius")
		if h is None: raise ValueError("missing height")

		if r is None:
			extent = V(d, d, h)
		else:
			extent = V(r * 2, r * 2, h)

		Primitive.__init__(s, extent)


class RectPrimitive(Primitive):
	def __init__(s, x=None, y=None):
		extent = None
		if isinstance(x, Iterable):
			if len(x) != 2: raise ValueError("two coordinates expected")
			x, y = x
			extent = V(x, y, 0)
		else:
			if x is None and y is None:
				return ValueError("missing extent coordinate")
			if y is None: y = x
			extent = V(x, y, 0)

		Primitive.__init__(s, extent)


class CirclePrimitive(Primitive):
	def __init__(s, r=None, d=None, segments=32):
		s.segments = segments

		if r is None and d is None: raise ValueError("missing radius / diameter")
		if r is not None and d is not None: raise ValueError("ambiguous radius")

		if r is None:
			extent = V(d, d, 0)
		else:
			extent = V(r, r, 0) * 2

		Primitive.__init__(s, extent)


class PrimitiveFactory:
	def __init__(s, primitive):
		s.primitive = primitive

	def __call__(s, anchor, *args, **kwargs):
		node = s.primitive(*args, *kwargs)
		node.unlink()
		return transform.translate(-0.5 * node.extent * anchor) * node


cuboid = usability.BoxAnchorPattern(PrimitiveFactory(CuboidPrimitive))
sphere = usability.BoxAnchorPattern(PrimitiveFactory(SpherePrimitive))
cylinder = usability.BoxAnchorPattern(PrimitiveFactory(CylinderPrimitive))
rect = usability.BoxAnchorPattern(PrimitiveFactory(RectPrimitive))
circle = usability.BoxAnchorPattern(PrimitiveFactory(CirclePrimitive))