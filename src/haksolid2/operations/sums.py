from . import base


class SumOperation(base.DAGOperation):
	def __init__(s):
		base.DAGOperation.__init__(s)


class minkowski(SumOperation):
	pass


class offset(SumOperation):
	def __init__(s, offset, round=True):
		s.offset = offset
		s.round = round
