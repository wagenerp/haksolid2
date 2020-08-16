from ..math import *
from .. import dag
from .. import primitives
from .. import transform
from .. import metadata
from collections import namedtuple, defaultdict
import math
import slvs

edge_t = namedtuple("edge_t", "angle length")
attachment_t = namedtuple("attachment_t", "partner partnerEdge dihedral")


@dag.DAGModule
def triad():
	~metadata.color((1, 0, 0)) * primitives.cuboid.nx(10, 1, 1)
	~metadata.color((0, 1, 0)) * primitives.cuboid.ny(1, 10, 1)
	~metadata.color((0, 0, 1)) * primitives.cuboid.nz(1, 1, 10)


class Vertex:
	IDHigh = 0

	def __init__(s):
		global ASDF
		s.index = Vertex.IDHigh
		Vertex.IDHigh += 1
		s.polygons = set()
		s.references = list()

		s.pos = V(0, 0, 0)

	def attach(s, polygon):
		if polygon in s.polygons: return
		s.polygons.add(polygon)

	def solve(s):

		n = len(s.polygons)
		print(f"solving vertex with {n} faces")
		polygonList = list()
		polygonVertexIndices = list()

		if True: # build ordered list of polygons (adjacent to one another)
			openSet = set(s.polygons)
			item = openSet.pop()
			polygonList.append(item)
			while len(openSet) > 0:
				for next in openSet:
					if item.isAttachedTo(next):
						item = next
						openSet.remove(item)
						polygonList.append(item)
						break
				else:
					raise RuntimeError("incomplete vertex")

		if True: # find vertices that connect adjacent (prev,this,next) polygons
			for ipoly, poly in enumerate(polygonList):
				inext = (ipoly + 1) % n
				# iprev = (ipoly + n - 1) % n
				next = polygonList[inext]
				# prev = polygonList[iprev]

				ivertex = poly.vertexIndex(s)
				if poly._attachments[ivertex].partner == next:
					polygonVertexIndices.append((ivertex + 1, ivertex, ivertex - 1))
				else:
					polygonVertexIndices.append((ivertex - 1, ivertex, ivertex + 1))

		sss = slvs.System()

		points = list()
		points.append(sss.point(0, 0, 0)) # us

		for i in range(n):
			points.append(sss.point(*V.Cylinder(i * 360 / n, 10, 10)))

		print("  constraints")
		for i in range(n):
			poly = polygonList[i]
			iprev, ithis, inext = polygonVertexIndices[i]
			pprev = (poly.edgeTransform(iprev) @ V(0, 0, 0, 1)).xyz
			pthis = (poly.edgeTransform(ithis) @ V(0, 0, 0, 1)).xyz
			pnext = (poly.edgeTransform(inext) @ V(0, 0, 0, 1)).xyz
			# central vertex <-> vertex i
			dist = (pthis - pprev).norm
			sss.constrain(slvs.SLVS_C_PT_PT_DISTANCE,
			              ptA=points[0],
			              ptB=points[i + 1],
			              valA=dist)
			print(f"    c-{i}: {dist:7.3}")
			# vertex i <-> vertex i+1
			dist = (pnext - pprev).norm
			sss.constrain(slvs.SLVS_C_PT_PT_DISTANCE,
			              ptA=points[i + 1],
			              ptB=points[((i + 1) % n) + 1],
			              valA=dist)
			print(f"    {i}-{i+1}: {dist:7.3}")

		sss.build()
		sss.solve()

		print("  coordinates")
		coords = list()
		for i in range(n + 1):
			coords.append(
			  V(sss.param[points[i].param[0] - 1].val,
			    sss.param[points[i].param[1] - 1].val,
			    sss.param[points[i].param[2] - 1].val))
			print(f"    V({coords[-1].x},{coords[-1].y},{coords[-1].z}),")

		print("  normals")
		normals = list()
		for i in range(n):
			j = (i + 1) % n
			normals.append(
			  ((coords[i + 1] - coords[0]).cross(coords[j + 1] - coords[0])).normal)

			print(f"    {normals[-1]}")

		dihedralAngles = list()
		for i in range(n):
			j = (i + 1) % n

			angleAbs = 180 - math.acos(normals[i] @ normals[j]) * 180 / math.pi
			dihedralAngles.append(angleAbs)
			print(f"  dihedral angle {i} to {i+1}: {angleAbs:7.3f}")
			polygonList[i].setDihedralAngle(polygonList[j], angleAbs)

	def merge(s, b):
		if b == s: return s

		for p in b.polygons:
			s.attach(p)
		s.references += b.references

		return s


