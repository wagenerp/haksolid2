from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import operations
from haksolid2 import transform
from haksolid2 import metadata
from haksolid2 import prefabs
from haksolid2 import processing


class Component:
	def __init__(s, p=V(0, 0), r=0, flipped=False):
		s.position = V(*p)
		s.rotation = r
		s.flipped = flipped

	def build(s, layer, ident: str):
		pass

	@property
	def boundingBox(s) -> (V, V):
		raise NotImplementedError()

	@dag.DAGModule
	def mod_preview(s):
		pass

	@dag.DAGModule
	def mod_cutout(s):
		pass

	@dag.DAGModule
	def mod_addendum(s):
		pass

	@dag.DAGModule
	def mod_cavity(s):
		pass


class ScrewPattern:
	def __init__(s):
		pass

	def build(s, case):
		pass

	@dag.DAGModule
	def mod_lid_profile(s):
		pass

	@dag.DAGModule
	def mod_frame_bottom(s, layer):
		pass

	@dag.DAGModule
	def mod_frame_top(s, layer):
		pass


class HScrewPattern:
	def __init__(s, screw: prefabs.mechanical.screws.Screw, minBacking=2):
		s.offset = V(0, 0)
		s.screw = screw
		s.minBacking = minBacking

	def build(s, case):
		s.r1 = max(s.screw.driver.d_body / 2,
		           s.screw.thread.d_nut / 2) + case.wall_thickness
		s.offset = V(case.size_inner.x / 2 + case.wall_thickness,
		             case.size_inner.y / 2 - s.r1 * 2)
		s.center = case.size_inner / 2

	@dag.DAGModule
	def at_anchors(s):
		~transform.translate(s.center) * transform.mirrorquad(
		) * transform.translate(s.offset) * dag.DAGAnchor()

	@dag.DAGModule
	def mod_lid_profile(s):
		with ~s.at_anchors():

			with ~operations.difference():
				with ~dag.DAGGroup():
					~transform.translate(x=s.r1) * primitives.circle(r=s.r1, segments=180)
					~primitives.rect.nx(s.r1, s.r1 * 4)
				~transform.translate(x=s.r1) * primitives.circle(
				  d=s.screw.thread.d_throughhole + 0.1, segments=180)

				~transform.mirrordup(0, 1, 0) * transform.translate(
				  s.r1, s.r1 * 2) * primitives.circle(r=s.r1, segments=180)

	@dag.DAGModule
	def mod_frame_bottom(s, layer):

		h = s.screw.length - layer.thickness
		# h = max(s.screw.thread.h_nut + s.minBacking, h / 2)
		h = s.screw.thread.h_nut + s.minBacking
		~operations.linear_extrude.p(h) * s.mod_lid_profile()

		with operations.difference.emplace():
			with ~s.at_anchors():

				~transform.translate(s.r1, 0, -h) * s.screw.mod_nut_cavity()

	@dag.DAGModule
	def mod_frame_top(s, layer):

		h = s.screw.length - layer.thickness
		# h = min(h - s.screw.thread.h_nut - s.minBacking, h / 2)
		h = h - (s.screw.thread.h_nut + s.minBacking)

		~operations.linear_extrude.n(h) * s.mod_lid_profile()


