from .. import dag
from .. import usability
from .. import transform
from .. import primitives
from ..math import *
from collections import namedtuple


class ExtrusionNode(dag.DAGNode):
	def __init__(s):
		dag.DAGNode.__init__(s)


class LinearExtrude(ExtrusionNode):
	def __init__(s, amount):
		ExtrusionNode.__init__(s)
		s.amount = amount

	def __str__(s):
		return f"{s.__class__.__name__}({s.amount})"


class rotate_extrude(ExtrusionNode):
	def __init__(s, segments=None):
		ExtrusionNode.__init__(s)
		s.segments = segments


class MatrixExtrusionNode(ExtrusionNode):
	def __init__(s):
		ExtrusionNode.__init__(s)

	def matrices(s):
		raise NotImplementedError()
		if False:
			yield None


class matrix_extrude(MatrixExtrusionNode):
	def __init__(s, matrix, steps=1, offset=None):
		MatrixExtrusionNode.__init__(s)
		if offset is None:
			offset = M()

		s._matrix = matrix
		s._steps = steps
		s._offset = offset

	def matrices(s):
		T = s._offset

		for step in range(s._steps):
			yield T
			T = s._matrix @ T
		yield T


class path_extrude(MatrixExtrusionNode):
	def __init__(s, path, protrusion=None):
		MatrixExtrusionNode.__init__(s)

		s._path = path
		s._protrusion = protrusion

	def augment(s, iterator):
		first = True
		m0 = None
		for m in iterator:
			if m is None:
				if not first and s._protrusion is not None: # protrude out the end
					yield M.Translation(m0.col3.xyz.normal * s._protrusion) @ m0
				first = True
				yield m
				continue
			if first:
				first = False
				if s._protrusion is not None:
					yield M.Translation((-s._protrusion) * m.col3.xyz.normal) @ m
			yield m
			m0 = m

		if not first and s._protrusion is not None: # protrude out the end
			yield M.Translation(m0.col3.xyz.normal * s._protrusion) @ m0

	def matrices(s):
		yield from s.augment(s._path.generate())


class CylinderOffsetFactory:
	def __init__(s, primitive):
		s.primitive = primitive

	def __call__(s, anchor, *args, **kwargs):
		node = s.primitive(*args, *kwargs)
		return transform.translate(z=-0.5 * node.amount * anchor) * node


linear_extrude = usability.CylinderAnchorPattern(
  CylinderOffsetFactory(LinearExtrude))

SweepRing = namedtuple("SweepRing", "transform node")


@dag.DAGModule
def sweep(*rings):

	faces = list()
	if True:
		from ..openscad.codegen import NodeToGeometry

		rings = tuple(rings)
		geometries = tuple(NodeToGeometry(ring.node) for ring in rings)

		for geo, ring in zip(geometries, rings):
			if len(geo.faces) != 1:
				raise RuntimeError("cannot sweep non-contiguous geometry")
			geo.transform(ring.transform)
			faces.append(geo.faces[0])

	allVertices = sum((face.vertices for face in faces), tuple())
	allFaces = list()

	O1 = 0

	for face0, face1 in zip(faces, faces[1:]):

		vex0 = face0.vertices
		vex1 = face1.vertices
		n0 = len(vex0)
		n1 = len(vex1)
		O0 = O1
		O1 = O0 + n0

		i0 = 0
		o1 = min(range(len(face1.vertices)), key=lambda i: (vex0[i0] - vex1[i]).sqr)

		i1 = 0

		v0 = vex0[i0]
		v1 = vex1[o1]

		while (i0 <= n0) and (i1 <= n1):
			j0 = i0 % n0
			j1 = (i1 + o1) % n1

			k0 = (j0 + 1) % n0
			k1 = (j1 + 1) % n1

			w0 = vex0[k0]
			w1 = vex1[k1]

			if (w0 - v1).sqr < (v0 - w1).sqr:
				allFaces.append((O0 + j0, O1 + j1, O0 + k0))
				i0 += 1
				v0 = w0
			else:
				allFaces.append((O0 + j0, O1 + j1, O1 + k1))
				i1 += 1
				v1 = w1

	for ring, offset in ((faces[0], 0), (faces[-1], O1)):

		ring = range(offset, offset + len(ring.vertices))
		ring = tuple(reversed(ring)) if offset > 0 else tuple(ring)
		v0 = ring[0]
		v1 = ring[1]
		for i in ring[2:]:
			allFaces.append((v0, v1, i))
			v1 = i

	~primitives.polyhedron(allVertices, allFaces)
