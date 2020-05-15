from .. import dag
from .. import usability
from .. import transform
from ..math import *


def processRoundingData(s, roundingLevel, r, maxRoundingLevel, segments=32):

	if roundingLevel < 0 or roundingLevel > maxRoundingLevel or not isinstance(
	  roundingLevel, int):
		raise ValueError("invalid rounding level")
	if roundingLevel > 0 and r is None:
		raise ValueError("missing rounding radius")
	elif roundingLevel == 0 and r is not None:
		raise ValueError("missing rounding level")

	s.roundingLevel = roundingLevel
	s.roundingRadius = r
	s.roundingSegments = segments


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
	def __init__(s,
	             x=None,
	             y=None,
	             z=None,
	             roundingLevel=0,
	             r=None,
	             roundingSegments=32):
		extent = usability.getFlexibleExtent3(x, y, z)

		processRoundingData(s, roundingLevel, r, 2, roundingSegments)

		Primitive3D.__init__(s, extent)


class SpherePrimitive(Primitive3D):
	def __init__(s, r=None, d=None, segments=32):
		s.segments = segments

		r = usability.getFlexibleRadius(r, d)
		extent = V(r, r, r) * 2

		Primitive3D.__init__(s, extent)


class CylinderPrimitive(Primitive3D):
	def __init__(s,
	             r=None,
	             h=None,
	             d=None,
	             segments=32,
	             explicit=False,
	             roundingLevel=0,
	             r2=None,
	             roundingSegments=32):
		s.segments = segments
		s.explicit = explicit

		if h is None: raise ValueError("missing height")
		r = usability.getFlexibleRadius(r, d)
		extent = V(r * 2, r * 2, h)

		processRoundingData(s, roundingLevel, r2, 2 if explicit else 1,
		                    roundingSegments)

		Primitive3D.__init__(s, extent)


class RectPrimitive(Primitive2D):
	def __init__(s, x=None, y=None, roundingLevel=0, r=None):
		extent = usability.getFlexibleExtent2(x, y)

		processRoundingData(s, roundingLevel, r, 1)
		Primitive2D.__init__(s, extent)


class CirclePrimitive(Primitive2D):
	def __init__(s,
	             r=None,
	             d=None,
	             segments=32,
	             explicit=False,
	             roundingLevel=0,
	             r2=None,
	             roundingSegments=32):
		s.segments = segments
		s.explicit = explicit

		r = usability.getFlexibleRadius(r, d)
		extent = V(r, r, 0) * 2

		processRoundingData(s, roundingLevel, r2, 1 if explicit else 0,
		                    roundingSegments)

		Primitive2D.__init__(s, extent)


class polygon(Primitive2D):
	def __init__(s, points, *args):
		if len(args) > 0:
			s.points = list()
			s.points.append(V(points[0], points[1]))
			for p in args:
				s.points.append(V(p[0], p[1]))
		else:
			s.points = list(V(p[0], p[1]) for p in points)

		xmax = max(p.x for p in s.points)
		ymax = max(p.y for p in s.points)
		Primitive2D.__init__(s, V(xmax, ymax, 0))


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
		s.explicit = explicit

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


class RoundedBoxAnchorPattern(usability.BoxAnchorPattern):
	def __init__(s, target, defaultAnchor=V(0, 0, 0), roundingLevel=0):
		usability.BoxAnchorPattern.__init__(s, target, defaultAnchor)
		s.roundingLevel = roundingLevel

	def clone(s):
		return RoundedBoxAnchorPattern(s.target, s.anchor, s.roundingLevel)

	def augmentArguments(s, args: list, kwargs: dict):
		kwargs["roundingLevel"] = s.roundingLevel
		usability.BoxAnchorPattern.augmentArguments(s, args, kwargs)

	def consumePrefix(s, attr):
		sym = attr[:1]
		if sym == "r":
			s.roundingLevel += 1
			return 1
		return usability.BoxAnchorPattern.consumePrefix(s, attr)


class RoundedBoxAnchorExplicitPattern(usability.BoxAnchorPattern):
	def __init__(s,
	             target,
	             defaultAnchor=V(0, 0, 0),
	             roundingLevel=0,
	             explicit=False):
		usability.BoxAnchorPattern.__init__(s, target, defaultAnchor)
		s.explicit = explicit
		s.roundingLevel = roundingLevel

	def clone(s):
		return RoundedBoxAnchorExplicitPattern(s.target, s.anchor, s.roundingLevel,
		                                       s.explicit)

	def augmentArguments(s, args: list, kwargs: dict):
		kwargs["explicit"] = s.explicit
		kwargs["roundingLevel"] = s.roundingLevel
		usability.BoxAnchorPattern.augmentArguments(s, args, kwargs)

	def consumePrefix(s, attr):
		sym = attr[:1]
		if sym == "e":
			if s.explicit: raise AttributeError("duplicate explicit setting")
			s.explicit = True
			return 1
		elif sym == "r":
			s.roundingLevel += 1
			return 1
		return usability.BoxAnchorPattern.consumePrefix(s, attr)


cuboid = RoundedBoxAnchorPattern(PrimitiveFactory(CuboidPrimitive))
sphere = usability.BoxAnchorPattern(PrimitiveFactory(SpherePrimitive))
cylinder = RoundedBoxAnchorExplicitPattern(PrimitiveFactory(CylinderPrimitive))
rect = RoundedBoxAnchorPattern(PrimitiveFactory(RectPrimitive))
circle = RoundedBoxAnchorExplicitPattern(PrimitiveFactory(CirclePrimitive))
