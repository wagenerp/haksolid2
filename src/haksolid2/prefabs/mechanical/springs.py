import math
from ... import dag
from ...math import *
from ... import operations
from ... import transform
from ... import primitives


class Spring:
	def __init__(s, d_coil, l_coil, d_wire, n_windings, clearance=0.2):
		s.d_coil = d_coil
		s.l_coil = l_coil
		s.d_wire = d_wire
		s.n_windings = n_windings
		s.d_inner = d_coil - d_wire - clearance * 2
		s.clearance = clearance

	@dag.DAGModule
	def mod_body(s, elongation=None):
		elongation = elongation or s.l_coil
		if False:
			segments = s.n_windings * 360 // 45

			dm = M.Translation([0, 0, elongation / segments]) @ M.RotationZ(
			  s.n_windings * 360 / segments)

			m0 = M()
			for i in range(segments):
				m1 = dm @ m0
				with ~transform.matrix(m0) * operations.hull():
					(~transform.translate([s.d_coil / 2 - s.d_wire / 2, 0]) *
					 transform.rotate([90, 0, 0]) *
					 primitives.cylinder.nz(d=s.d_wire, segments=45, h=1e-4))
					(~transform.matrix(dm) *
					 transform.translate([s.d_coil / 2 - s.d_wire / 2, 0]) *
					 transform.rotate([90, 0, 0]) *
					 primitives.cylinder.nz(d=s.d_wire, segments=45, h=1e-4))
				m0 = m1
		else:
			#segments = s.n_windings * 360 // 45
			segments = s.n_windings * 8
			m = M.Translation([0, 0, elongation / segments]) @ M.RotationZ(
			  360 * s.n_windings / segments)
			offset = M.RotationY(90)
			with ~operations.matrix_extrude(m, steps=segments, offset=offset):
				(~transform.translate([0, s.d_coil / 2 - s.d_wire / 2, 0]) *
				 primitives.circle(d=s.d_wire, segments=16))

			#with linear_extrude(height=elongation,twist=s.n_windings*360):
			#	transform.translate([s.d_coil/2-s.d_wire/2,0]) * primitives.circle(d=s.d_wire,segments=45)

	@dag.DAGModule
	def mod_cavity(s, clearance=None, segments=None):
		clearance = clearance or s.clearance

		(~transform.translate(z=-clearance) * primitives.cylinder.nz(
		  d=s.d_coil + clearance * 2, h=s.l_coil + clearance * 2,
		  segments=segments))
