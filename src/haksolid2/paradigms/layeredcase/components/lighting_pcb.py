from haksolid2.paradigms import layeredcase
from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import transform
from haksolid2 import operations


class WS2812_6P6C(layeredcase.Component):
	def __init__(s, p=V(0, 0), r=0, flipped=False, passthrough=True):
		layeredcase.Component.__init__(s, p, r, flipped)
		s.passthrough = passthrough

	@property
	def boundingBox(s) -> (V, V, float):
		return V(-14, -25, -6), V(14, 25, 2 + 1.6 + 16)

	@dag.DAGModule
	def mod_preview(s):
		~primitives.cuboid.nz(20, 50, 1.6)

		~primitives.cuboid.nzpy(1, 8, 3)

		~transform.mirrordup(
		  1, 0, 0) * transform.rotate(60) * primitives.cuboid.nzpy(1, 3, 3)

	@dag.DAGModule
	def mod_cutout(s):
		~transform.mirrorquad() * transform.translate(10, 10) * primitives.rect.nx(
		  4, 6)

	@dag.DAGModule
	def mod_addendum(s):
		pass

	@dag.DAGModule
	def mod_cavity(s):
		alt = 1.6 + 2

		if s.passthrough:
			~transform.translate(z=0) * primitives.cuboid.nz([13, 100, 16 + alt])
		else:
			~transform.translate(z=0) * primitives.cuboid.pynz([13, 100, 16 + alt])
