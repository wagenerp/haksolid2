from .. import dag
from ..math import *
from .. import usability
from .. import metadata


class DAGLayer(dag.DAGGroup):
	color = V(1, 1, 1)
	alpha = 1

	def __init__(s):
		dag.DAGGroup.__init__(s)

	def ident(s):
		def cts(v):
			return "%.2x" % (min(255, max(0, int(v * 255))))

		return f"{s.__class__.__name__}_{cts(s.color.x)}{cts(s.color.y)}{cts(s.color.z)}{cts(s.alpha)}"

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
		s.classes = tuple(classes)

	def __call__(s, layer: DAGLayer):
		return isinstance(layer, s.classes)


class LayersVisitor(usability.TransformVisitor):
	def __init__(s, shallow):
		usability.TransformVisitor.__init__(s)
		s.layers = list()
		s.shallow = shallow

	def __call__(s, node):
		usability.TransformVisitor.__call__(s, node)

		if isinstance(node, metadata.DAGLayer):
			s.layers.append((M(s.absTransform), node))
			if s.shallow: return False