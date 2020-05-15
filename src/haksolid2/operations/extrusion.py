from .. import dag
from .. import usability
from .. import transform
from ..math import *


class ExtrusionNode(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)


class LinearExtrude(ExtrusionNode):
	def __init__(s, amount):
		ExtrusionNode.__init__(s)
		s.amount = amount


class rotate_extrude(ExtrusionNode):
	def __init__(s, amount):
		ExtrusionNode.__init__(s)
		s.amount = amount


class MatrixExtrusionNode(ExtrusionNode):
	def __init__(s):
		ExtrusionNode.__init__(s)

	def matrices(s):
		raise NotImplementedError()
		if False:
			yield None


class matrix_extrude(MatrixExtrusionNode):
	def __init__(s, matrix, steps=1, offset=None):
		MatrixExtrusionNode.__init__(s)
		if offset is None:
			offset = M()

		s._matrix = matrix
		s._steps = steps
		s._offset = offset

	def matrices(s):
		T = s._offset

		for step in range(s._steps):
			yield T
			T = s._matrix @ T
		yield T


class CylinderOffsetFactory:
	def __init__(s, primitive):
		s.primitive = primitive

	def __call__(s, anchor, *args, **kwargs):
		node = s.primitive(*args, *kwargs)
		return transform.translate(z=-0.5 * node.amount * anchor) * node


linear_extrude = usability.CylinderAnchorPattern(
  CylinderOffsetFactory(LinearExtrude))
