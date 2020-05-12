from ..dag import *

class TestNode(DAGNode):
	def __init__(s, v):
		s.v = v
		DAGNode.__init__(s)

	def __str__(s):
		return f"TestNode({s.v})"


class PrintVisitor(DAGVisitor):
	def __init__(s):
		s.depth = 0
		s.output = ""

	def __call__(s, node):
		s.output += ("  " * s.depth + str(node) + "\n")

	def descent(s):
		s.depth += 1

	def ascend(s):
		s.depth -= 1
