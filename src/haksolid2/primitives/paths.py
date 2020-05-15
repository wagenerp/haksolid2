from ..math import *
from .. import usability
import numbers
import math

class PathSegment:
	def generate(s, *args, **kwargs):
		if False: yield M()

	@property
	def lead_out(s):
		return M()


class moveto(PathSegment):
	def __init__(s, path, p=None, n=None, u=None, v=None, m=None):
		# try to obtain an orientation from our arguments
		s.m = usability.getFlexibleMatrix(p, n, u, v, m)
		path._segments.append(s)

	@property
	def lead_out(s):
		return s.m

	def generate(s, *args, **kwargs):
		yield None


class lineto(PathSegment):
	def __init__(s, path, p, n=None, u=None, v=None):

		s.m0 = path.lead_out

		if isinstance(p, numbers.Number):
			p = s.m0.col4.xyz + s.m0.col3.xyz * p
		if n is None and (u is None or v is None):
			n = p - s.m0.col4.xyz
		if u is None and (n is None or v is None):
			u = s.m0.col1.xyz
		if v is None and (n is None or u is None):
			v = s.m0.col2.xyz
		s.m1 = usability.getFlexibleMatrix(p=p, n=n, u=u, v=v)

		path._segments.append(s)

	def generate(s, *args, **kwargs):
		yield s.m0
		yield s.m1

	@property
	def lead_out(s):
		return s.m1


def bezier4(t, p0, p1, p2, p3):
	s = 1 - t
	return s**3 * p0 + 3 * s**2 * t * p1 + 3 * s * t**2 * p2 + t**3 * p3


class splineto(PathSegment):
	def __init__(s, path, p, n, lin, lout, segments):

		m0 = path.lead_out

		s.matrices = [m0]

		p0 = m0.col4.xyz
		n0 = m0.col3.xyz.normal
		n = n.normal
		n1 = n
		p1 = p
		spline = (p0, p0 + n0 * lin, p - n * lout, p)

		for i in range(segments):
			if i == segments - 1:
				n = n1
				p = p1
			else:
				p = bezier4((i + 1) / segments, *spline)
				n = (p - p0).normal

			a = math.acos(n @ n0) * 180 / math.pi
			if abs(a) < 1e-6:
				m = M()
			else:
				m = M.Rotation(a, n0.cross(n).normal)

			m = M.Translation(p) @ m @ M.Translation(-p0) @ m0
			s.matrices.append(m)
			m0 = m
			p0 = p
			n0 = n

		path._segments.append(s)

	def generate(s, *args, **kwargs):
		yield from s.matrices

	@property
	def lead_out(s):
		return s.matrices[-1]


class Path:
	def __init__(s):
		s._segments = []

	@property
	def lead_out(s):
		if len(s._segments) < 1: return M()
		return s._segments[-1].lead_out

	def generate(s, *args, **kwargs):
		for segment in s._segments:
			yield from segment.generate(*args, **kwargs)
