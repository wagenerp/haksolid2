from haksolid2.paradigms import layeredcase
from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import transform
from haksolid2 import operations
from haksolid2.prefabs import mechanical
from haksolid2 import processing


class MT30(layeredcase.Component):
	def __init__(s, p=V(), r=0, flipped=False, count=1):
		layeredcase.Component.__init__(s, p, r, flipped)
		s.screw = mechanical.screws.Screw(mechanical.threads.M2,
		                                  mechanical.screws.ScrewDriver(6, 4), 12)
		s.count = count

		s.width = 16 * count + s.screw.thread.d_throughhole + 5

	def build(s, layer, ident: str):
		processing.registerEntity(
		  processing.EntityRecord(processing.part, s.mod_preview, f"{ident}-clamp",
		                          "", processing.part.DefaultProcess, list(),
		                          dict()))

	@property
	def boundingBox(s) -> (V, V, float):
		return V(-s.width / 2, 0, 0), V(s.width / 2, 7, 14)

	@dag.DAGModule
	def mod_preview(s):
		if s.screw is not None:

			with ~operations.difference():

				with ~transform.translate(z=8):
					~primitives.cuboid.nyz(s.width, 7, 5)
				~s.mod_cavity()
				for i in range(s.count + 1):
					with ~transform.translate((i - s.count / 2) * 16, 3.5, 13 - 2.5):

						~s.screw.mod_cavity(protrusion_screw=8, protrusion_head=3)

	@dag.DAGModule
	def mod_profile(s, offset):
		with ~operations.hull():
			h = 4 * 0.75**0.5
			r = (10.25 - h) * 0.5
			~transform.translate(-2, h + r) * primitives.circle(r=r + offset,
			                                                    segments=90)
			~transform.translate(2, h + r) * primitives.circle(r=r + offset,
			                                                   segments=90)
			~transform.translate(0, r) * primitives.circle(r=r + offset, segments=90)

	@dag.DAGModule
	def mod_addendum(s):

		with ~operations.difference():

			dhole = s.screw.thread.d_throughhole
			~primitives.cuboid.nyz(s.width, 7, 8)

			~s.mod_cavity()

			for i in range(s.count + 1):
				with ~transform.translate((i - s.count / 2) * 16, 3.5):

					~transform.translate(z=8 + 1) * s.screw.mod_cavity(protrusion_screw=8)
					~transform.translate(
					  z=8 - 2 - s.screw.thread.h_nut) * s.screw.mod_nut_cavity(chute=20)

		if True: # travel guides
			for i in range(s.count + 1):
				with ~transform.translate((i - s.count / 2) * 16, 7, 1):
					~primitives.cuboid.nyz(0.3, 3, 7)
			with ~transform.translate(0, 10, 1):
				~primitives.cuboid.nyz(s.count * 16 + 0.3, 0.3, 7)

		pass

	@dag.DAGModule
	def mod_cavity(s):

		for i in range(s.count):
			with ~transform.translate((i - (s.count - 1) / 2) * 16):
				with ~transform.translate(z=1) * transform.rotate(90, 0, 0):
					~operations.linear_extrude(16) * s.mod_profile(-0.4)
					~transform.translate(
					  z=-3.6) * operations.linear_extrude.p(1.6) * s.mod_profile(0.2)
				~primitives.cuboid.pynz(10, 10, 8)


class XT60(layeredcase.Component):
	def __init__(s, p=V(), r=0, flipped=False, count=1):
		layeredcase.Component.__init__(s, p, r, flipped)
		s.screw = mechanical.screws.Screw(mechanical.threads.M2,
		                                  mechanical.screws.ScrewDriver(6, 4), 12)
		s.count = count

		s.width = 16 * count + s.screw.thread.d_throughhole + 5

	def build(s, layer, ident: str):
		processing.registerEntity(
		  processing.EntityRecord(processing.part, s.mod_preview, f"{ident}-clamp",
		                          "", processing.part.DefaultProcess, list(),
		                          dict()))

	@property
	def boundingBox(s) -> (V, V, float):
		return V(-s.width / 2, 0, 0), V(s.width / 2, 7, 22)

	@dag.DAGModule
	def mod_preview(s):
		if s.screw is not None:

			with ~operations.difference():

				with ~transform.translate(z=13):
					~primitives.cuboid.nyz(s.width, 10, 7)
				~s.mod_cavity()
				for i in range(s.count + 1):
					with ~transform.translate((i - s.count / 2) * 16, 3.5, 20 - 2):

						~s.screw.mod_cavity(protrusion_screw=8, protrusion_head=3)

	@dag.DAGModule
	def mod_profile(s, offset):
		with ~operations.hull() * operations.offset(offset):

			~primitives.rect.rny(8.2, 13.5, r=1.25, roundingSegments=90)
			~primitives.rect.rny(3.2, 15.9, r=1.25, roundingSegments=90)

	@dag.DAGModule
	def mod_addendum(s):

		with ~operations.difference():

			~primitives.cuboid.nyz(s.width, 10, 13)

			~s.mod_cavity()

			for i in range(s.count + 1):
				with ~transform.translate((i - s.count / 2) * 16, 3.5):

					~transform.translate(z=13 + 1) * s.screw.mod_cavity(
					  protrusion_screw=8)
					~transform.translate(
					  z=13 - 2 - s.screw.thread.h_nut) * s.screw.mod_nut_cavity(chute=20)

		if True: # travel guides
			for i in range(s.count + 1):
				with ~transform.translate((i - s.count / 2) * 16, 10, 1):
					~primitives.cuboid.nyz(0.3, 3, 12)
			with ~transform.translate(0, 13, 1):
				~primitives.cuboid.nyz(s.count * 16 + 0.3, 0.3, 12)

	@dag.DAGModule
	def mod_cavity(s):

		for i in range(s.count):
			with ~transform.translate((i - (s.count - 1) / 2) * 16):
				with ~operations.difference():
					with ~(transform.translate(z=1) * transform.rotate(90, 0, 0)):
						~transform.translate(
						  z=-5) * operations.linear_extrude(11) * s.mod_profile(0.2)
						~transform.translate(
						  z=0) * operations.linear_extrude(11 + 10) * s.mod_profile(0.8)

					~transform.mirrordup(1, 0, 0) * transform.translate(
					  8.2 / 2, 2, 3.4) * primitives.cuboid.nzy(0.4, 5.2, 9.2)

				~primitives.cuboid.pynz(9.8, 100, 8)
