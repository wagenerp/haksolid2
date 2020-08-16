import math
from ... import dag
from ...math import *
from ... import operations
from ... import transform
from ... import primitives
from . import threads


class ScrewDriver:
	def __init__(s, d_body, h_body, is_grub=False, clearance=None):
		s.d_body = d_body
		s.h_body = h_body
		s.is_grub = is_grub

	@dag.DAGModule
	def mod_body(s, segments=90):
		~primitives.cylinder.nz(d=s.d_body, h=s.h_body, segments=segments)

	@dag.DAGModule
	def mod_cavity(s, clearance=0.2, protrusion=0, segments=90):
		(~transform.translate([0, 0, -clearance]) *
		 primitives.cylinder.nz(d=s.d_body + clearance,
		                        h=s.h_body + clearance * 2 + protrusion,
		                        segments=segments))


class CountersunkDriver:
	def __init__(s, d_body, d_base, angle=120, clearance=None):
		t = math.tan(angle / 2 * math.pi / 180)
		s.d_body = d_body
		s.d_base = d_base
		s.h_body = (d_body - d_base) / (2 * t)
		s.angle = angle
		s.is_grub = False

	@dag.DAGModule
	def mod_body(s, segments=90):
		~primitives.cylinder.nz(
		  d0=s.d_base, d1=s.d_body, h=s.h_body, segments=segments)

	@dag.DAGModule
	def mod_cavity(s, clearance=0.2, protrusion=0, segments=90):
		(~transform.translate([0, 0, -clearance]) *
		 primitives.cylinder.nz(d0=s.d_base + clearance,
		                        d1=s.d_body + clearance,
		                        h=s.h_body + clearance * 2,
		                        segments=segments))

		if protrusion > 0:
			(~transform.translate(z=s.h_body) * primitives.cylinder.nz(
			  d=s.d_body + clearance, h=protrusion, segments=segments))


class ExternalHexDriver(ScrewDriver):
	def __init__(s, size_body, h_body, clearance=None):
		ScrewDriver.__init__(s, size_body * (4 / 3)**0.5, h_body, False, clearance)

	@dag.DAGModule
	def mod_body(s, segments=None):
		~primitives.cylinder.nz(d=s.d_body, h=s.h_body, segments=6)

	@dag.DAGModule
	def mod_cavity(s, clearance=0.2, protrusion=0, segments=None):
		(~transform.translate([0, 0, -clearance]) *
		 primitives.cylinder.nz(d=s.d_body + clearance,
		                        h=s.h_body + clearance * 2 + protrusion,
		                        segments=6))


class Screw:
	def __init__(s,
	             thread: threads.Thread,
	             driver: ScrewDriver,
	             length,
	             clearance=None):
		s.thread = thread
		s.driver = driver
		s.length = length
		s.clearance = clearance

	@dag.DAGModule
	def mod_cavity(s,
	               clearance=None,
	               protrusion_screw=0,
	               protrusion_head=0,
	               segments=90):
		clearance = clearance or s.clearance or 0.2
		# head
		if not s.driver.is_grub:
			(~s.driver.mod_cavity(
			  clearance, protrusion=protrusion_head, segments=segments))
		elif protrusion_head > 0:
			(~primitives.cylinder.nz(d=s.thread.d_throughhole + clearance * 2,
			                         h=protrusion_head,
			                         segments=segments))

		# body
		length_actual = s.length + clearance + protrusion_screw
		(~transform.translate([0, 0, -length_actual]) *
		 primitives.cylinder.nz(d=s.thread.d_throughhole + clearance * 2,
		                        h=length_actual + clearance,
		                        segments=segments))

	@dag.DAGModule
	def mod_nut_cavity(s, protrusion=0, clearance=None, chute=None):
		clearance = clearance or s.clearance or 0.2
		rotation = 12 if chute is not None else 0
		rotation = 30
		diam = s.thread.d_nut + clearance * 2
		with ~transform.translate([0, 0, -clearance - protrusion]):
			(~transform.rotate(rotation) * primitives.cylinder.nz(
			  d=diam, h=s.thread.h_nut + clearance * 2 + protrusion, segments=6))
			if chute is not None:
				(~primitives.cuboid.nzycx([
				  diam * 3**0.5 / 2, chute, s.thread.h_nut + clearance * 2 + protrusion
				]))

	@dag.DAGModule
	def mod_body(s, segments=None):
		# head
		if not s.driver.is_grub:
			~s.driver.mod_body(segments=segments)

		# body
		with ~transform.translate([0, 0, -s.length]):
			~primitives.cylinder.nz(d=s.thread.d_min, h=s.length, segments=segments)
			with ~operations.intersection():
				~s.thread.external(s.length, segments=segments)
				d = s.thread.d_throughhole * 2
				~primitives.cuboid.nz([d, d, s.length])
