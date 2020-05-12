from .. import dag
from .. import usability
from .. import transform

class ExtrusionNode(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)


class LinearExtrude(ExtrusionNode):
	def __init__(s,zanchor,amount):
		s.zanchor = zanchor
		s.amount = amount

class rotate_extrude(ExtrusionNode):
	def __init__(s,zanchor,amount):
		s.amount = amount



class CylinderOffsetFactory:
	def __init__(s, primitive):
		s.primitive = primitive

	def __call__(s, anchor, *args, **kwargs):
		node = s.primitive(*args, *kwargs)
		return transform.translate(z=-0.5 * node.amount * anchor) * node



linear_extrude = usability.CylinderAnchorPattern(CylinderOffsetFactory(LinearExtrude))