class EdgeScrewPattern:
	def __init__(s,
	             screw: prefabs.mechanical.screws.Screw,
	             minBacking=2,
	             locations=list()):
		s.offset = V(0, 0)
		s.screw = screw
		s.minBacking = minBacking
		s.locations = list(locations)
		s.edges = (
		  (V(0, 0), V(0, 0)),
		  (V(0, 0), V(0, 0)),
		  (V(0, 0), V(0, 0)),
		  (V(0, 0), V(0, 0)),
		)

	def build(s, case):
		t = case.wall_thickness
		d = case.size_inner
		s.edges = (
		  (V(d.x / 2, -t), V(1, 0)),
		  (V(d.x + t, d.y / 2), V(0, 1)),
		  (V(d.x / 2, d.y + t), V(-1, 0)),
		  (V(-t, d.y / 2), V(0, -1)),
		)
		s.r1 = max(s.screw.driver.d_body / 2,
		           s.screw.thread.d_nut / 2) + case.wall_thickness
		s.fillet = case.wall_thickness

	@dag.DAGModule
	def at_anchors(s):
		for (e, o) in s.locations:
			p, d = s.edges[e]
			~transform.translate(p + d * o) * transform.rotate(e * 90 -
			                                                   90) * dag.DAGAnchor()

	@dag.DAGModule
	def mod_lid_profile(s):
		with ~s.at_anchors():

			with ~operations.difference():
				with ~dag.DAGGroup():
					~transform.translate(x=s.r1) * primitives.circle(r=s.r1, segments=180)
					~primitives.rect.nx(s.r1, s.r1 * 4)
				~transform.translate(x=s.r1) * primitives.circle(
				  d=s.screw.thread.d_throughhole + 0.1, segments=180)

				~transform.mirrordup(0, 1, 0) * transform.translate(
				  s.r1, s.r1 * 2) * primitives.circle(r=s.r1, segments=180)

	@dag.DAGModule
	def mod_frame_bottom(s, layer):

		h = s.screw.length - layer.thickness
		if layer.binary: h -= layer.thickness
		# h = max(s.screw.thread.h_nut + s.minBacking, h / 2)
		h = s.screw.thread.h_nut + s.minBacking

		~operations.linear_extrude.p(h + s.fillet) * s.mod_lid_profile()

		with operations.difference.emplace():
			with ~s.at_anchors():

				with ~transform.translate(s.fillet, 0, -h - s.fillet):
					~transform.rotate(90, 0, 0) * primitives.cylinder(
					  r=s.fillet, segments=90, h=s.r1 * 4)
					~primitives.cuboid.nx(s.r1 * 4, s.r1 * 4, s.fillet * 2)

				~transform.translate(s.r1, 0, -h) * s.screw.mod_nut_cavity(
				  protrusion=s.fillet)

	@dag.DAGModule
	def mod_frame_top(s, layer):

		h = s.screw.length - layer.thickness
		if layer.binary: h -= layer.thickness
		# h = min(h - s.screw.thread.h_nut - s.minBacking, h / 2)
		h = h - (s.screw.thread.h_nut + s.minBacking)

		~operations.linear_extrude.n(h + s.fillet) * s.mod_lid_profile()

		with operations.difference.emplace():
			with ~s.at_anchors():

				with ~transform.translate(s.fillet, 0, h + s.fillet):
					~transform.rotate(90, 0, 0) * primitives.cylinder(
					  r=s.fillet, segments=90, h=s.r1 * 4)
					~primitives.cuboid.nx(s.r1 * 4, s.r1 * 4, s.fillet * 2)


class Layer:
	def __init__(s, case, thickness, binary):
		s.components = list()
		s.case = case
		s.height_above = 0
		s.height_below = 0
		s.thickness = thickness
		s.binary = binary

	def addComponent(s, c: Component):
		s.components.append(c)
		return c

	def build(s, ident: str):
		s.height_above = 0
		s.height_below = 0

		for i_comp, comp in enumerate(s.components):
			comp.build(s, f"{ident}-comp{i_comp}")
			boxMin, boxMax = comp.boundingBox

			maxz = boxMax.z
			minz = max(0, -boxMin.z - s.thickness)

			if comp.flipped:
				s.height_below = max(s.height_below, maxz)
				s.height_above = max(s.height_above, minz)
			else:
				s.height_above = max(s.height_above, maxz)
				s.height_below = max(s.height_below, minz)

	@dag.DAGModule
	def mod_profile(s):
		with ~operations.difference():
			with ~dag.DAGGroup():
				~s.case.mod_lid_profile()
				~s.case.screw_pattern.mod_lid_profile()

			for comp in s.components:
				with ~(transform.translate(comp.position + s.case.offset_inner) *
				       transform.rotate(comp.rotation)):
					if comp.flipped:
						~transform.mirror(0, 1, 0) * comp.mod_cutout()
					else:
						~comp.mod_cutout()

	@dag.DAGModule
	def mod_plate(s, bottom=None):
		~operations.linear_extrude.n(s.thickness) * s.mod_profile()

		for comp in s.components:
			with ~(transform.translate(comp.position + s.case.offset_inner) *
			       transform.rotate(comp.rotation)):
				if s.binary and (bottom is None or bottom != comp.flipped): continue
				if comp.flipped:
					~transform.rotate(0, 180, 0) * comp.mod_addendum()
				else:
					~transform.translate(z=s.thickness) * comp.mod_addendum()

		with operations.difference.emplace():
			for comp in s.components:
				with ~(transform.translate(comp.position + s.case.offset_inner) *
				       transform.rotate(comp.rotation)):
					if comp.flipped:
						~transform.rotate(0, 180, 0) * comp.mod_cavity()
					else:
						~transform.translate(z=s.thickness) * comp.mod_cavity()

	@dag.DAGModule
	def mod_preview(s, bottom=None):
		for comp in s.components:
			with ~(transform.translate(comp.position + s.case.offset_inner) *
			       transform.rotate(comp.rotation)):
				if s.binary and (bottom is None or bottom != comp.flipped): continue
				if comp.flipped:
					~transform.rotate(0, 180, 0) * metadata.color() * comp.mod_preview()
				else:
					~transform.translate(
					  z=s.thickness) * metadata.color() * comp.mod_preview()

	@dag.DAGModule
	def mod_cavity(s):
		for comp in s.components:
			with ~(transform.translate(comp.position + s.case.offset_inner) *
			       transform.rotate(comp.rotation)):
				if comp.flipped:
					~transform.rotate(0, 180, 0) * comp.mod_cavity()
				else:
					~comp.mod_cavity()


