from .. import dag
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


class AllAbsTransformsVisitor(dag.DAGVisitor):
	def __init__(s):
		s.absTransforms = list()
		s.transformStack = list()
		s.transformStack.append(M())
		s.absTransform = M()
		s.isRoot = False

	def __call__(s, node):
		s.isRoot = False
		if isinstance(node, transform.AffineTransform):
			s.absTransform = node.matrix @ s.transformStack[-1]
		elif isinstance(node, transform.untransform):
			s.absTransforms.append(s.absTransform)
			return False

	def descent(s):
		s.transformStack.append(M(s.absTransform))
		s.isRoot = True

	def ascend(s):
		if s.isRoot:
			s.absTransforms.append(s.absTransform)
		s.transformStack.pop()
		s.absTransform = s.transformStack[-1]
		s.isRoot = False