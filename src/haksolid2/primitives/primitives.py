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


class Primitive2D(dag.DAGNode):
	def __init__(s, extent):
		Primitive.__init__(s, extent)


class Primitive3D(dag.DAGNode):
	def __init__(s, extent):
		Primitive.__init__(s, extent)


class CuboidPrimitive(Primitive3D):
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

		Primitive3D.__init__(s, extent)


class SpherePrimitive(Primitive3D):
	def __init__(s, r=None, d=None, segments=32):
		s.segments = segments

		if r is None and d is None: raise ValueError("missing radius / diameter")
		if r is not None and d is not None: raise ValueError("ambiguous radius")

		if r is None:
			extent = V(d, d, d)
		else:
			extent = V(r, r, r) * 2

		Primitive3D.__init__(s, extent)


class CylinderPrimitive(Primitive3D):
	def __init__(s, r=None, h=None, d=None, segments=32, explicit=False):
		s.segments = segments
		s.explicit = explicit

		if r is None and d is None: raise ValueError("missing radius / diameter")
		if r is not None and d is not None: raise ValueError("ambiguous radius")
		if h is None: raise ValueError("missing height")

		if r is None:
			extent = V(d, d, h)
		else:
			extent = V(r * 2, r * 2, h)

		Primitive3D.__init__(s, extent)


class RectPrimitive(Primitive2D):
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

		Primitive2D.__init__(s, extent)


class CirclePrimitive(Primitive2D):
	def __init__(s, r=None, d=None, segments=32, explicit=False):
		s.segments = segments
		s.explicit = explicit

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
		node = s.primitive(*args, **kwargs)
		node.unlink()
		return transform.translate(-0.5 * node.extent * anchor) * node


class BoxAnchorExplicitPattern(usability.BoxAnchorPattern):
	def __init__(s, target, defaultAnchor=V(0, 0, 0), explicit=False):
		usability.BoxAnchorPattern.__init__(s, target, defaultAnchor)
		s.explicit = False

	def clone(s):
		return BoxAnchorExplicitPattern(s.target, s.anchor, s.explicit)

	def augmentArguments(s, args: list, kwargs: dict):
		kwargs["explicit"] = s.explicit
		usability.BoxAnchorPattern.augmentArguments(s, args, kwargs)

	def consumePrefix(s, attr):
		sym = attr[:1]
		if sym == "e":
			if s.explicit: raise AttributeError("duplicate explicit setting")
			s.explicit = True
			return 1
		return usability.BoxAnchorPattern.consumePrefix(s, attr)


cuboid = usability.BoxAnchorPattern(PrimitiveFactory(CuboidPrimitive))
sphere = usability.BoxAnchorPattern(PrimitiveFactory(SpherePrimitive))
cylinder = BoxAnchorExplicitPattern(PrimitiveFactory(CylinderPrimitive))
rect = usability.BoxAnchorPattern(PrimitiveFactory(RectPrimitive))
circle = BoxAnchorExplicitPattern(PrimitiveFactory(CirclePrimitive))
