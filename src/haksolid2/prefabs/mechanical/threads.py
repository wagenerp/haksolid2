import math
from ... import dag
from ...math import *
from ... import operations
from ... import transform
from ... import primitives


@dag.DAGModule
def external_metric_thread(pitch=1.25,
                           dmaj=8,
                           length=10,
                           segments=None,
                           segments_per_revolution=32,
                           clearance=0,
                           solid=False):

	if segments is None:
		if segments_per_revolution is None: segments_per_revolution = 32
		segments = math.ceil(segments_per_revolution * length / pitch)
	height = pitch * (0.75**0.5)

	y0 = dmaj / 2 - height * 0.625
	x1 = 0.375 * pitch - clearance * 2
	cleared_height = x1 * 3**0.5
	y1 = min(height * 0.625 - clearance, cleared_height)
	x2 = x1 - y1 * 3**-0.5
	m = M.Translation([0, 0, length / segments]) @ M.RotationZ(
	  360 * (length / pitch) / segments)
	offset = M.RotationY(90)

	with ~operations.matrix_extrude(m, steps=segments, offset=offset):
		~primitives.polygon([-x1, y0], [x1, y0], [x2, y0 + y1], [-x2, y0 + y1])

	if solid:
		~primitives.cylinder.enz(
		  r=y0 + 1e-2, h=length, segments=segments_per_revolution)


@dag.DAGModule
def internal_metric_thread(pitch=1.25,
                           dmaj=8,
                           length=10,
                           segments=None,
                           segments_per_revolution=32,
                           dtube=None,
                           clearance=0):

	if segments is None:
		segments = math.ceil(segments_per_revolution * length / pitch)
	else:
		segments_per_revolution = segments // (length / pitch)
	height = pitch * (0.75**0.5)
	length += pitch

	x2 = 0.4375 * pitch - clearance * 2
	cleared_height = x2 * 3**0.5
	y1 = min(height * 0.625 - clearance, cleared_height)
	x1 = x2 - y1 * 3**-0.5
	y1 = height * 0.625 - y1
	y2 = height * 0.625

	m = M.Translation([0, 0, length / segments]) @ M.RotationZ(
	  360 * (length / pitch) / segments)
	offset = M.RotationY(90)
	with (~transform.translate([0, 0, -pitch / 2]) *
	      operations.matrix_extrude(m, steps=segments, offset=offset)):
		with ~transform.translate(0, dmaj / 2 - height * 0.625) * operations.hull():
			~primitives.polygon([-x1, y1], [x1, y1], [x2, y2], [-x2, y2])

	if dtube is not None:
		with ~operations.linear_extrude.n(length) * operations.difference():
			~primitives.circle.e(d=dtube, segments=segments_per_revolution)
			~primitives.circle.e(d=dmaj, segments=segments_per_revolution)


@dag.DAGModule
def whitworth_profile(density_tpi,
                      dmaj_in,
                      clearance=0,
                      arc_segments=64,
                      d_inner=None,
                      invert=False,
                      dtube=None):
	pitch = 25.4 / density_tpi
	dmaj = dmaj_in * 25.4
	theta_rad = math.pi / 180 * 27.5
	height = pitch / (2 * math.tan(theta_rad))
	depth = pitch / (3 * math.tan(theta_rad))
	arc_height = height * math.sin(theta_rad) / 6
	arc_radius = arc_height / (1 - math.sin(theta_rad))

	# note that this ranges from d_min up to the tangent, not tangent to tangent!
	straight_flank = tuple((math.tan(theta_rad) * y, height - y)
	                       for y in ((height / 6 + arc_height), height))

	if dtube is None:
		dtube = dmaj + clearance

	if d_inner is None:
		d_inner = dmaj - 2 * height * 5 / 6

	positive = dag.DAGGroup()
	with positive:

		with ~transform.translate(y=dmaj / 2 - height * 5 / 6) * operations.offset(
		  -clearance, round=True):
			~primitives.polygon(points=[
			  (-straight_flank[1][0], straight_flank[1][1]),
			  (-straight_flank[0][0], straight_flank[0][1]),
			  (+straight_flank[0][0], straight_flank[0][1]),
			  (+straight_flank[1][0], straight_flank[1][1]),
			])
			~transform.translate(y=height * 5 / 6 - arc_radius) * primitives.circle(
			  r=arc_radius, segments=arc_segments)

			with ~operations.difference():
				(~transform.translate(-pitch / 2, 0) *
				 primitives.rect.nxy(pitch, height / 6 + arc_height))
				(~transform.translate(-pitch / 2, height / 6 + arc_radius) *
				 primitives.circle(r=arc_radius, segments=arc_segments))
				(~transform.translate(pitch / 2, height / 6 + arc_radius) *
				 primitives.circle(r=arc_radius, segments=arc_segments))

		(~transform.translate(-pitch / 2 - 0.1, d_inner / 2) *
		 primitives.rect.nxy(pitch + 0.2, (dmaj - d_inner) / 2 - depth - clearance))
		with operations.intersection.emplace():
			(~transform.translate(-pitch / 2 - 0.1, (d_inner) / 2) *
			 primitives.rect.nxy([pitch + 0.2, (dmaj - d_inner) / 2 + clearance + 1]))

	if invert:
		with ~operations.difference():
			(~transform.translate(-pitch / 2 - 0.05, d_inner / 2) *
			 primitives.rect.nxy([pitch + 0.1, (dtube - d_inner) / 2]))
			~positive
	else:
		~positive


