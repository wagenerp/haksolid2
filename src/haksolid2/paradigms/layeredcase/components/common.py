from haksolid2.paradigms import layeredcase
from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import transform


class Wireport(layeredcase.Component):
	def __init__(s,
	             p=V(),
	             r=0,
	             flipped=False,
	             wires=tuple(),
	             spacing=0.8,
	             screw=None):
		layeredcase.Component.__init__(s, p, r, flipped)
		s.wires = tuple(wires)
		s.spacing = spacing
		s.screw = screw

		if len(wires) < 1:
			raise ValueError("need at least one wire")
		s.bundle_width = sum(wires) + (len(wires) - 1) * spacing

		s.depth = 0
		s.width = s.bundle_width
		s.height = max(wires)

	def build(s, layer):
		if s.screw is not None:

			s.h_cover = s.height / 2 + 1

			s.depth = max(s.screw.driver.d_body, s.screw.thread.d_nut + 3)
			s.screw_spacing = s.width + s.depth + 2 * s.spacing
			s.width += 2 * s.depth + 2 * s.spacing

			s.altitude = s.screw.length - layer.thickness - s.screw.thread.h_nut - s.h_cover
			s.height = s.altitude + s.h_cover + s.screw.driver.h_body
		else:
			s.altitude = s.height / 2

		s.protrusion = layer.case.wall_thickness

	@property
	def boundingBox(s) -> (V, V, float):

		return V(-s.width / 2, -s.depth, 0), V(s.width / 2, 0, s.height)

	@dag.DAGModule
	def mod_addendum(s):
		if s.screw is not None:
			~primitives.cuboid.pynz(s.width, s.depth, s.altitude)

	@dag.DAGModule
	def mod_cavity(s):
		with ~(transform.translate(-s.bundle_width / 2, -s.depth - 1, s.altitude) *
		       transform.rotate(-90, 0, 0)):
			x = 0
			for d in s.wires:
				~transform.translate(x) * primitives.cylinder.nz(
				  d=d, h=s.depth + 1 + s.protrusion + 1, segments=90)
				x += s.spacing + d

		if s.screw is not None:
			~transform.mirrordup(1, 0, 0) * transform.translate(
			  s.screw_spacing / 2, -s.depth / 2,
			  s.altitude + s.h_cover) * s.screw.mod_cavity()
