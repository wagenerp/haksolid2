from .. import dag
from .. import usability
from .. import transform
from .. import primitives
from ..math import *


class ExtrusionNode(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)


class LinearExtrude(ExtrusionNode):
	def __init__(s, amount):
		ExtrusionNode.__init__(s)
		s.amount = amount

	def __str__(s):
		return f"{s.__class__.__name__}({s.amount})"


class rotate_extrude(ExtrusionNode):
	def __init__(s):
		ExtrusionNode.__init__(s)


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


class path_extrude(MatrixExtrusionNode):
	def __init__(s, path, protrusion=None):
		MatrixExtrusionNode.__init__(s)

		s._path = path
		s._protrusion = protrusion

	def augment(s, iterator):
		first = True
		m0 = None
		for m in iterator:
			if m is None:
				if not first and s._protrusion is not None: # protrude out the end
					yield M.Translation(m0.col3.xyz.normal * s._protrusion) @ m0
				first = True
				yield m
				continue
			if first:
				first = False
				if s._protrusion is not None:
					yield M.Translation((-s._protrusion) * m.col3.xyz.normal) @ m
			yield m
			m0 = m

		if not first and s._protrusion is not None: # protrude out the end
			yield M.Translation(m0.col3.xyz.normal * s._protrusion) @ m0

	def matrices(s):
		yield from s.augment(s._path.generate())


class CylinderOffsetFactory:
	def __init__(s, primitive):
		s.primitive = primitive

	def __call__(s, anchor, *args, **kwargs):
		node = s.primitive(*args, *kwargs)
		return transform.translate(z=-0.5 * node.amount * anchor) * node


linear_extrude = usability.CylinderAnchorPattern(
  CylinderOffsetFactory(LinearExtrude))