class Case:
	def __init__(s,
	             ident,
	             wall_thickness=2.4,
	             layer_thickness=2.4,
	             wall_roundness=0):
		s.layers = list()
		s.ident = ident
		s.size_inner = V(0, 0)
		s.offset_inner = V(0, 0)
		s.wall_thickness = wall_thickness
		s.layer_thickness = layer_thickness
		s.wall_roundness = wall_roundness
		s.screw_pattern = ScrewPattern()
		s.lid_fillet = 2

	def layer(s, thickness=None, binary=False):
		l = Layer(s, thickness or s.layer_thickness, binary)
		s.layers.append(l)
		return l

	@dag.DAGModule
	def mod_lid_profile(s):

		with ~transform.translate(-s.wall_thickness, -s.wall_thickness):
			if s.wall_roundness > 0:
				~primitives.rect.rnxy(s.size_inner + V(2, 2) * s.wall_thickness,
				                      r=s.wall_roundness,
				                      roundingSegments=180)
			else:
				~primitives.rect.nxy(s.size_inner + V(2, 2) * s.wall_thickness)

	@dag.DAGModule
	def mod_lid_fillet(s, flip=False):
		with ~transform.mirror.If(flip, 0, 0, 1) * transform.translate(
		  s.size_inner / 2) * transform.translate(z=-s.lid_fillet):
			with ~(transform.mirrordup(1, 0, 0) * transform.translate(
			  x=s.size_inner.x / 2 - s.lid_fillet) * operations.difference()):
				~primitives.cuboid.nxz(s.lid_fillet, s.size_inner.y, s.lid_fillet)
				~(transform.rotate(90, 0, 0) * primitives.cylinder(
				  r=s.lid_fillet, h=s.size_inner.y - s.lid_fillet * 0, segments=90))
			with ~(transform.mirrordup(0, 1, 0) * transform.translate(
			  y=s.size_inner.y / 2 - s.lid_fillet) * operations.difference()):
				~primitives.cuboid.nyz(s.size_inner.x, s.lid_fillet, s.lid_fillet)
				~(transform.rotate(0, 90, 0) * primitives.cylinder(
				  r=s.lid_fillet, h=s.size_inner.x - s.lid_fillet * 0, segments=90))
		pass

	@dag.DAGModule
	def mod_layer_profile(s):

		if s.wall_roundness > 0:
			~primitives.rect.rnxy(
			  s.size_inner, r=s.wall_roundness, roundingSegments=180)
		else:
			~primitives.rect.nxy(s.size_inner)

	@dag.DAGModule
	def mod_frame(s, layerBottom=None, layerTop=None):
		if layerTop is None and layerBottom is None:
			raise ValueError("missing layer for frame")

		height_inner = 0
		if layerTop is not None: height_inner += layerTop.height_below
		if layerBottom is not None: height_inner += layerBottom.height_above

		with ~operations.linear_extrude.n(height_inner) * operations.difference():
			~s.mod_lid_profile()
			~s.mod_layer_profile()

		with ~transform.translate(z=height_inner):
			if layerTop is None:
				~operations.linear_extrude.n(s.wall_thickness) * s.mod_lid_profile()
			else:
				~s.screw_pattern.mod_frame_bottom(layerTop)
		if layerBottom is None:
			~operations.linear_extrude.p(s.wall_thickness) * s.mod_lid_profile()
		else:
			~s.screw_pattern.mod_frame_top(layerBottom)

		if layerBottom is None:
			~s.mod_lid_fillet(True)

		if layerTop is None:
			~transform.translate(z=height_inner) * s.mod_lid_fillet()

		with operations.difference.emplace():
			if layerTop is not None:
				~transform.translate(z=height_inner) * layerTop.mod_cavity()
			if layerBottom is not None:
				~layerBottom.mod_cavity()

	def build(s):
		x0 = 0
		x1 = 0
		y0 = 0
		y1 = 0
		layer0 = None
		for i_layer, layer in enumerate(s.layers):
			layer.build(f"{s.ident}-layer{i_layer}")

			if layer.binary:
				processing.registerEntity(
				  processing.EntityRecord(
				    processing.part, layer.mod_plate, f"{s.ident}-layer{i_layer}-top",
				    "", processing.part.DefaultProcess, list(), {"bottom": False}))
				processing.registerEntity(
				  processing.EntityRecord(processing.part, layer.mod_plate,
				                          f"{s.ident}-layer{i_layer}-bottom", "",
				                          processing.part.DefaultProcess, list(),
				                          {"bottom": True}))
			else:
				processing.registerEntity(
				  processing.EntityRecord(processing.part, layer.mod_plate,
				                          f"{s.ident}-layer{i_layer}",
				                          "", processing.part.DefaultProcess, list(),
				                          dict()))

			processing.registerEntity(
			  processing.EntityRecord(processing.part, s.mod_frame,
			                          f"{s.ident}-frame{i_layer}", "",
			                          processing.part.DefaultProcess, (layer0, layer),
			                          dict()))
			layer0 = layer
			for comp in layer.components:
				boxMin, boxMax = comp.boundingBox

				T = M.Translation(comp.position) @ M.RotationZ(comp.rotation)

				for v in (V(boxMin.x, boxMin.y), V(
				  boxMax.x, boxMin.y), V(boxMin.x, boxMax.y), V(boxMax.x, boxMax.y)):
					w = (T @ v.xyno).xy

					x0 = min(x0, w.x)
					x1 = max(x1, w.x)
					y0 = min(y0, w.y)
					y1 = max(y1, w.y)

		s.size_inner = V(x1 - x0, y1 - y0)
		s.offset_inner = V(-x0, -y0)

		s.screw_pattern.build(s)

		processing.registerEntity(
		  processing.EntityRecord(processing.part, s.mod_frame,
		                          f"{s.ident}-frame{len(s.layers)}", "",
		                          processing.part.DefaultProcess, (layer0, None),
		                          dict()))

	@dag.DAGModule
	def mod_assembly(s, explode=30):
		if len(s.layers) < 1: return

		z = 0
		layer0 = None

		for layer in s.layers:

			h = layer.height_below
			if layer0 is not None:
				h += layer0.height_above

			~transform.translate(z=z) * metadata.color() * s.mod_frame(layer0, layer)
			z += h + explode

			if layer.binary:
				~transform.translate(z=z) * metadata.color() * layer.mod_plate(
				  bottom=True)
				~transform.translate(z=z) * layer.mod_preview(bottom=True)
				z += layer.thickness + explode
				~transform.translate(z=z) * metadata.color() * layer.mod_plate(
				  bottom=False)
				~transform.translate(z=z) * layer.mod_preview(bottom=False)
				z += layer.thickness + explode

			else:

				~transform.translate(z=z) * metadata.color() * layer.mod_plate()
				~transform.translate(z=z) * layer.mod_preview()
				z += layer.thickness + explode

			layer0 = layer

		if layer0 is not None:
			~metadata.color() * transform.translate(z=z) * s.mod_frame(layer0, None)
