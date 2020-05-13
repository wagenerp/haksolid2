from .. import dag, errors
from .. import transform, primitives, operations, metadata
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

	def __call__(s, node):
		if isinstance(node, transform.AffineTransform):
			s.code += f"multmatrix({scad_repr(node.matrix)})"

		elif isinstance(node, primitives.CuboidPrimitive):
			s.code += f"cube({scad_repr(node.extent)},true)"
		elif isinstance(node, primitives.SpherePrimitive):
			s.code += f"sphere({scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})"
		elif isinstance(node, primitives.CylinderPrimitive):
			s.code += f"cylinder(d={scad_repr(node.extent.x)},h={scad_repr(node.extent.z)},$fn={scad_repr(node.segments)},center=true)"
		elif isinstance(node, primitives.RectPrimitive):
			s.code += f"square({scad_repr(node.extent)},true)"
		elif isinstance(node, primitives.CirclePrimitive):
			s.code += f"circle({scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})"

		elif isinstance(node, operations.difference):
			s.code += f"difference()"
		elif isinstance(node, operations.intersection):
			s.code += f"intersection()"
		elif isinstance(node, operations.minkowski):
			s.code += f"minkowski()"
		elif isinstance(node, operations.offset):
			if node.round:
				s.code += f"offset(r={scad_repr(node.offset)})"
			else:
				s.code += f"offset(delta={scad_repr(node.offset)})"

		elif isinstance(node, operations.LinearExtrude):
			s.code += f"linear_extrude(height={scad_repr(node.amount)},center=true)"
		elif isinstance(node, operations.rotate_extrude):
			s.code += f"rotate_extrude()"
		
		elif isinstance(node, metadata.color):
			color=list(node.getColor())+[node.alpha]
			s.code+=f"color({scad_repr(color)})"

		elif isinstance(node, dag.DAGGroup):
			s.code += "union()"
		else:
			warnings.warn(
			  errors.UnsupportedFeatureWarning(f"OpenSCAD cannot handle {node}"))
			return False

	def descent(s):
		s.code += "{"

	def ascend(s):
		s.code += "}"
