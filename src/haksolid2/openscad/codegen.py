from .. import dag, errors
from .. import transform, primitives, operations, metadata
from ..math import *
import warnings
import numbers
import numpy
import math
from collections import Iterable


def scad_repr(data):
	"""Returns a piece of OpenSCAD code representing a given variable, simmilar to python's 'repr' call. Supports nonetype, boolean, string, numbers and iterables (being translated to list literals)."""
	if data is None:
		return "undef"
	elif data is True:
		return "true"
	elif data is False:
		return "false"
	elif isinstance(data, numbers.Number):
		if math.isnan(data): return "0"
		elif math.isinf(data): return "0"
		if math.isnan(data): return "(0/0)"
		elif math.isinf(data): return "(1e200*1e200)"
		else: return repr(data)
	elif type(data) == str:
		data_enc = "".join(v if v != '"' else '\\"' for v in data)
		return '"%s"' % data
	elif isinstance(data, numpy.ndarray):
		return scad_repr(data.tolist())
	elif isinstance(data, Iterable):
		if len(data) < 1: return "[]"
		return "[%s]" % (",".join(scad_repr(v) for v in data))
	else:
		raise Exception("unexpected data type: %s" % type(data))


class OpenSCADcodeGen(dag.DAGVisitor):
	def __init__(s):
		s.code = ""
		s.transformStack = list()
		s.transformStack.append(M())
		s.absTransform = M()

	def addNode(s, code):
		s.code += code

	def addLeaf(s, code):
		s.code += f"multmatrix({scad_repr(s.transformStack[-1])}) {code}"

	def __call__(s, node):
		if isinstance(node, transform.AffineTransform):
			s.absTransform = s.transformStack[-1] @ node.matrix
			s.addNode("union()")
		elif isinstance(node, transform.untransform):
			s.absTransform = M()
			s.addNode("union()")

		elif isinstance(node, primitives.CuboidPrimitive):
			s.addLeaf(f"cube({scad_repr(node.extent)},true)")
		elif isinstance(node, primitives.SpherePrimitive):
			s.addLeaf(
			  f"sphere({scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})")
		elif isinstance(node, primitives.CylinderPrimitive):
			s.addLeaf(
			  f"cylinder(d={scad_repr(node.extent.x)},h={scad_repr(node.extent.z)},$fn={scad_repr(node.segments)},center=true)"
			)
		elif isinstance(node, primitives.RectPrimitive):
			s.addLeaf(f"square({scad_repr(node.extent)},true)")
		elif isinstance(node, primitives.CirclePrimitive):
			s.addLeaf(
			  f"circle({scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})")

		elif isinstance(node, operations.difference):
			s.addNode(f"difference()")
		elif isinstance(node, operations.intersection):
			s.addNode(f"intersection()")
		elif isinstance(node, operations.minkowski):
			s.addNode(f"minkowski()")
		elif isinstance(node, operations.offset):
			if node.round:
				s.addNode(f"offset(r={scad_repr(node.offset)})")
			else:
				s.addNode(f"offset(delta={scad_repr(node.offset)})")

		elif isinstance(node, operations.LinearExtrude):
			s.addNode(f"linear_extrude(height={scad_repr(node.amount)},center=true)")
		elif isinstance(node, operations.rotate_extrude):
			s.addNode(f"rotate_extrude()")

		elif isinstance(node, metadata.color):
			color = list(node.getColor()) + [node.alpha]
			s.addNode(f"color({scad_repr(color)})")

		elif isinstance(node, dag.DAGGroup):
			s.addNode("union()")
		else:
			warnings.warn(
			  errors.UnsupportedFeatureWarning(f"OpenSCAD cannot handle {node}"))
			return False

	def descent(s):
		s.transformStack.append(M(s.absTransform))
		s.code += "{"

	def ascend(s):
		s.absTransform = s.transformStack.pop()
		s.code += "}"
