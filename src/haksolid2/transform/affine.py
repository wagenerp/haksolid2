from .. import dag
from ..math import *
from .. import usability


class AffineTransform(dag.DAGNode):
	def __init__(s, matrix: M):
		dag.DAGNode.__init__(s)
		s.matrix = matrix

	def __str__(s):
		return "AffineTransform(%s)" % str(s.matrix).replace('\n', ', ')


def _translate(x=0, y=0, z=0):
	if isinstance(x, Iterable):
		return AffineTransform(M.Translation(x))
	else:
		return AffineTransform(M.Translation((x, y, z)))


def _scale(X=1, Y=1, Z=1):
	if isinstance(X, Iterable):
		return AffineTransform(M.Scale(X))
	else:
		return AffineTransform(M.Scale((X, Y, Z)))


def _rotate(a=0, b=None, c=None):

	if isinstance(a, Iterable):
		return AffineTransform(M.Rotation(a))
	elif b is None and c is None:
		return AffineTransform(M.Rotation((0,0,a)))
	else:
		return AffineTransform(M.Rotation((a, b or 0, c or 0)))


def _rebase(p=None, ex=None, ey=None, ez=None, angs=None):
	return AffineTransform(M.Transform(p, ex, ey, ez, angs))


def _mirror(x=None, y=None, z=None):

	axis = usability.getFlexibleAxis3(x, y, z)

	return AffineTransform(M.Reflection(axis))


def _matrix(m: M):
	return AffineTransform(m)


class untransform(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)

	def __str__(s):
		return "untransform"


translate = usability.OptionalConditionalNode(_translate, dag.DAGNode)
scale = usability.OptionalConditionalNode(_scale, dag.DAGNode)
rotate = usability.OptionalConditionalNode(_rotate, dag.DAGNode)
rebase = usability.OptionalConditionalNode(_rebase, dag.DAGNode)
mirror = usability.OptionalConditionalNode(_mirror, dag.DAGNode)
matrix = usability.OptionalConditionalNode(_matrix, dag.DAGNode)
