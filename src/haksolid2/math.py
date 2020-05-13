import re
import numpy
from collections import Iterable
from math import cos, sin, pi


class V(numpy.ndarray):
	"""Augmented subclass of numpy vectors.
	For usability reasons, we added more versatile constructors, getters and methods such as cross products."""
	e_subrange = re.compile("[xyzwon]+")
	key_dimensions = {"x": 0, "y": 1, "z": 2, "w": 3}

	def __new__(s, *args):
		if len(args) == 1:
			arg = args[0]
			if isinstance(arg, Iterable):
				args = [v for v in arg]
			else:
				args = [arg]

		return numpy.ndarray.__new__(s,
		                             shape=(len(args), ),
		                             buffer=numpy.array([float(v) for v in args]),
		                             dtype=float)

	@classmethod
	def Cylinder(cls, phi, r=1, z=0):
		a = pi / 180 * phi
		return V(cos(a) * r, sin(a) * r, z)

	def __getitem__(s, k):
		if isinstance(k, slice):
			return V(numpy.ndarray.__getitem__(s, k))
		else:
			return numpy.ndarray.__getitem__(s, k)

	def __getattribute__(s, attr):
		def resolve(key):
			if key == "o": return 1
			elif key == "n": return 0
			else: return s[V.key_dimensions[key]]

		if V.e_subrange.fullmatch(attr):
			if len(attr) == 1:
				return resolve(attr)
			else:
				return V(resolve(k) for k in attr)
		else:
			return numpy.ndarray.__getattribute__(s, attr)

	def cross(a, b):
		if isinstance(b, V):
			if len(a) != len(b):
				raise TypeError(
				  "cross product not supported for different vector lengths")
			if len(a) != 3:
				raise TypeError(
				  "cross product not supported for non-threedimensional vectors")
			return V(a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
			         a[0] * b[1] - a[1] * b[0])
		else:
			raise TypeError("cannot multiply vector with %s" % type(b))

	def __or__(a, b):
		"""Returns True iff two vectors are collinear or identical"""
		if isinstance(b, V):
			if a.sqr == 0 and b.sqr == 0: return True
			for i in range(len(a)):
				if a[i] == 0:
					if b[i] != 0: return False
					continue
				return (a * (b[i] / a[i]) - b).sqr / (a.sqr + b.sqr) < 1e-6
		return NotImplemented

	@property
	def norm(s):
		return sum(v**2 for v in s)**0.5

	@property
	def sqr(s):
		return sum(v**2 for v in s)

	@property
	def normal(s):
		return s / s.norm


