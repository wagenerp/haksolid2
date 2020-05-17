from .. import dag
from .. import primitives, operations


class DimensionVisitor(dag.DAGVisitor):
	def __init__(s):
		dag.DAGVisitor.__init__(s)
		s.has2d = False
		s.has3d = False
		s.has2dTo3d = False
		s.has3dTo2d = False

	def __call__(s, node):
		if isinstance(node, primitives.Primitive2D):
			s.has2d = True
		elif isinstance(node, primitives.Primitive3D):
			s.has3d = True
		elif isinstance(node, operations.ExtrusionNode):
			s.has2dTo3d = True
			s.has3d = True
			return False
		elif isinstance(node, operations.ProjectionNode):
			s.has3dTo2d = True
			s.has2d = True
			return False

	@property
	def empty(s):
		return not (s.has2d or s.has3d)

	@property
	def pure(s):
		return not (s.has2dTo3d or s.has3dTo2d)
