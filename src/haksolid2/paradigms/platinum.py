from collections import namedtuple
import math
from ..math import *
from .. import dag
from .. import transform
from .. import primitives
from .. import operations
from .. import metadata
from .. import usability
from .. import processing
import hashlib

plate_t = namedtuple("plate_t", "core diff plane flat thickness name aabb")


class PlateWrapper:
	def __init__(s, node):
		s._node = node

	def __enter__(s):
		return s._node.__enter__()

	def __exit__(s, *args, **kwargs):
		return s._node.__exit__(*args, **kwargs)


def clip2d_line_halfspace_int(p, q, n, o, d1, d2):
	if d1 == d2:
		if d1 < 0:
			return None
		else:
			return (p, q)
	elif d2 < 0:
		return clip2d_line_halfspace_int(q, p, n, o, d2, d1)
	else:
		return (p + (p @ n - o) * (q - p).normal / ((p - q).normal @ n), q)


def clip2d_line_halfspace(l, n, o):
	if l is None: return None
	for i in range(2):
		if math.isnan(l[0][i]) or math.isnan(l[1][i]): return None
	return clip2d_line_halfspace_int(l[0], l[1], n, o, -1 if
	                                 (l[0] @ n - o < -1e-8) else 1, -1 if
	                                 (l[1] @ n - o < -1e-8) else 1)


def clip2d_line_rect(v, box):
	return clip2d_line_halfspace(
	  clip2d_line_halfspace(
	    clip2d_line_halfspace(clip2d_line_halfspace(v, V(1, 0), box.min.x),
	                          V(-1, 0), -box.max.x), V(0, 1), box.min.y), V(
	                            0, -1), -box.max.y)


def proj_point(p, m):
	return V((m @ V(1, 0, 0, 0)).xyz @ (p - (m @ V(0, 0, 0, 1)).xyz),
	         (m @ V(0, 1, 0, 0)).xyz @ (p - (m @ V(0, 0, 0, 1)).xyz))


def pt_sort_line(l):
	if l[0][0] < l[1][0]: return l
	if (l[0][0] == l[1][0]) and (l[0][1] < l[1][1]): return l
	#if (l[0][1] == l[1][1]) and ((l[0][2] or 0) < (l[1][2] or 0)): return l
	if ((l[0][1] == l[1][1]) and (len(l[0]) > 2) and (len(l[1]) > 2) and
	    (l[0][2] < l[1][2])):
		return l
	return (l[1], l[0])


def pt_reproject_line(l, m):
	return ((m @ V(l[0][0], l[0][1], 0, 1)).xy,
	        (m @ V(l[1][0], l[1][1], 0, 1)).xy)


def pt_test_cut1(p, box, t=0.2):
	if (p[0] < box.min.x + t) or (p[1] < box.min.y + t) or (
	  p[0] > box.max.x - t) or (p[1] > box.max.y - t):
		return 1
	return 0


def pt_test_cut2(a, b):
	return (a and b, a or b, a, b)


def pt_test_cut(l, box, t=0.2):
	return pt_test_cut2(pt_test_cut1(l[0], box, t), pt_test_cut1(l[1], box, t))


def pt_test_edge1(l, c, o, t, e):
	if (abs(l[0][c] - o) < t) and (abs(l[1][c] - o) < t): return (c, o)
	return e


def pt_test_edge(l, box, t=0.2):
	return pt_test_edge1(
	  l, 0, box.min.x, t,
	  pt_test_edge1(
	    l, 0, box.max.x, t,
	    pt_test_edge1(l, 1, box.min.y, t, pt_test_edge1(l, 1, box.max.y, t,
	                                                    None))))


def edge_key(name1, name2):
	if name1 is None:
		return (name2, name1)
	elif name2 is None:
		return (name1, name2)
	else:
		return tuple(sorted((name1, name2)))


