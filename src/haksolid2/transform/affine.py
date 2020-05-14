from .. import dag
from ..math import *
from .. import usability


class AffineTransform(dag.DAGNode):
	def __init__(s, matrix: M):
		dag.DAGNode.__init__(s)
		s.matrix = matrix

	def __str__(s):
		return "AffineTransform(%s)" % str(s.matrix).replace('\n', ', ')


def translate(x=0, y=0, z=0):
	if isinstance(x, Iterable):
		return AffineTransform(M.Translation(x))
	else:
		return AffineTransform(M.Translation((x, y, z)))


def scale(X=1, Y=1, Z=1):
	if isinstance(X, Iterable):
		return AffineTransform(M.Scale(X))
	else:
		return AffineTransform(M.Scale((X, Y, Z)))


def rotate(a=0, b=0, c=0):

	if isinstance(a, Iterable):
		return AffineTransform(M.Rotation(a))
	else:
		return AffineTransform(M.Rotation((a, b, c)))


def affine(p=None, ex=None, ey=None, ez=None, angs=None):
	return AffineTransform(M.Transform(p, ex, ey, ez, angs))


def mirror(x=None, y=None, z=None):

	axis = usability.getFlexibleAxis3(x, y, z)

	return AffineTransform(M.Reflection(axis))


def matrix(m: M):
	return AffineTransform(m)


class untransform(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)

	def __str__(s):
		return "untransform"
