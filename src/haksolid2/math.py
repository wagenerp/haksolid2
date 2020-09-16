import re
import numpy
from collections import Iterable, namedtuple
from math import cos, sin, pi, asin, acos
import shlex
import sympy


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

		is_symbolic = False
		for arg in args:
			if isinstance(arg, sympy.core.Expr):
				is_symbolic = True
				break

		if is_symbolic:
			return numpy.ndarray.__new__(s,
			                             shape=(len(args), ),
			                             buffer=numpy.array(
			                               [sympy.core.Mul(1, v) for v in args]),
			                             dtype=sympy.core.Expr)
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

			is_symbolic = False
			for row in A:
				for cell in row:
					if isinstance(cell, sympy.core.Expr):
						is_symbolic = True
						break
				else:
					continue
				break

			if is_symbolic:
				for row in A:
					values += [sympy.core.Mul(1, v) for v in row]

				return numpy.ndarray.__new__(s,
				                             shape=(
				                               n,
				                               m,
				                             ),
				                             buffer=numpy.array(values),
				                             dtype=sympy.core.Expr)
			else:
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

		is_symbolic = False
		for row in args:
			for cell in row:
				if isinstance(cell, sympy.core.Expr):
					is_symbolic = True
					break
			else:
				continue
			break

		for arg in args:
			if len(arg) != m:
				raise ValueError("matrix rows must have equal length")

		values = []

		if is_symbolic:
			for arg in args:
				values += [sympy.core.Mul(1, v) for v in arg]
		else:
			for arg in args:
				values += [float(v) for v in arg]

		return numpy.ndarray.__new__(
		  s,
		  shape=(
		    n,
		    m,
		  ),
		  buffer=numpy.array(values),
		  dtype=sympy.core.Expr if is_symbolic else float)

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
			res = M.Translation(p) @ res
		return res

	@classmethod
	def FromSVGTransform(cls, code):

		e_transformation_arguments = re.compile(r"([0-9.e+-]+)")
		e_transformation_ops = re.compile(r"([a-z]+)\s*\(\s*([^)]*?)\s*\)")

		m = M()

		for op, argstr in e_transformation_ops.findall(code):
			args = tuple(float(v) for v in e_transformation_arguments.findall(argstr))
			if op == "translate":
				m = M.Translation(args) @ m
			elif op == "rotate":
				ang = -args[0] if len(args) > 0 else 0
				x = args[1] if len(args) > 1 else 0
				y = args[2] if len(args) > 2 else 0

				m = M.Translation((x, y)) @ M.RotationZ(ang) @ M.Translation(
				  (-x, -y)) @ m
			elif op == "matrix":
				m = M([
				  [args[0], args[1], 0, args[2]],
				  [args[3], args[4], 0, args[5]],
				  [0, 0, 1, 0],
				  [0, 0, 0, 1],
				]) @ m
			elif op == "scale":
				x = args[0] if len(args) > 0 else 1
				y = args[1] if len(args) > 1 else x
				m = M.Scale((x, y, 1)) @ m

			else:
				raise RuntimeError(f"unsupported transform op: {op}")

		return m

	def toAxisAngle(s):
		R = s[:3, :3]
		axis = V(0, 0, 0)
		dmin = 1e99

		evals, evecs = numpy.linalg.eig(R)

		for i in range(len(evals)):
			v = evals[i]
			vec = evecs[:, i]

			d = abs(v - 1)
			if d < dmin:
				dmin = d
				axis = V(*vec)

		v1 = V(axis.x + 1, axis.y + 2,
		       axis.y + axis.x + axis.z + 3).cross(axis).normal
		v2 = v1.cross(axis)

		v1t = V(*(R @ v1)).normal

		angle = acos(v1 @ v1t) * 180 / pi
		if v2 @ v1t > 0:
			angle = -angle

		return axis, angle


face_t = namedtuple("face_t", "normal vertices")