class Platinum:
	class EdgeConfig:
		Keys = ("forceSlit", "finger_overlap", "finger_grip", "finger_lip",
		        "finger_length", "slit_grip", "invert", "forceFinger", "ignore")

		def __init__(s,
		             forceSlit=False,
		             finger_overlap=None,
		             finger_grip=None,
		             finger_lip=None,
		             finger_length=None,
		             slit_grip=None,
		             invert=None,
		             forceFinger=False,
		             ignore=False):
			s.forceSlit = forceSlit
			s.forceFinger = forceFinger
			# how much finger pairs overlap, negative numbers loosen, positive tighten
			# e.g. -1 causes a slit -2 units wide between adjacent fingers
			s.finger_overlap = finger_overlap
			# how far fingers cut into the material. this is added to material
			# thickness negative numbers cut deeper, positive ones less deep.
			s.finger_grip = finger_grip
			# inset from edges for finger joints. this can be used to correct corner
			# artifacts.
			s.finger_lip = finger_lip
			# basic length of each finger
			s.finger_length = finger_length
			# tightness of slits, negative numbers loosen, positive ones tighten
			s.slit_grip = slit_grip
			# flips parity on slit and finger joints
			s.invert = invert
			# ignore collisions
			s.ignore = ignore

		def override(s, b):
			if b is None:
				return Platinum.EdgeConfig(
				  **{k: getattr(s, k)
				     for k in Platinum.EdgeConfig.Keys})
			return Platinum.EdgeConfig(
			  **{
			    k: getattr(s, k) if getattr(b, k) is None else getattr(b, k)
			    for k in Platinum.EdgeConfig.Keys
			  })

	def __init__(s,
	             default_thickness=4,
	             beam_width=0.2,
	             edgeConfig=None,
	             process=None):
		s._global_hole = dag.DAGGroup()
		s._global_envelope = dag.DAGGroup()
		s._default_thickness = default_thickness
		s._beam_width = beam_width

		s._edgeConfig = Platinum.EdgeConfig(finger_overlap=0.2,
		                                    finger_grip=0.1,
		                                    finger_lip=4,
		                                    finger_length=8,
		                                    slit_grip=0.1,
		                                    invert=False,
		                                    ignore=False).override(edgeConfig)

		s._plates = list()
		s._edgeConfigOverrides = dict()
		s._process = process

	def configureEdge(s, plate1, plate2, cfg):
		key = edge_key(plate1, plate2)
		s._edgeConfigOverrides[key] = cfg

	@property
	def hole(s):
		return s._global_hole

	@property
	def envelope(s):
		return s._global_envelope

	@dag.DAGModule
	def mod_finger_joint(s, cfg, l, v, p, protrude=0, thickness=None):
		thickness = thickness or s._default_thickness
		oh = cfg.finger_overlap / 2
		gh = cfg.finger_grip / 2
		lh = (l[1] - l[0]).norm / 2
		u = (l[1] - l[0]).normal

		protrude1 = protrude * (v[0] / abs(v[0]) if
		                        (abs(v[0]) > abs(v[1])) else v[1] / abs(v[1]))

		y1 = gh + min(0, protrude1)
		y2 = thickness - gh + max(0, protrude1)

		matrices = (M([u[0], v[0], 0, l[0][0]], [u[1], v[1], 0, l[0][1]],
		              [0, 0, 1, 0], [0, 0, 0, 1]),
		            M([-u[0], v[0], 0, l[1][0]], [-u[1], v[1], 0, l[1][1]],
		              [0, 0, 1, 0], [0, 0, 0, 1]))

		@dag.DAGModule
		def finger(x, w):
			for m in matrices:
				(~transform.matrix(m) * primitives.polygon(
				  [x + oh, y1], [x + w - oh, y1], [x + w - oh, y2], [x + oh, y2]))

		if p > 0:
			x = cfg.finger_lip
			while x < lh:
				~finger(x, min(lh - x, cfg.finger_length))
				x += cfg.finger_length * 2
		else:
			~finger(0, cfg.finger_lip)

			x = cfg.finger_lip + cfg.finger_length
			while x < lh:
				~finger(x, min(lh - x, cfg.finger_length))
				x += cfg.finger_length * 2

	@dag.DAGModule
	def mod_slit_joint(s,
	                   cfg,
	                   l,
	                   v,
	                   protrude1=False,
	                   protrude2=False,
	                   thickness=None):
		thickness = thickness or s._default_thickness
		gh = cfg.slit_grip / 2
		w = (l[1] - l[0]).norm
		u = (l[1] - l[0]) / w
		x1 = -2 * thickness if protrude1 else gh
		x2 = w + 2 * thickness if protrude2 else w - gh
		(~transform.matrix([[u[0], v[0], 0, l[0][0]], [u[1], v[1], 0, l[0][1]],
		                    [0, 0, 1, 0], [0, 0, 0, 1]]) *
		 primitives.polygon([x1, gh], [x1, thickness - gh], [x2, thickness - gh],
		                    [x2, gh]))

	def plate(s,
	          name=None,
	          ex=None,
	          ey=None,
	          ez=None,
	          p=None,
	          thickness=None,
	          process=None,
	          aabb=None):
		if process is None: process = s._process
		thickness = thickness or s._default_thickness

		core = dag.DAGGroup()

		diff = operations.difference()
		diff * core

		flat = operations.intersection()
		plane = flat
		if name is not None:
			plane = processing.part(name=name, process=process) * plane
		with plane:
			~diff

		plate = plate_t(core, diff, plane, flat, thickness, name, aabb)
		s._plates.append(plate)

		preview = metadata.color(
		  a=0.4) * operations.linear_extrude.n(thickness) * plane

		res = dag.DAGNodeConcatenator(preview, core)
		return transform.rebase(p, ex, ey, ez) * res

	def _retrieve_matrix(s, p):
		v = usability.AllAbsTransformsVisitor()
		p.core.visitAncestors(v)
		if len(v.absTransforms) != 1:
			raise RuntimeError(f"ambiguous plate placement for {p.name}")
		return v.absTransforms[0]

	def _retrieve_aabb(s, p):
		visitor = metadata.BoundingBoxVisitor()
		p.core.visitDescendants(visitor)
		return visitor.aabb

	def _combine_plates(s, i1, i2):
		if i1 == i2: return
		p1 = s._plates[i1]
		p2 = s._plates[i2]
		cfg = s._edgeConfig
		key = edge_key(p1.name, p2.name)
		if key in s._edgeConfigOverrides:
			cfg = cfg.override(s._edgeConfigOverrides[key])

		m1 = s._retrieve_matrix(p1) @ M.Translation(V(0, 0, -p1.thickness * 0.5))
		m2 = s._retrieve_matrix(p2) @ M.Translation(V(0, 0, -p2.thickness * 0.5))

		if cfg.ignore: return
		box1 = s._retrieve_aabb(p1)
		box2 = s._retrieve_aabb(p2)

		# compute intersection of hyperplanes defined by p1 and p2
		w1 = (m1 @ V(0, 0, 1, 0)).xyz # normal of p1
		w2 = (m2 @ V(0, 0, 1, 0)).xyz # normal of p2
		# point on intersection line
		p = ((m1 @ V(0, 0, 0, 1)).xyz + (((m2 - m1) @ V(0, 0, 0, 1)).xyz @ w2) * w2)
		# direction of intersection line
		u = w1.cross(w2).normal

		# clip line to bounding boxes of both planes
		# this yields a 2d line in the respective planes' subspace
		# (so we need to re-project the line for the second step)
		t1 = clip2d_line_rect(
		  [proj_point(-10000 * u + p, m2),
		   proj_point(p + u * 10000, m2)], box2)
		if t1 is None: return # no collision
		t2 = clip2d_line_rect(pt_reproject_line(t1, m1.inverse @ m2), box1)
		if t2 is None: return # no collision

		# at this point we know we have a collision,
		# for repeatability we sort the line segments's endpoints as represented in
		# the first plane's coordinates
		# then extract the line representation in the second plane's subspace.
		l1 = pt_sort_line(t2)
		l2 = pt_reproject_line(l1, m2.inverse @ m1)

		# test if the line coincides with a plane's edge.
		# this is a crude method, does not account for holes etc.
		# todo: figure out what thickness to use
		# todo: find a better way of detecting edges
		e1 = pt_test_edge(l1, box1, t=s._beam_width + p1.thickness)
		e2 = pt_test_edge(l2, box2, t=s._beam_width + p2.thickness)

		# test if we cut through any of the both plates
		c1 = pt_test_cut(l1, box1, t=s._beam_width)
		c2 = pt_test_cut(l2, box2, t=s._beam_width)

		# 2vector perpendicular to line direction in p1's subspace
		v = (m1.inverse @ m2 @ V(0, 0, 1, 0)).xy

		# cut into p1 depending on how we intersect with p2

		if (c1[2] and not c1[3]): parity = False
		elif (not c1[2] and c1[3]): parity = True
		elif (c2[2] and not c2[3]): parity = True
		elif (not c2[2] and c2[3]): parity = False
		elif i1 < i2: parity = False
		else: parity = True
		if cfg.invert: parity = not parity
		with p1.diff:
			if (e1 is not None or cfg.forceFinger) and not cfg.forceSlit:
				# intersection occurs at p1's edge
				protrude = 1 if e1[1] > box1.center[e1[0]] else -1
				~s.mod_finger_joint(cfg, l1, v, -1 if parity else 1, protrude=protrude)
			elif e2 is not None and not cfg.forceSlit:
				# intersection occurs at p2's edge
				~s.mod_finger_joint(cfg, l1, v, -1 if parity else 1)
			elif c1[0] and not c2[1]:
				# p2 cuts p1 clean through (so we remain intact here - p2 sees case
				# below)
				pass
			elif c2[0] and not c1[1]:
				# p1 cuts p2 clean through - add a slit in p1 to move p2 through p1
				~s.mod_slit_joint(cfg, l1, v)
			else:
				# at least for one partner, we cut in from an edge.
				# cut a slit halfway across the line on both partners to allow
				# sticking them together.
				slit_center = (l1[0] + l1[1]) / 2
				slit_line = [slit_center, l1[1]] if parity else [l1[0], slit_center]
				~s.mod_slit_joint(cfg, slit_line, v, not parity and c1[2], parity and
				                  c1[3])

	def build(s):
		for i1, p1 in enumerate(s._plates):
			for i2, p2 in enumerate(s._plates):
				if i1 == i2: continue
				s._combine_plates(i1, i2)

			if len(s._global_hole.children) > 0:
				m = s._retrieve_matrix(p1) @ M.Translation(V(0, 0, -p1.thickness * 0.5))

				with p1.diff:

					with ~operations.projection() * operations.intersection():
						~transform.matrix(m.inverse) * s._global_hole
						~dag.DAGVirtualRoot() * operations.linear_extrude.n(
						  p1.thickness) * p1.core
			if len(s._global_envelope.children) > 0:
				m = s._retrieve_matrix(p1) @ M.Translation(V(0, 0, -p1.thickness * 0.5))

				with p1.plane:

					with ~operations.projection() * operations.intersection():
						~transform.matrix(m.inverse) * s._global_envelope
						~dag.DAGVirtualRoot() * operations.linear_extrude.n(
						  p1.thickness) * p1.core

	@dag.DAGModule
	def mod_preview(s):
		for plate in s._plates:
			with transform.matrix(plate.m) * operations.linear_extrude(
			  plate.thickness):
				plate.plane.instance()
			with preview_layer(color=[0.2, 0.2, 1.0, 0.3]):
				transform.matrix(plate.m) * plate.core.instance()

		with preview_layer(color=[1, 0.4, 0.2, 0.3]):
			s._global_hole.instance()
		with preview_layer(color=[0.4, 1.0, 0.2, 0.3]):
			s._global_envelope.instance()

	@dag.DAGModule
	def _mod_plate(s, plate):
		with ~transform.matrix(s._retrieve_matrix(plate)):

			~operations.linear_extrude.c(plate.thickness) * plate.flat

	@dag.DAGModule
	def mod_plate(s, ident):
		for plate in s._plates:
			if plate.name != ident: continue
			~plate.plane

	@dag.DAGModule
	def mod_assembly(s, explode=0):
		for plate in s._plates:

			box = s._retrieve_aabb(plate)
			m = s._retrieve_matrix(plate)
			anchor = (m @ V(box.center.x, box.center.y, plate.thickness * 0.5, 1)).xyz
			explosion = anchor * explode
			with ~metadata.color() * transform.translate(explosion):
				~s._mod_plate(plate)
