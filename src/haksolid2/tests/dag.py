from ..dag import *
import unittest
import sys


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


class DAGTest(unittest.TestCase):
	def test_direct(self):
		root = TestNode("root")

		foo = root * TestNode("expr-level1") * TestNode("expr-level2")

		with root * TestNode(4):
			~TestNode(2)
			~TestNode(3)

			nontree = ~TestNode("non-tree")

			with nontree:
				~TestNode("non-tree leaf")

		with root:
			~TestNode(5)

		with foo:
			~TestNode(7)
			nontree()

		with foo * TestNode(8):
			~TestNode(9)

		visitor = PrintVisitor()
		root.visitDescendants(visitor)
		self.assertEqual(
		  visitor.output,
		  'TestNode(root)\n  TestNode(expr-level1)\n    TestNode(expr-level2)\n      TestNode(7)\n      TestNode(non-tree)\n        TestNode(non-tree leaf)\n      TestNode(8)\n        TestNode(9)\n  TestNode(4)\n    TestNode(2)\n    TestNode(3)\n    TestNode(non-tree)\n      TestNode(non-tree leaf)\n  TestNode(5)\n'
		)

	def test_module(self):
		@DAGModule
		def mymodule():
			~TestNode("mymodule-1")
			with ~TestNode("mymodule-2"):
				~DAGAnchor()
			~DAGAnchor()

		root = TestNode("root")

		with root * mymodule():
			~TestNode("leaf")

		with root * mymodule() * TestNode("intermediate"):
			~TestNode("leaf2")

		visitor = PrintVisitor()
		root.visitDescendants(visitor)

		self.assertEqual(
		  visitor.output,
		  'TestNode(root)\n  DAGGroup\n    TestNode(mymodule-1)\n    TestNode(mymodule-2)\n      TestNode(leaf)\n    TestNode(leaf)\n  DAGGroup\n    TestNode(mymodule-1)\n    TestNode(mymodule-2)\n      TestNode(intermediate)\n        TestNode(leaf2)\n    TestNode(intermediate)\n      TestNode(leaf2)\n'
		)
