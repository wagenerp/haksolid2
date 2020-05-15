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
	def __init__(s, layerFilter: metadata.LayerFilter = None):
		s.code = ""
		s.transformStack = list()
		s.transformStack.append(M())
		s.absTransform = M()
		s.layerFilter = layerFilter

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
			if node.roundingLevel == 0:
				s.addLeaf(f"cube({scad_repr(node.extent)},true)")
			elif node.roundingLevel == 1:
				code = (
				  f"linear_extrude(height={scad_repr(node.extent.z)},center=true) hull() {{"
				)

				dx = node.extent.x * 0.5 - node.roundingRadius
				dy = node.extent.y * 0.5 - node.roundingRadius
				for x in (-1, 1):
					for y in (-1, 1):
						code += (
						  f"translate([{scad_repr(x*dx)},{scad_repr(y*dy)}]) circle(r={scad_repr(node.roundingRadius)},$fn={scad_repr(node.roundingSegments)});"
						)

				code += "}"
				s.addLeaf(code)

			elif node.roundingLevel == 2:
				code = (f"hull() {{")

				dx = node.extent.x * 0.5 - node.roundingRadius
				dy = node.extent.y * 0.5 - node.roundingRadius
				dz = node.extent.z * 0.5 - node.roundingRadius
				for x in (-1, 1):
					for y in (-1, 1):
						for z in (-1, 1):
							code += f"""
							  translate([
									{scad_repr(x*dx)},{scad_repr(y*dy)},{scad_repr(z*dz)}]) 
									sphere(
										r={scad_repr(node.roundingRadius)},
										$fn={scad_repr(node.roundingSegments)});
								"""

				code += "}"
				s.addLeaf(code)
				pass

		elif isinstance(node, primitives.SpherePrimitive):
			s.addLeaf(
			  f"sphere({scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})")
		elif isinstance(node, primitives.CylinderPrimitive):
			if node.roundingLevel == 0:
				s.addLeaf(
				  f"cylinder(d={scad_repr(node.extent.x)},h={scad_repr(node.extent.z)},$fn={scad_repr(node.segments)},center=true)"
				)
			elif node.roundingLevel == 1:
				x1 = node.extent.x * 0.5 - node.roundingRadius
				code = f"""
				  rotate_extrude($fn={scad_repr(node.segments)}) 
						translate([0,{scad_repr(-node.extent.z*0.5)}]) 
							hull() {{
								square([0.01,{scad_repr(node.extent.z)}]);
								translate([{scad_repr(x1)},{scad_repr(node.roundingRadius)}])
									circle(
										r={scad_repr(node.roundingRadius)},
										$fn={scad_repr(node.roundingSegments)});
								translate([
									{scad_repr(x1)},
									{scad_repr(node.extent.z-node.roundingRadius)}]) 
									circle(
										r={scad_repr(node.roundingRadius)},
										$fn={scad_repr(node.roundingSegments)});
							}}
					"""
				s.addLeaf(code)
			elif node.roundingLevel == 2:
				ida = 360 / node.segments
				r = node.extent.x * 0.5 - node.roundingRadius / cos(pi / node.segments)
				code = "hull() {"
				z = node.extent.z * 0.5 - node.roundingRadius
				for z in (-z, z):
					for i in range(node.segments):
						code += f"""
							translate({scad_repr(V.Cylinder(i*ida,r,z))}) 
								sphere(r={node.roundingRadius},$fn={node.roundingSegments});"""
				code += "}"
				s.addLeaf(code)
		elif isinstance(node, primitives.RectPrimitive):
			if node.roundingLevel == 0:
				s.addLeaf(f"square({scad_repr(node.extent.xy)},true)")
			elif node.roundingLevel == 1:
				code = (f"hull() {{")

				dx = node.extent.x * 0.5 - node.roundingRadius
				dy = node.extent.y * 0.5 - node.roundingRadius
				for x in (-1, 1):
					for y in (-1, 1):
						code += (
						  f"translate([{scad_repr(x*dx)},{scad_repr(y*dy)}]) circle(r={scad_repr(node.roundingRadius)},$fn={scad_repr(node.roundingSegments)});"
						)

				code += "}"
				s.addLeaf(code)

		elif isinstance(node, primitives.CirclePrimitive):
			if node.roundingLevel == 0:
				s.addLeaf(
				  f"circle(d={scad_repr(node.extent.x)},$fn={scad_repr(node.segments)})"
				)
			elif node.roundingLevel == 1:
				ida = 360 / node.segments
				r = node.extent.x * 0.5 - node.roundingRadius / cos(pi / node.segments)
				code = "hull() {"
				for i in range(node.segments):
					code += f"""
						translate({scad_repr(V.Cylinder(i*ida,r))}) 
							circle(r={node.roundingRadius},$fn={node.roundingSegments});"""
				code += "}"
				s.addLeaf(code)
		
		elif isinstance(node, primitives.polygon):
			s.addLeaf(f"polygon(points={scad_repr(node.points)})")

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
		elif isinstance(node, operations.Hull):
			s.addNode(f"hull()")

		elif isinstance(node, operations.LinearExtrude):
			s.addLeaf(f"linear_extrude(height={scad_repr(node.amount)},center=true)")
			s.absTransform=M()
		elif isinstance(node, operations.rotate_extrude):
			s.addLeaf(f"rotate_extrude()")
			s.absTransform=M()
		elif isinstance(node, operations.MatrixExtrusionNode):
			s.addLeaf(f"union()")
			s.code+="{"
			s.absTransform=M()

			children_code="union() {"
			for child in node.children:
				sub=OpenSCADcodeGen(layerFilter=s.layerFilter)
				child.visitDescendants(sub)
				children_code+=sub.code
				

			children_code+="}"


			T0=None
			for T1 in node.matrices():
				if T0 is not None:
					s.code+=f"""
						hull() {{ 
							multmatrix({scad_repr(T0)}) 
								linear_extrude(height=1e-99,center=true) {children_code};
							multmatrix({scad_repr(T1)}) 
								linear_extrude(height=1e-99,center=true) {children_code};
						}}"""
					
				T0=T1
			s.code +="}"
			return False

		elif isinstance(node, metadata.color):
			color = list(node.getColor()) + [node.alpha]
			s.addNode(f"color({scad_repr(color)})")

		elif isinstance(node, metadata.DAGLayer):
			if s.layerFilter is None or not s.layerFilter(node): return False
			color = list(node.color) + [node.alpha]
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
		s.transformStack.pop()
		s.absTransform = s.transformStack[-1]
		s.code += "};"
