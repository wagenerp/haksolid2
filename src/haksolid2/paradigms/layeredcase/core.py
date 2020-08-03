from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import operations
from haksolid2 import transform
from haksolid2 import metadata
from haksolid2 import prefabs


class Component:
	def __init__(s, p=V(0, 0), r=0, flipped=False):
		s.position = V(*p)
		s.rotation = r
		s.flipped = flipped

	def build(s, layer):
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


class Layer:
	def __init__(s, case, thickness):
		s.components = list()
		s.case = case
		s.height_above = 0
		s.height_below = 0
		s.thickness = thickness

	def addComponent(s, c: Component):
		s.components.append(c)
		return c

	def build(s):
		s.height_above = 0
		s.height_below = 0

		for comp in s.components:
			comp.build(s)
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
	def mod_plate(s):
		~operations.linear_extrude.n(s.thickness) * s.mod_profile()

		for comp in s.components:
			with ~(transform.translate(comp.position + s.case.offset_inner) *
			       transform.rotate(comp.rotation)):
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
	def mod_preview(s):
		for comp in s.components:
			with ~(transform.translate(comp.position + s.case.offset_inner) *
			       transform.rotate(comp.rotation)):
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

	def layer(s, thickness=None):
		l = Layer(s, thickness or s.layer_thickness)
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
		for layer in s.layers:
			layer.build()
			for comp in layer.components:
				boxMin, boxMax = comp.boundingBox

				x0 = min(x0, boxMin.x + comp.position.x)
				x1 = max(x1, boxMax.x + comp.position.x)
				y0 = min(y0, boxMin.y + comp.position.y)
				y1 = max(y1, boxMax.y + comp.position.y)

		s.size_inner = V(x1 - x0, y1 - y0)
		s.offset_inner = V(-x0, -y0)

		s.screw_pattern.build(s)

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

			~transform.translate(z=z) * metadata.color() * layer.mod_plate()
			~transform.translate(z=z) * layer.mod_preview()
			z += layer.thickness + explode

			layer0 = layer

		if layer0 is not None:
			~metadata.color() * transform.translate(z=z) * s.mod_frame(layer0, None)
