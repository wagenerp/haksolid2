from .. import dag
from ..math import *


class DAGLayer(dag.DAGGroup):
	color = V(1, 1, 1)
	alpha = 1

	def __init__(s):
		dag.DAGGroup.__init__(s)
	
	def __str__(s):
		return f"{s.__class__.__name__}({s.color} {s.alpha*100}%)"


class previewLayer(DAGLayer):
	color = V(0.2, 0.8, 0.5)
	alpha = 0.4


class nonpreviewLayer(DAGLayer):
	pass

class SubprocessLayer(DAGLayer):
	pass

class LayerFilter:
	def __call__(s, layer: DAGLayer):
		raise NotImplementedError()


class AllLayerFilter(LayerFilter):
	def __call__(s, layer: DAGLayer):
		return True


class NoLayerFilter(LayerFilter):
	def __call__(s, layer: DAGLayer):
		return False


class ClassLayerFilter(LayerFilter):
	def __init__(s, *classes):
		s.classes = set(classes)

	def __call__(s, layer: DAGLayer):
		return layer.__class__ in s.classes
