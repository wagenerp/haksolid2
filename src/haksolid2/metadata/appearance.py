from .. import dag
from ..math import *
import hashlib


class ColorHashVisitor(dag.DAGVisitor):
	def __init__(s):
		s.hash = hashlib.md5()

	def __call__(s, node):
		s.hash.update(str(node).encode())

	def descent(s):
		s.hash.update(b"{")

	def ascend(s):
		s.hash.update(b"}")

	@property
	def color(s):
		return V((s.hash.digest()[0]) / 512 + 0.5, (s.hash.digest()[1]) / 512 + 0.5,
		         (s.hash.digest()[2]) / 512 + 0.5)


class color(dag.DAGGroup):
	def __init__(s, color=None, a=1.0):

		s._color = color
		s.alpha = a

		dag.DAGGroup.__init__(s)

	def __str__(s):
		if s._color is None:
			return f"color(<hash>,{s.alpha})"
		else:
			return f"color({s._color},{s.alpha})"

	def getColor(s):
		if s._color is not None:
			return s._color

		visitor = ColorHashVisitor()
		s.visitDescendants(visitor)

		return visitor.color