@dag.DAGModule
def external_whitworth_thread(density_tpi,
                              dmaj_in,
                              length=10,
                              segments=None,
                              segments_per_revolution=32,
                              arc_segments=16,
                              dtube=None,
                              clearance=0,
                              align_segments=True):

	revolutions = length * density_tpi / 25.4
	if align_segments:
		revolutions = math.ceil(
		  revolutions * segments_per_revolution) / segments_per_revolution
	if segments is None:
		segments = math.ceil(segments_per_revolution * revolutions)

	m = M.Translation([0, 0, length / segments]) @ M.RotationZ(
	  360 * revolutions / segments)
	offset = M.RotationY(90)
	with ~operations.matrix_extrude(m, steps=segments, offset=offset):
		~whitworth_profile(density_tpi,
		                   dmaj_in,
		                   clearance=clearance,
		                   arc_segments=arc_segments,
		                   d_inner=dtube)


@dag.DAGModule
def internal_whitworth_thread(density_tpi,
                              dmaj_in,
                              length=10,
                              segments=None,
                              segments_per_revolution=32,
                              arc_segments=16,
                              dtube=None,
                              clearance=0,
                              align_segments=True):

	revolutions = length * density_tpi / 25.4
	if align_segments:
		revolutions = math.ceil(
		  revolutions * segments_per_revolution) / segments_per_revolution
	if segments is None:
		segments = math.ceil(segments_per_revolution * revolutions)

	m = M.Translation([0, 0, length / segments]) @ M.RotationZ(
	  360 * revolutions / segments)
	offset = M.RotationY(90)
	with ~operations.matrix_extrude(m, steps=segments, offset=offset):
		~whitworth_profile(density_tpi,
		                   dmaj_in,
		                   clearance=-clearance,
		                   arc_segments=arc_segments,
		                   invert=True,
		                   dtube=dtube)


class Thread:
	def __init__(s, d_throughhole, h_pitch, d_taphole, d_nut, h_nut, d_maj,
	             d_min):
		s.d_throughhole = d_throughhole
		s.h_pitch = h_pitch
		s.d_taphole = d_taphole
		s.d_nut = d_nut
		s.h_nut = h_nut
		s.d_maj = d_maj
		s.d_min = d_min

	@dag.DAGModule
	def internal(s, length, segments=None, clearance=0):
		pass

	@dag.DAGModule
	def external(s, length, segments=None, clearance=0):
		pass

	@dag.DAGModule
	def mod_hexnut(s):
		with ~operations.linear_extrude(height=s.h_nut) * operations.difference():
			~primitives.circle(d=s.d_nut, segments=6)
			~primitives.circle(d=s.d_maj, segments=60)
		~s.internal(length=s.h_nut)