class M(numpy.ndarray):
	"""Augmented subclass of numpy matrices.
	For usability reasons, we added more versatile constructors, getters and methods such as inverse computation."""
	e_key = re.compile("a([1-9])([1-9])|a([1-9][0-9]*)_([1-9][0-9]*)")
	e_rowcol = re.compile("(row|col)([1-9][0-9]*)")
	e_block = re.compile("(a([1-9])([1-9])|a([1-9][0-9]*)_([1-9][0-9]*))"
	                     "_"
	                     "(a([1-9])([1-9])|a([1-9][0-9]*)_([1-9][0-9]*))")

	def __new__(s, *args):

		if len(args) == 1 and isinstance(args[0], numpy.ndarray):
			A = args[0]
			n = len(A)
			m = len(A[0])
			values = list()
			for row in A:
				values += [float(v) for v in row]

			return numpy.ndarray.__new__(s,
			                             shape=(
			                               n,
			                               m,
			                             ),
			                             buffer=numpy.array(values),
			                             dtype=float)

			return numpy.ndarray.__new__(s, args[0])
		if len(args) < 1:
			args = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
		n = len(args)
		m = len(args[0])

		for arg in args:
			if len(arg) != m:
				raise ValueError("matrix rows must have equal length")

		values = []
		for arg in args:
			values += [float(v) for v in arg]

		return numpy.ndarray.__new__(s,
		                             shape=(
		                               n,
		                               m,
		                             ),
		                             buffer=numpy.array(values),
		                             dtype=float)

	def __getattribute__(s, attr):
		m = M.e_key.fullmatch(attr)
		if m:
			g = m.groups()
			i = int(g[0] or g[2])
			j = int(g[1] or g[3])
			return s[i - 1, j - 1]
		m = M.e_block.fullmatch(attr)
		if m:
			g = m.groups()
			return s[int(g[1] or g[3]) - 1:int(g[6] or g[8]),
			         int(g[2] or g[4]) - 1:int(g[7] or g[9])]
		subs = M.e_key.findall(attr)
		if len(subs) > 0:
			return V(s[int(a or c) - 1, int(b or d) - 1] for a, b, c, d in subs)
		m = M.e_rowcol.fullmatch(attr)
		if m:
			g = m.groups()
			if g[0] == "row": return s[int(g[1]) - 1, :]
			else: return s[:, int(g[1]) - 1]
		if V.e_subrange.fullmatch(attr):

			def resolve(key):
				if key == "o": return 1
				elif key == "n": return 0
				else: return s[V.key_dimensions[key]]

			if len(attr) == 1:
				return resolve(attr)
			else:
				return V(resolve(k) for k in attr)
		else:
			return numpy.ndarray.__getattribute__(s, attr)

	@property
	def inverse(s):
		return numpy.linalg.inv(s)

	@classmethod
	def RotationX(cls, a):
		c = cos(a * pi / 180.0)
		s = sin(a * pi / 180.0)
		return M([1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1])

	@classmethod
	def RotationY(cls, a):
		c = cos(a * pi / 180.0)
		s = sin(a * pi / 180.0)
		return M([c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1])

	@classmethod
	def RotationZ(cls, a):
		c = cos(a * pi / 180.0)
		s = sin(a * pi / 180.0)
		return M([c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])

	@classmethod
	def RotationV(cls, a, w):
		c = cos(a * pi / 180.0)
		s = sin(a * pi / 180.0)
		x = w.x
		y = w.y
		z = w.z

		return M([
		  1 + (1 - c) * (x * x - 1), -z * s + (1 - c) * x * y, y * s +
		  (1 - c) * x * z, 0
		], [
		  z * s + (1 - c) * x * y, 1 + (1 - c) * (y * y - 1), -x * s +
		  (1 - c) * y * z, 0
		], [
		  -y * s + (1 - c) * x * z, x * s + (1 - c) * y * z, 1 + (1 - c) *
		  (z * z - 1), 0
		], [0, 0, 0, 1])

	@classmethod
	def Rotation(cls, a, v=None):

		if isinstance(a, Iterable):
			rx, ry, rz = a
			return numpy.dot(M.RotationZ(rz),
			                 numpy.dot(M.RotationY(ry), M.RotationX(rx)))
		elif v is not None:
			return M.RotationV(a, v)
		else:
			return M.RotationZ(a)

	@classmethod
	def Translation(cls, v):
		v = [c for c in v]
		v += [0 for i in range(3 - len(v))]
		return M([1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1])

	@classmethod
	def Scale(cls, v):
		if isinstance(v, Iterable):
			v = [c for c in v]
			v += [1 for i in range(3 - len(v))]
			return M([v[0], 0, 0, 0], [0, v[1], 0, 0], [0, 0, v[2], 0], [0, 0, 0, 1])
		else:
			return M([v, 0, 0, 0], [0, v, 0, 0], [0, 0, v, 0], [0, 0, 0, 1])

	@classmethod
	def Reflection(cls, v):
		x = v[0]
		y = v[1]
		z = v[2]
		return M([1 - 2 * x * x, -2 * x * y, -2 * x * z, 0],
		         [-2 * x * y, 1 - 2 * y * y, -2 * y * z, 0],
		         [-2 * x * z, -2 * y * z, 1 - 2 * z * z, 0], [0, 0, 0, 1])

	@classmethod
	def TransformEz(cls, ez):
		ez = V(ez)
		w0 = ez.normal
		v = V(0, 0, 1).cross(ez)
		u = v.cross(w0)
		v0 = v.normal
		u0 = u.normal

		if ez[0] == 0 and ez[1] == 0:
			if ez[2] > 0:
				m = M([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1])
			else:
				m = M([1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1])
		else:
			m = M([u0[0], v0[0], w0[0], 0], [u0[1], v0[1], w0[1], 0],
			      [u0[2], v0[2], w0[2], 0], [0, 0, 0, 1])
		return m

	@classmethod
	def TransformEzEx(cls, ez, ex):
		ex = V(ex)
		ez = V(ez)
		u0 = ex.normal
		v = ez.cross(ex)
		v0 = v.normal
		w0 = u0.cross(v0)
		m = [[u0[0], v0[0], w0[0], 0], [u0[1], v0[1], w0[1], 0],
		     [u0[2], v0[2], w0[2], 0], [0, 0, 0, 1]]
		return m

	@classmethod
	def Transform(cls, p=None, ex=None, ey=None, ez=None, angs=None):
		if ex is not None: ex = V(ex)
		if ey is not None: ey = V(ey)
		if ez is not None: ez = V(ez)

		hx = ex is not None
		hy = ey is not None
		hz = ez is not None

		if angs is None:
			if False: pass
			elif (hx and hy and hz): res = M.TransformEzEx(ez, ex)
			elif (not hx and hy and hz): res = M.TransformEzEx(ez, ey.cross(ez))
			elif (hx and not hy and hz): res = M.TransformEzEx(ez, ex)
			elif (hx and hy and not hz): res = M.TransformEzEx(ex.cross(ey), ex)
			elif (hx): res = M.Transform(ex=ex, ey=V(0, 0, 1).cross(ex))
			elif (hy): res = M.Transform(ey=ey, ex=ey.cross(V(0, 0, 1)))
			elif (hz and (abs(ez @ V(0, 0, 1)) == ez.norm)): res = M()
			elif (hz): res = M.Transform(ez=ez, ex=ez.cross(V(0, 0, 1)))
			else: res = M()
		else:
			res = M.Rotation(angs)

		if p is not None:
			res = M.Translation(p) @ M
		return res
