from . import base
from .. import dag
from .. import usability


class SumOperation(base.DAGOperation):
	def __init__(s):
		base.DAGOperation.__init__(s)


class minkowski(SumOperation):
	pass


class offset(SumOperation):
	def __init__(s, offset, round=True, segments=None):
		SumOperation.__init__(s)
		s.offset = offset
		s.round = round
		s.segments = segments

	def __str__(s):
		return f"offset({s.offset} {'round' if s.round else ''})"


class Hull(SumOperation):
	pass


hull = usability.OptionalConditionalNode(Hull, dag.DAGGroup)
