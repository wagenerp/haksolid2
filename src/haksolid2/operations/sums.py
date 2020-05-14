from . import base
from .. import dag
from .. import usability


class SumOperation(base.DAGOperation):
	def __init__(s):
		base.DAGOperation.__init__(s)


class minkowski(SumOperation):
	pass


class offset(SumOperation):
	def __init__(s, offset, round=True):
		SumOperation.__init__(s)
		s.offset = offset
		s.round = round


class Hull(SumOperation):
	pass


hull = usability.OptionalConditionalNode(Hull, dag.DAGGroup)
