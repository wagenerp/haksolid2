from haksolid2.paradigms import layeredcase
from haksolid2.math import *
from haksolid2 import dag
from haksolid2 import primitives
from haksolid2 import transform

class WS2812_6P6C(layeredcase.Component):
	@property
	def boundingBox(s) -> (V, V, float):
		return V(-14, -25, -6), V(14, 25, 2 + 1.6 + 16)

	@dag.DAGModule
	def mod_preview(s):
		~transform.translate(z=2) * primitives.rect(20, 50)

	@dag.DAGModule
	def mod_cutout(s):
		~transform.mirrorquad() * transform.translate(10, 10) * primitives.rect.nx(4, 6)

	@dag.DAGModule
	def mod_addendum(s):
		pass

	@dag.DAGModule
	def mod_cavity(s):
		alt = 1.6 + 2
		~transform.translate(z=0) * primitives.cuboid.nz([13, 100, 16 + alt])
