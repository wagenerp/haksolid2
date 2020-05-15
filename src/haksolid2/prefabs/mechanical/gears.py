import math
from ... import dag
from ...math import *
from ... import operations
from ... import transform
from ... import primitives


class HTDBelt:
	def __init__(s, thickness, d_tooth, pitch, protrusion):
		s.thickness = thickness
		s.d_tooth = d_tooth
		s.pitch = pitch
		s.protrusion = protrusion

	@dag.DAGModule
	def mod_teeth(s, count):
		d_ring = count * s.pitch / pi
		for i in range(count):
			with (~transform.rotate(i * 360 / count) *
			      transform.translate(y=-d_ring / 2)):
				~primitives.rect.cxnyz([s.d_tooth, s.protrusion])
				(~transform.translate(y=s.protrusion) *
				 primitives.circle(d=s.d_tooth, segments=90))

	@dag.DAGModule
	def mod_rack(s, teeth, width, protrusion=0, clearance=0.3):
		with (~transform.rotate(-90, 0, 0) * operations.linear_extrude(width)):
			for i in range(teeth):
				with (~transform.translate(i * s.pitch -
				                           (s.pitch * (teeth - 1) / 2), -s.protrusion)):
					with ~operations.difference():
						~primitives.circle(d=s.d_tooth + clearance * 2, segments=90)
						~primitives.rect.cxnyz([s.d_tooth + 2, s.d_tooth + 2])
					~primitives.rect.cxnyz([s.d_tooth + clearance * 2, s.protrusion])
			(~transform.translate(y=-clearance) * primitives.rect.cxnyz([
			  teeth * s.pitch + s.d_tooth + protrusion * 2,
			  s.thickness + clearance * 2
			]))

	@dag.DAGModule
	def mod_ring(s, count, width):

		d_ring = count * s.pitch / pi
		with ~operations.linear_extrude.n(width):
			with ~operations.difference():
				~primitives.circle(d=d_ring + s.thickness * 2, segments=1440)
				~primitives.circle(d=d_ring, segments=1440)
			for i in range(count):
				with (~transform.rotate(i * 360 / count) *
				      transform.translate(y=-d_ring / 2)):
					~primitives.rect.cxnyz([s.d_tooth, s.protrusion])
					(~transform.translate(y=s.protrusion) *
					 primitives.circle(d=s.d_tooth, segments=90))


class Involute:
	def __init__(s, module, pressure_angle=20, f_addendum=1, f_clearance=0.25):
		s._module = module
		s._pressure_angle = pressure_angle
		s._f_addendum = f_addendum
		s._f_clearance = f_clearance

	@property
	def module(s):
		return s._module

	@property
	def pressure_angle(s):
		return s._pressure_angle

	@property
	def f_addendum(s):
		return s._f_addendum

	@property
	def f_clearance(s):
		return s._f_clearance

	@property
	def addendum(s):
		return s._f_addendum * s._module

	@property
	def dedendum(s):
		return (s._f_addendum + s._f_clearance) * s._module

	def d_pitch(s, count):
		return s._module * count

	@dag.DAGModule
	def spur_profile(s, count):
		addendum = s._f_addendum * s._module
		dedendum = (s._f_addendum + s._f_clearance) * s._module
		d_pitch = s._module * count
		d_tip = d_pitch + addendum * 2
		d_root = d_pitch - dedendum * 2
		d_base = math.cos(s._pressure_angle * math.pi / 180) * d_pitch
		l_involute_base = math.sin(
		  s._pressure_angle * math.pi / 180) * d_pitch * 0.5

		segments = 16

		a1 = l_involute_base / (math.pi * d_base) * 360 - s._pressure_angle
		l_final_tangent = ((d_tip / 2)**2 - (d_base / 2)**2)**0.5
		a0 = a1 - (360 * l_final_tangent) / (math.pi * d_base)
		involute_points = [V(0, 0)]
		for i in range(segments):
			f = i / (segments - 1)
			a = f * a1 + (1 - f) * a0
			l_tangent = (a1 - a) / 360 * math.pi * d_base
			n = V(math.cos(math.pi / 180 * a), math.sin(math.pi / 180 * a))
			p = n * d_base / 2 + V(-n.y, n.x) * l_tangent
			involute_points.append(p)

		a_gap = 360 / count - (a1 + 180 / count)
		# rotate the entire gear to align at least one tooth with
		# a principal axis (x)
		with ~transform.rotate(90 / count):
			# teeth - involutes
			for i in range(count):
				# involutes
				with ~transform.rotate(360.0 * i / count):
					(~operations.hull() *
					 transform.mirrordup(V.Cylinder(90 - 90 / count)) *
					 primitives.polygon(involute_points))
			# root
			with ~operations.difference():
				~primitives.circle(d=d_base, segments=count * 8)
				for i in range(count):
					with ~transform.rotate(360 * i / count):
						# fillets (negatives)
						(~transform.rotate(90 / count + 360 / count) *
						 transform.translate(d_base / 2) *
						 transform.scale([(d_base - d_root),
						                  math.sin(a_gap * math.pi / 180) * d_base / 2]) *
						 primitives.circle(d=1, segments=segments * 2))

	@dag.DAGModule
	def rack_profile(s, count):
		pitch = math.pi * s._module
		addendum = s._f_addendum * s._module
		dedendum = (s._f_addendum + s._f_clearance) * s._module
		height = addendum + dedendum
		tanpa = math.tan(s._pressure_angle * math.pi / 180)
		for i in range(count):
			with ~transform.translate(x=(i + 0.5) * pitch, y=-dedendum):
				(~primitives.polygon(points=[
				  [-1 / 2 * pitch, 0],
				  [-1 / 2 * pitch, 0],
				  [-1 / 4 * pitch - dedendum * tanpa, 0],
				  [-1 / 4 * pitch + addendum * tanpa, height],
				  [1 / 4 * pitch - addendum * tanpa, height],
				  [1 / 4 * pitch + dedendum * tanpa, 0],
				  [1 / 2 * pitch, 0],
				  [1 / 2 * pitch, 0],
				]))
