from ..dag import *
from .. import operations
from .common import *
import unittest
import sys


class OperationsTest(unittest.TestCase):
	def test_emplacement(self):

		root = TestNode("root")

		with root:
			with ~TestNode(0):
				~TestNode(1)
				with operations.difference.emplace():
					~TestNode(2)
				~TestNode(3)

			with ~TestNode(10):
				~TestNode(11)
				with operations.intersection.emplace():
					~TestNode(12)
				~TestNode(13)

		visitor = PrintVisitor()
		root.visitDescendants(visitor)
		self.assertEqual(
		  visitor.output,
		  'TestNode(root)\n  difference\n    TestNode(0)\n      TestNode(1)\n      TestNode(3)\n    DAGGroup\n      TestNode(2)\n  intersection\n    TestNode(10)\n      TestNode(11)\n      TestNode(13)\n    DAGGroup\n      TestNode(12)\n'
		)
