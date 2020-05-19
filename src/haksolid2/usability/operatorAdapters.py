from .. import dag
from .. import operations


class OperationsAdapter:
	def __add__(a, b):
		res = dag.DAGGroup()
		res * a
		res * b
		return res

	def __sub__(a, b):
		res = operations.difference()
		res * a
		res * b
		return res

	def __mod__(a, b):
		res = operations.intersection()
		res * a
		res * b
		return res

	def __matmul__(a, b):
		res = operations.hull()
		res * a
		res * b
		return res

	def __pow__(a, b):
		res = operations.minkowski()
		res * a
		res * b
		return res


dag.DAGBase.Adapters.append(OperationsAdapter)