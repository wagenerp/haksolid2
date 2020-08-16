from .. import dag, errors
from .. import transform, primitives, operations, metadata, processing, paradigms, usability
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
	elif isinstance(data, (sympy.core.Expr, sympy.core.relational.Relational)):
		return str(data)
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


class OpenSCADcodeGen(usability.TransformVisitor):
	def __init__(s,
	             layerFilter: metadata.LayerFilter = None,
	             processPreview=False,
	             useSegmentCount=True):
		usability.TransformVisitor.__init__(s)
		s.code = ""
		s.variables = dict()
		s.variable_list = list()

		s.layerFilter = layerFilter
		s.processPreview = processPreview
		s.useSegmentCount = useSegmentCount

	def clone(s):
		return OpenSCADcodeGen(s.layerFilter, s.processPreview, s.useSegmentCount)

	def addNode(s, code):
		s.code += code

	def addLeaf(s, code):
		s.code += f"multmatrix({scad_repr(s.transformStack[-1])}) {code}"
		s.absTransform = M()

	def segmentCode(s, node, n=None, first=False):
		if n is None: return ""
		if (hasattr(node, "explicit") and
		    getattr(node, "explicit")) or s.useSegmentCount:
			if first:
				return f"$fn={scad_repr(n)}"
			else:
				return f",$fn={scad_repr(n)}"
		return ""

	def __call__(s, node):
		usability.TransformVisitor.__call__(s, node)
		if isinstance(node, transform.AffineTransform):
			s.addNode("union()")
		elif isinstance(node, transform.untransform):
			s.addNode("union()")
		elif isinstance(node, transform.retransform):
			allabs = usability.AllAbsTransformsVisitor()
			node.subject.visitAncestors(allabs)
			sub = s.clone()
			node.subject.visitDescendants(sub)
			s.code += "{"
			for T in allabs.absTransforms:
				s.code += f"multmatrix({scad_repr(T)}) {{ {sub.code} }}"
			s.code += "}"

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
						code += f"""
						  translate([{scad_repr(x*dx)},{scad_repr(y*dy)}]) 
								circle(
									r={scad_repr(node.roundingRadius)}
									{s.segmentCode(node,node.roundingSegments)});"""

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
										r={scad_repr(node.roundingRadius)}
										{s.segmentCode(node,node.roundingSegments)});
								"""

				code += "}"
				s.addLeaf(code)
				pass

		elif isinstance(node, primitives.SpherePrimitive):
			s.addLeaf(
			  f"sphere(d={scad_repr(node.extent.x)}{s.segmentCode(node,node.segments)})"
			)
		elif isinstance(node, primitives.CylinderPrimitive):
			if node.roundingLevel == 0:
				s.addLeaf(f"""
				  cylinder(
						r1={scad_repr(node.r0)},
						r2={scad_repr(node.r1)},
						h={scad_repr(node.extent.z)}
						{s.segmentCode(node,node.segments)}
						,center=true)""")
			elif node.roundingLevel == 1:
				r0, r1, R, h = node.r0, node.r1, node.roundingRadius, node.extent.z
				code = f"""
				  rotate_extrude({s.segmentCode(node,first=True)}) 
						translate([0,{scad_repr(-h*0.5)}]) 
							hull() {{
								square([0.01,{scad_repr(h)}]);
								translate([{scad_repr(r0-R + (r1-r0)/h*R)},{scad_repr(R)}])
									circle(
										r={scad_repr(R)}
										{s.segmentCode(node,node.roundingSegments)});
								translate([
									{scad_repr(r1-R + (r0-r1)/h*R)},
									{scad_repr(h-R)}]) 
									circle(
										r={scad_repr(R)}
										{s.segmentCode(node,node.roundingSegments)});
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
								sphere(r={node.roundingRadius}{s.segmentCode(node,node.roundingSegments)});"""
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
						  f"translate([{scad_repr(x*dx)},{scad_repr(y*dy)}]) circle(r={scad_repr(node.roundingRadius)}{s.segmentCode(node,node.roundingSegments)});"
						)

				code += "}"
				s.addLeaf(code)

		elif isinstance(node, primitives.CirclePrimitive):
			if node.roundingLevel == 0:
				s.addLeaf(
				  f"circle(d={scad_repr(node.extent.x)}{s.segmentCode(node,node.segments)})"
				)
			elif node.roundingLevel == 1:
				ida = 360 / node.segments
				r = node.extent.x * 0.5 - node.roundingRadius / cos(pi / node.segments)
				code = "hull() {"
				for i in range(node.segments):
					code += f"""
						translate({scad_repr(V.Cylinder(i*ida,r))}) 
							circle(
								r={node.roundingRadius}
								{s.segmentCode(node,node.roundingSegments)});"""
				code += "}"
				s.addLeaf(code)

		elif isinstance(node, primitives.polygon):
			s.addLeaf(f"polygon(points={scad_repr(node.points)})")

		elif isinstance(node, primitives.text):
			code = f"text({scad_repr(node.text)}"
			for k in ("size", "font", "halign", "valign", "spacing", "direction"):
				v = getattr(node, k)
				if v is not None:
					code += f",{k}={scad_repr(v)}"
			if node.segments is not None:
				code += f",$fn={scad_repr(node.segments)}"
			code += ")"
			s.addLeaf(code)

		elif isinstance(node, operations.difference):
			s.addNode(f"difference()")
		elif isinstance(node, operations.intersection):
			if node.skipIfEmpty:
				n_nonempty = 0
				for child in node.children:
					v = metadata.DimensionVisitor()
					child.visitDescendants(v)
					if not v.empty:
						n_nonempty += 1
						if n_nonempty > 1:
							break
				if n_nonempty < 2: return False
			s.addNode(f"intersection()")

		elif isinstance(node, operations.minkowski):
			s.addNode(f"minkowski()")
		elif isinstance(node, operations.offset):
			if node.round:
				s.addNode(
				  f"offset(r={scad_repr(node.offset)}{s.segmentCode(node,node.segments)})"
				)
			else:
				s.addNode(f"offset(delta={scad_repr(node.offset)})")
		elif isinstance(node, operations.Hull):
			s.addNode(f"hull()")

		elif isinstance(node, operations.LinearExtrude):
			s.addLeaf(f"linear_extrude(height={scad_repr(node.amount)},center=true)")
		elif isinstance(node, operations.rotate_extrude):
			s.addLeaf(
			  f"rotate_extrude({s.segmentCode(node,node.segments,first=True)})")
		elif isinstance(node, operations.MatrixExtrusionNode):
			s.addLeaf(f"union()")
			s.code += "{"

			children_code = "union() {"
			for child in node.children:
				sub = OpenSCADcodeGen(layerFilter=s.layerFilter)
				child.visitDescendants(sub)
				children_code += sub.code

			children_code += "}"

			T0 = None
			for T1 in node.matrices():
				if T0 is not None:
					s.code += f"""
						hull() {{ 
							multmatrix({scad_repr(T0)}) 
								linear_extrude(height=1e-99,center=true) {children_code};
							multmatrix({scad_repr(T1)}) 
								linear_extrude(height=1e-99,center=true) {children_code};
						}}"""

				T0 = T1
			s.code += "}"
			return False

		elif isinstance(node, operations.slicePlane):
			s.addLeaf("projection(cut=true)")
		elif isinstance(node, operations.projection):
			s.addLeaf("projection(cut=false)")

		elif isinstance(node, metadata.color):
			color = list(node.getColor()) + [node.alpha]
			s.addNode(f"color({scad_repr(color)})")

		elif isinstance(node, metadata.DAGLayer):
			if (len(s.transformStack) > 1 and
			    (s.layerFilter is None or not s.layerFilter(node))):
				return False
			color = list(node.color) + [node.alpha]
			s.addNode(f"color({scad_repr(color)})")

		elif s.processPreview and isinstance(node, processing.EntityNode):
			if isinstance(node.process, paradigms.lasercut.LasercutProcess):
				layers = metadata.LayersVisitor(shallow=True)
				node.visitDescendants(layers)

				holes = ""

				for T, child in layers.layers:
					if not isinstance(child, paradigms.lasercut.LasercutLayer): continue
					sub = OpenSCADcodeGen(layerFilter=metadata.ClassLayerFilter(
					  paradigms.lasercut.LasercutLayer))
					child.visitDescendants(sub)
					layer_code = None
					if child.mode == paradigms.lasercut.LasercutLayer.TraceContour:
						layer_code = f"""
							difference() {{ 
								offset(delta=0.25) {{ {sub.code}}} 
								offset(delta=-0.25) {{ {sub.code}}} }}"""

						pass
					elif child.mode == paradigms.lasercut.LasercutLayer.FillZigZag:
						layer_code = sub.code
					if layer_code is not None:
						depth = child.depth
						if depth == node.process.thickness: depth += 1e-1
						layer_code = f"""
							color([1,0.2,1,0.5])
							multmatrix({scad_repr(s.absTransform @ T)})
								translate([0,0,{scad_repr(-depth)}])
									linear_extrude(height={scad_repr(depth+1e-1)}) {{{layer_code}}}"""
						holes += layer_code

				sub = OpenSCADcodeGen(layerFilter=s.layerFilter)
				node.visitDescendants(sub)

				s.code += f""" multmatrix({scad_repr(s.absTransform)})  {{
					difference() {{
						translate([0,0,{scad_repr(-node.process.thickness)}]) 
							linear_extrude(height={scad_repr(node.process.thickness)}) {{ 
								{sub.code} }} 
						color([1,1,1,1]) union() {{ {holes} }} }}
						{holes} }}"""
				return False
			else:
				s.addNode("union()")
		elif isinstance(node, dag.DAGGroup):
			s.addNode("union()")
		elif isinstance(node, metadata.variable):
			if node.ident not in s.variables:
				s.variables[node.ident] = node
				s.variable_list.append(node)
			else:
				raise Exception(f"variable redeclared: {node.ident}")

		elif isinstance(node, metadata.conditional):
			s.addNode(f"if ({scad_repr(node.expr)})")
		elif isinstance(node, metadata.runtime_assertion):
			s.addNode(f"assert ({scad_repr(node.expr)},{scad_repr(node.message)})")
		else:
			warnings.warn(
			  errors.UnsupportedFeatureWarning(f"OpenSCAD cannot handle {node}"))
			return False

	def descent(s):
		usability.TransformVisitor.descent(s)
		s.code += "{"

	def ascend(s):
		usability.TransformVisitor.ascend(s)
		s.code += "};"

	def finish(s):
		varcode = str()

		current_group = None

		for _, v in sorted(enumerate(s.variable_list),
		                   key=lambda v: (v[1].group or '', v[0])):
			if v.group != current_group:
				current_group = v.group
				varcode += f"/* [{current_group}] */\n"

			if v.description is not None:
				varcode += "".join(f"// {ln}\n" for ln in v.description.splitlines())

			varcode += f"{v.ident} = {scad_repr(v.default)}; "
			if v.domain is not None:
				varcode += "// " + " ".join(v.domain.splitlines())
			varcode += "\n"

		varcode += "/* [Hidden] */\n"

		for v in s.variable_list:

			if v.isBool:
				varcode += f"{v.symbol} = {v.ident} ? 1 : 0;\n"
			else:
				varcode += f"{v.symbol} = {v.ident};\n"

		s.code = varcode + s.code
