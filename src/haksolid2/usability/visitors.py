from .. import dag
from .. import metadata
from .. import transform
from ..math import *


class PrintVisitor(dag.DAGVisitor):
	def __init__(s):
		dag.DAGVisitor.__init__(s)
		s.depth = 0
		s.output = ""

	def __call__(s, node):
		s.output += ("  " * s.depth + str(node) + "\n")

	def descent(s):
		s.depth += 1

	def ascend(s):
		s.depth -= 1


class TransformVisitor(dag.DAGVisitor):
	def __init__(s):
		dag.DAGVisitor.__init__(s)
		s.transformStack = list()
		s.transformStack.append(M())
		s.absTransform = M()

	def __call__(s, node):
		if isinstance(node, transform.AffineTransform):
			s.absTransform = s.transformStack[-1] @ node.matrix
		elif isinstance(node, transform.untransform):
			s.absTransform = M()

	def descent(s):
		s.transformStack.append(M(s.absTransform))

	def ascend(s):
		s.transformStack.pop()
		s.absTransform = s.transformStack[-1]


class LayersVisitor(TransformVisitor):
	def __init__(s, shallow):
		TransformVisitor.__init__(s)
		s.layers = list()
		s.shallow = shallow

	def __call__(s, node):
		TransformVisitor.__call__(s, node)

		if isinstance(node, metadata.DAGLayer):
			s.layers.append((M(s.absTransform), node))
			if s.shallow: return False