class VertexReference:
	def __init__(s, owner):
		s.owner = owner
		s.instance = Vertex()
		s.instance.attach(owner)
		s.instance.references.append(s)

	def merge(s, b):

		s.instance.merge(b.instance)
		for ref in s.instance.references:
			ref.instance = s.instance

	def __eq__(s, b):
		if isinstance(b, VertexReference):
			return s.instance == b.instance
		if isinstance(b, Vertex):
			return s.instance == b

		return NotImplemented


class Polygon:
	IDHigh = 0

	def __init__(s, *edges):
		pos = V(0, 0)
		angle = 0

		s.index = Polygon.IDHigh
		Polygon.IDHigh += 1

		s._edges = list()
		s._attachments = dict()
		s._vertices = list()

		for edge in edges:
			pos += V.Cylinder(angle, edge.length).xy
			s._edges.append(edge_t(edge.angle, edge.length))
			angle += edge.angle

			s._vertices.append(VertexReference(s))

		if (pos @ pos) > edges[0].length * 1e-5:
			raise ValueError(f"not a closed polygon, deviation {pos@pos}")

	def __str__(s):
		return f"poly-{s.index:03}"

	def edge(s, index):
		n = s.n
		index = ((index % n) + n) % n
		return s._edges[index]

	@classmethod
	def Regular(s, side, n):
		edge = edge_t(360 / n, side)
		return Polygon(*(edge for i in range(n)))

	@property
	def n(s):
		return len(s._edges)

	def vertex(s, index):
		n = s.n
		index = ((index % n) + n) % n
		return s._vertices[index]

	def vertexIndex(s, vertex):
		for i, v in enumerate(s._vertices):
			if v == vertex:
				return i
		raise KeyError(f"vertex {vertex} not part of polygon {s}")

	def edgeIndex(s, v0, v1):
		i0 = s.vertexIndex(v0)
		i1 = s.vertexIndex(v1)
		n = s.n
		if (i0 + 1 == n) and (i1 == 0): return i0
		if (i1 + 1 == n) and (i0 == 0): return i1
		return min(i0, i1)

	@property
	def normal(s):
		a = (s._vertices[1].instance.pos - s._vertices[0].instance.pos)
		b = (s._vertices[2].instance.pos - s._vertices[0].instance.pos)
		return a.cross(b).normal

	def attachment(s, edge):
		n = s.n
		edge = ((edge % n) + n) % n
		return s._attachments[edge]

	def attach(s, edge: int, partner, partnerEdge: int = 0, dihedral: float = 0):
		if not isinstance(partner, Polygon):
			raise TypeError(f"{partner} is not a polygon")
		n = s.n
		edge = ((edge % n) + n) % n

		m = partner.n
		partnerEdge = ((partnerEdge % m) + m) % m

		if edge in s._attachments:
			raise RuntimeError(f"edge {edge} is already attached to something")
		if partnerEdge in partner._attachments:
			raise RuntimeError(
			  f"partner's edge {partnerEdge} is already attached to something")

		s._attachments[edge] = attachment_t(partner, partnerEdge, dihedral)
		partner._attachments[partnerEdge] = attachment_t(s, edge, dihedral)

		s.vertex(edge).merge(partner.vertex(partnerEdge + 1))
		s.vertex(edge + 1).merge(partner.vertex(partnerEdge))

		return partner

	def setDihedralAngle(s, partner, angle):
		for edge, a in s._attachments.items():
			if a.partner != partner: continue

			s._attachments[edge] = attachment_t(a.partner, a.partnerEdge, angle)
			a.partner._attachments[a.partnerEdge] = attachment_t(s, edge, angle)
			return

		raise KeyError(f"edge {partner} is not adjacent to {s}")

	def isAttachedTo(s, partner):
		for a in s._attachments.values():
			if a.partner == partner:
				return True
		return False

	def edgeTransform(s, edge):

		n = len(s._edges)
		edge = ((edge % n) + n) % n

		if edge < 0 or edge >= n:
			raise IndexError(f"invalid edge index for {len(s._edges)}-gon: {edge}")

		T = M()
		for i in range(edge):
			T = (M.Translation(V(s._edges[i].length, 0, 0)) @ M.RotationZ(
			  s._edges[i].angle) @ T)

		return T

	def attachmentEdgeTransform(s, edge, planar=True):

		n = len(s._edges)
		edge = ((edge % n) + n) % n

		T = s.edgeTransform(edge) @ M.Translation(V(s._edges[edge].length, 0,
		                                            0)) @ M.RotationZ(180)

		if not planar:
			T = T @ M.RotationX(180 - s._attachments[edge].dihedral)

		return T

	def allPolygons(s, baseEdge=0):
		closedSet = set()
		openSet = list()

		node_t = namedtuple("node_t",
		                    "polygon transformNet transformShape baseEdge")
		openSet.append(node_t(s, M(), M(), baseEdge))
		while len(openSet) > 0:
			node = openSet.pop()
			p, TN, TS, edge = node
			if p in closedSet: continue
			closedSet.add(p)

			yield node

			TN = TN @ p.edgeTransform(edge).inverse
			TS = TS @ p.edgeTransform(edge).inverse

			for edge1, a in p._attachments.items():
				if a.partner in closedSet: continue
				openSet.append(
				  node_t(a.partner, TN @ p.attachmentEdgeTransform(edge1, True),
				         TS @ p.attachmentEdgeTransform(edge1, False), a.partnerEdge))

	def shapeVertices(s):
		vertices = set()
		for node in s.allPolygons():
			for v in node.polygon._vertices:
				vertices.add(v.instance)
		return vertices

	@property
	def closed(s):
		return len(s._attachments) == len(s._edges)

	@property
	def shapeClosed(s):
		for node in s.allPolygons():
			if not node.polygon.closed:
				return False
		return True

	def computeDihedralAngles(s):
		for vertex in s.shapeVertices():
			vertex.solve()
			pass

	def localVertices(s, baseEdge=0):
		pos = V(0, 0)
		angle = 0
		n = len(s._edges)
		for i in range(n):
			yield V(pos)
			edge = s._edges[(i + baseEdge) % n]
			pos += V.Cylinder(angle, edge.length).xy
			angle += edge.angle

	@dag.DAGModule
	def mod_polygon(s, baseEdge=0):
		~primitives.polygon(points=[*s.localVertices(baseEdge)])

	def net(s, baseEdge=0):
		closedSet = set()
		openSet = list()

		node_t = namedtuple("node_t", "polygon transform baseEdge")
		openSet.append(node_t(s, M(), baseEdge))
		while len(openSet) > 0:
			p, T, edge = openSet.pop()
			if p in closedSet: continue
			closedSet.add(p)

			yield T, p, edge

			T = T @ p.edgeTransform(edge).inverse

			for edge1, a in p._attachments.items():
				if a.partner in closedSet: continue
				openSet.append(
				  node_t(a.partner, T @ p.attachmentEdgeTransform(edge1),
				         a.partnerEdge))

	def refineShape(s, threshold=1e-5, verbose=True):
		# unify overlapping vertices

		closedSet = set()
		vertices = list()

		if True: # compute vertex positions
			if verbose: print("compute vertex positions")
			for node in s.allPolygons():
				p = node.polygon
				T = node.transformShape @ p.edgeTransform(node.baseEdge).inverse
				for i in range(p.n):
					v = p.vertex(i)
					v.instance.pos = (T @ p.edgeTransform(i) @ V(0, 0, 0, 1)).xyz

					if not v.instance in closedSet:
						closedSet.add(v.instance)
						vertices.append(v)

		if True: # unify vertices
			if verbose: print("unify vertices")
			for iv, v in enumerate(vertices):
				for w in vertices[iv + 1:]:
					if (v.instance.pos - w.instance.pos).norm < threshold:
						v.merge(w)

		if True: # remove duplicate faces
			if verbose: print("remove duplicate faces")

			polygons = dict() # polygonKey -> polygon
			edges = defaultdict(
			  lambda: set()) # sorted(vertexID,vertexID) -> set(polygonKey)
			idVertices = dict()
			n_total = 0

			# build polygons, edges and idVertices to attain a new shape
			for node in s.allPolygons():
				p = node.polygon
				n_total += 1
				key = tuple(sorted(v.instance.index for v in p._vertices))

				for i in range(p.n):
					edgeKey = tuple(
					  sorted(
					    (p.vertex(i).instance.index, p.vertex(i + 1).instance.index)))
					edges[edgeKey].add(key)
					idVertices[p.vertex(i).instance.index] = p.vertex(i).instance

					if len(edges[edgeKey]) > 2:
						raise RuntimeError("overburdened edge")

				if key in polygons:
					# todo: replace attachments
					pass
				else:
					polygons[key] = p

			# strip all attachments
			for v in idVertices.values():
				v.polygons.clear()
				v.references.clear()

			for p in polygons.values():
				p._attachments.clear()
				for v in p._vertices:
					v.instance.attach(p)
					v.instance.references.append(v)

			if True: # re-solve geometry
				sss = slvs.System()
				idPoints = dict()
				for k, v in idVertices.items():
					idPoints[k] = sss.point(v.pos.x, v.pos.y, v.pos.z)

				for vids, polys in edges.items():
					if len(polys) < 1: continue
					v0, v1 = (idVertices[k] for k in vids)
					for p in polys:
						p = polygons[p]
						edge = p.edgeIndex(v0, v1)

						sss.constrain(slvs.SLVS_C_PT_PT_DISTANCE,
						              ptA=idPoints[vids[0]],
						              ptB=idPoints[vids[1]],
						              valA=p._edges[edge].length)
						break

				sss.build()
				sss.solve()

				for k, v in idVertices.items():
					v.pos = V(sss.param[idPoints[k].param[0] - 1].val,
					          sss.param[idPoints[k].param[1] - 1].val,
					          sss.param[idPoints[k].param[2] - 1].val)

			# recreate all edge attachments
			dihedrals = set()
			for vids, polys in edges.items():
				if len(polys) != 2: continue
				a, b = (polygons[k] for k in sorted(polys))

				v0, v1 = (idVertices[k] for k in vids)

				edgea = a.edgeIndex(v0, v1)
				edgeb = b.edgeIndex(v0, v1)

				dihedral = math.acos(a.normal @ b.normal) * 180 / math.pi

				if (a.vertex(edgea + 2).instance.pos - v0.pos) @ b.normal < 0:
					dihedral = 180 + dihedral
				else:
					dihedral = 180 - dihedral

				dihedrals.add(int(dihedral * 100))
				# dihedral = 180 - math.acos(a.normal @ b.normal) * 180 / math.pi

				a.attach(edgea, b, edgeb, dihedral=dihedral)

			if verbose:
				print(f"  solution:")
				print(f"    dof: {sss.dof}")
				print(f"    failed: {sss.failed}")
				print(f"    calculateFaileds: {sss.calculateFaileds}")
				print(f"    result: {sss.result}")
				print(f"  faces: {len(polygons)}")
				print(f"  edges: {len(edges)}")
				print(f"  vertices: {len(idVertices)}")
				print(f"  closed: {s.shapeClosed}")
				print(f"  dihedrals: {len(dihedrals)}")
				# for dihedral in sorted(dihedrals):
				# 	print(f"    {dihedral*0.01:7.3f}")
