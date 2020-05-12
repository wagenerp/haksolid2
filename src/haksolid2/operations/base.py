from .. import dag


class DAGOperation(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)

	def __str__(s):
		return s.__class__.__name__
