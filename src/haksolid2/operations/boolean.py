from .. import dag
from . import base


class CSGOperation(base.DAGOperation):
	def __init__(s):
		base.DAGOperation.__init__(s)

	@classmethod
	def emplace(cls):
		dummy = ~dag.DAGNode()

		if len(dummy.parents) < 1:
			raise dag.DAGTopologyError("emplace formed without parent geometry")

		appendix = dag.DAGGroup()
		appendix.unlink()

		for root in dummy.parents:
			newroot = cls()
			root.emplace(newroot)
			newroot * appendix

		dummy.unlink()
		return appendix


class difference(CSGOperation):
	pass


class intersection(CSGOperation):
	def __init__(s, skipIfEmpty=False):
		CSGOperation.__init__(s)
		s.skipIfEmpty = skipIfEmpty