class MetricThread(Thread):
	TapHoles = {
	  (1, 0.25): 0.75,
	  (1.2, 0.25): 0.95,
	  (1.4, 0.3): 1.1,
	  (1.6, 0.35): 1.25,
	  (1.8, 0.35): 1.5,
	  (2, 0.4): 1.6,
	  (2.5, 0.45): 2.05,
	  (3, 0.5): 2.5,
	  (3.5, 0.6): 2.9,
	  (4, 0.7): 3.3,
	  (5, 0.8): 4.2,
	  (6, 1): 5,
	  (8, 1.25): 6.8,
	  (8, 1): 7,
	  (10, 1.5): 8.5,
	  (10, 1.25): 8.8,
	  (12, 1.75): 10.2,
	  (12, 1.25): 10.8,
	  (14, 2): 12,
	  (14, 1.5): 12.5,
	  (16, 2.5): 14,
	  (16, 2): 14,
	  (16, 1.5): 14.5,
	  (18, 2.5): 15.5,
	  (18, 1.5): 16.5,
	  (20, 2.5): 17.5,
	  (20, 1.5): 18.5,
	  (22, 2.5): 19.5,
	  (22, 1.5): 20.5,
	  (24, 3): 21,
	  (24, 2): 22,
	  (27, 3): 24,
	  (27, 2): 25,
	  (30, 3.5): 26.5,
	  (36, 4): 32,
	}

	CoarsePitches = {
	  1: 0.25,
	  1.2: 0.25,
	  1.4: 0.3,
	  1.6: 0.35,
	  1.8: 0.35,
	  2: 0.4,
	  2.5: 0.45,
	  3: 0.5,
	  3.5: 0.6,
	  4: 0.7,
	  5: 0.8,
	  6: 1,
	  7: 1,
	  8: 1.25,
	  10: 1.5,
	  12: 1.75,
	  14: 2,
	  16: 2,
	  18: 2.5,
	  20: 2.5,
	  22: 2.5,
	  24: 3,
	  27: 3,
	  30: 3.5,
	  33: 3.5,
	  36: 4,
	  39: 4,
	  42: 4.5,
	  45: 4.5,
	  48: 5,
	  52: 5,
	  56: 5.5,
	  60: 5.5,
	  64: 6,
	}
	FinePitches = {
	  1: 0.2,
	  1.2: 0.2,
	  1.4: 0.2,
	  1.6: 0.2,
	  1.8: 0.2,
	  2: 0.25,
	  2.5: 0.35,
	  3: 0.35,
	  3.5: 0.35,
	  4: 0.5,
	  5: 0.5,
	  6: 0.75,
	  7: 0.75,
	  8: 1,
	  10: 1.25,
	  12: 1.5,
	  14: 1.5,
	  16: 1.5,
	  18: 2,
	  20: 2,
	  22: 2,
	  24: 2,
	  27: 2,
	  30: 2,
	  33: 2,
	  36: 3,
	  39: 3,
	  42: 3,
	  45: 3,
	  48: 3,
	  52: 4,
	  56: 4,
	  60: 4,
	  64: 4,
	}

	NutData = {
	  1: (2.5, 0.8),
	  1.2: (3, 1.0),
	  1.4: (3, 1.2),
	  1.6: (3.2, 1.3),
	  1.8: (3.6, 1.5),
	  2: (4, 1.6),
	  2.5: (5, 2.0),
	  3: (5.5, 2.4),
	  3.5: (6, 2.8),
	  4: (7, 3.2),
	  5: (8, 4.7),
	  6: (10, 5.2),
	  8: (13, 6.8),
	  10: (16, 8.4),
	  12: (18, 10.8),
	  14: (21, 12.8),
	  16: (24, 14.8),
	  18: (27, 15.8),
	  20: (30, 18),
	  22: (34, 19.4),
	  24: (36, 21.5),
	  27: (41, 24.7),
	  30: (46, 25.6),
	  33: (50, 28.7),
	  36: (55, 31.0),
	  39: (60, 33.4),
	  42: (65, 34.0),
	  45: (70, 36),
	  48: (75, 38),
	  52: (80, 42),
	  56: (85, 45),
	  64: (95, 51),
	}

	def __init__(s,
	             d_maj,
	             h_pitch=None,
	             d_taphole=None,
	             d_throughhole=None,
	             w_nut=None,
	             d_nut=None,
	             h_nut=None,
	             fine=None):
		if h_pitch is None:
			if fine:
				h_pitch = MetricThread.FinePitches[d_maj]
			else:
				h_pitch = MetricThread.CoarsePitches[d_maj]
		elif fine is not None:
			raise ValueError("cannot select fine pitch and explicit pitch together")
		h_base = h_pitch * (0.75**0.5)

		if d_throughhole is None:
			if d_maj < 8: d_throughhole = d_maj + 0.2
			elif d_maj < 18: d_throughhole = d_maj + 0.5
			elif d_maj < 28: d_throughhole = d_maj + 1
			elif d_maj < 50: d_throughhole = d_maj + 2
			else: d_throughhole = d_maj * 1.1

		if d_taphole is None:
			d_taphole = MetricThread.TapHoles[(d_maj, h_pitch)]

		if w_nut is None and d_nut is None:
			d_nut = MetricThread.NutData[d_maj][0] * 2 / 3**0.5
		elif w_nut is not None and d_nut is None:
			d_nut = w_nut * 2 / 3**0.5
		elif w_nut is not None and d_nut is not None:
			raise ValueError("cannot specify nut diam and width together")

		if h_nut is None:
			h_nut = MetricThread.NutData[d_maj][1]

		Thread.__init__(s, d_throughhole, h_pitch, d_taphole, d_nut, h_nut, d_maj,
		                d_maj - 2 * h_base * 0.75)
		s.d_maj = d_maj
		s.h_pitch = h_pitch

	@dag.DAGModule
	def internal(s, length, segments=None, clearance=0, do_envelope=False):
		with ~dag.DAGGroup():
			~internal_metric_thread(pitch=s.h_pitch,
			                        dmaj=s.d_maj - clearance,
			                        length=length,
			                        segments=segments)
			if do_envelope:
				w = s.d_maj * 2 + clearance * 4 + 2
				with operations.intersection.emplace():
					~primitives.cuboid.cxynz(w, w, length)

	@dag.DAGModule
	def external(s,
	             length,
	             segments=None,
	             segments_per_revolution=None,
	             clearance=0,
	             solid=False,
	             enveloped=False):
		with ~dag.DAGGroup():
			~external_metric_thread(pitch=s.h_pitch,
			                        dmaj=s.d_maj + clearance,
			                        length=length,
			                        segments=segments,
			                        segments_per_revolution=segments_per_revolution,
			                        solid=solid)
			if enveloped:
				with operations.intersection.emplace():
					w = s.d_maj + clearance + 2
					~primitives.cuboid.cxynz(w, w, length)

	@dag.DAGModule
	def rod(s, length, segments=None, clearance=0):
		with ~operations.intersection():
			~external_metric_thread(pitch=s.h_pitch,
			                        dmaj=s.d_maj + clearance,
			                        length=length,
			                        segments=segments)
			w = s.d_maj * 2 + clearance * 4 + 2
			~primitives.cuboid.cxynz([w, w, length])

		height = s.h_pitch * (0.75**0.5)

		d_rod = s.d_maj + clearance - 2 * height * 0.625
		~primitives.cylinder.nz(d=d_rod, segments=180, h=length)

	@dag.DAGModule
	def internal_cavity(s, length, segments=None, clearance=0):
		~primitives.cylinder.nz(d=s.d_maj - clearance, h=length, segments=180)


M1 = MetricThread(1)
M1_2 = MetricThread(1.2)
M1_4 = MetricThread(1.4)
M1_6 = MetricThread(1.6)
M1_8 = MetricThread(1.8)
M2 = MetricThread(2)
M2_5 = MetricThread(2.5)
M3 = MetricThread(3)
M3_5 = MetricThread(3.5)
M4 = MetricThread(4)
M5 = MetricThread(5)
M6 = MetricThread(6)
M8 = MetricThread(8)
M10 = MetricThread(10)
M12 = MetricThread(12)
M14 = MetricThread(14)
M16 = MetricThread(16)
M18 = MetricThread(18)
M20 = MetricThread(20)
M22 = MetricThread(22)
M24 = MetricThread(24)
M27 = MetricThread(27)
M30 = MetricThread(30)
M36 = MetricThread(36)