class FaceSoup:
	def __init__(s):
		s.faces = list()

	def load_stl(s, code):

		INIT = 0
		BODY = 1
		FACET = 2
		LOOP = 3
		state = INIT
		vertices = list()
		normal = None
		for ln in code.splitlines():
			data = shlex.split(ln)
			if len(data) < 1: continue
			if state == INIT:
				if data[0] == "solid":
					state = BODY
				else:
					raise SyntaxError("solid expected")
			elif state == BODY:
				if data[0] == "facet":
					state = FACET
					normal = V(float(v) for v in data[2:5])
				elif data[0] == "endsolid":
					state = INIT
				else:
					raise SyntaxError("facet or endsolid expected")
			elif state == FACET:
				if ln.strip() == "outer loop":
					state = LOOP
					vertices = list()
				elif data[0] == "endfacet":
					state = BODY
				else:
					raise SyntaxError("loop or endfacet expected")
			elif state == LOOP:
				if data[0] == "endloop":
					state = FACET
					s.faces.append(face_t(normal, vertices))
				elif data[0] == "vertex":
					vertices.append(V(float(v) for v in data[1:4]))
				else:
					raise SyntaxError("vertex or endloop expected")

	def load_svg_loops(s, code):
		for stmt in re.findall("<path d=\"(.*?)\".*?/>", code, re.DOTALL):
			vertices = list()
			p = V(0, 0)
			for movop, x, y, endop in re.findall(
			  "([ML])[ \\t]+([0-9.-]+),([0-9.-]+)|(z)", stmt):
				if endop == "z":
					s.faces.append(face_t(V(0, 0, 1), vertices))
					vertices = list()
				elif movop == "M":
					p = V(float(x), -float(y))
				elif movop == "L":
					if len(vertices) < 1: vertices.append(p)
					p = V(float(x), -float(y))
					vertices.append(p)


class aabb_t:
	"""Structure used to represent two or three dimensional axis-aligned bounding boxes.
	In addition to a non-empty bounding box with extent and offset, this type
	can represent *empty* boxes as well as various comparisons and combinations
	of bounding boxes.
	"""
	def __init__(s, min, max):
		if min is None or max is None:
			s.min = None
			s.max = None
		else:
			s.min = V(*min)
			s.max = V(*max)

	@classmethod
	def Empty(cls):
		return aabb_t(None, None)

	@property
	def empty(s):
		return s.min is None or s.max is None

	@property
	def extent(s):
		if s.empty: return V(0, 0, 0)
		return s.max - s.min

	@property
	def center(s):
		if s.empty: return V(0, 0, 0)
		return (s.max + s.min) / 2

	def __str__(s):
		if s.empty:
			return "aabb_t.Empty()"
		else:
			return "aabb_t(%s,%s)" % (s.min, s.max)

	def __eq__(s, b):
		if not isinstance(b, aabb_t):
			raise TypeError("cannot compare %s with %s" % (type(s), type(b)))
		if s.empty() and b.empty():
			return True
		return s.min == b.min and s.max == b.max

	def __add__(s, b):
		"""Returns the union of two bounding boxes, i.e. a new bounding box that encompasses both."""
		if isinstance(b, aabb_t):
			if s.empty: return aabb_t(b.min, b.max)
			if b.empty: return aabb_t(s.min, s.max)
			return aabb_t(V(min(pair) for pair in zip(s.min, b.min)),
			              V(max(pair) for pair in zip(s.max, b.max)))

		elif isinstance(b, Iterable):
			if s.empty: return aabb_t.Empty()
			vec = [v for v in b]
			if len(vec) == 2:
				vec += [0]
			elif len(vec) != 3:
				raise ValueError("oobb offsets must have two or three dimensions")
			return aabb_t(V(*s.min) + V(*vec), V(*s.max) + V(*vec))

		else:
			raise TypeError("cannot add %s to %s" % (type(s), type(b)))

	def __iadd__(s, b):
		"""Enlarges this bounding box to accommodate another"""

		if isinstance(b, aabb_t):
			if s.empty:
				s.min = b.min
				s.max = b.max
			if b.empty: return s
			s.min = V(min(pair) for pair in zip(s.min, b.min))
			s.max = V(max(pair) for pair in zip(s.max, b.max))
			return s

		elif isinstance(b, Iterable):
			if s.empty: return
			vec = [v for v in b]
			if len(vec) == 2:
				vec += [0]
			elif len(vec) != 3:
				raise ValueError("oobb offsets must have two or three dimensions")
			s.min = s.min + V(*vec)
			s.max = s.max + V(*vec)
			return s

		else:
			raise TypeError("cannot add %s to %s" % (type(s), type(b)))

	def __mul__(s, b):
		"""Transforms a bounding box with a given matrix"""
		if isinstance(b, M):
			if s.empty: return aabb_t.Empty()

			base = [s.min, s.max]
			vectors = [
			  numpy.dot(b, V(base[x].x, base[y].y, base[z].z, 1)).xyz for x in (0, 1)
			  for y in (0, 1) for z in (0, 1)
			]

			return aabb_t(V(min(v[k] for v in vectors) for k in range(3)),
			              V(max(v[k] for v in vectors) for k in range(3)))

		else:
			raise TypeError("cannot multiply %s with %s" % (type(s), type(b)))

	def intersection(s, b):
		"""Returns a new bounding box encompassing the intersection of two others."""
		if s.empty or b.empty: return aabb_t.Empty()
		return aabb_t(V(max(pair) for pair in zip(s.min, b.min)),
		              V(min(pair) for pair in zip(s.max, b.max)))
