from .. import dag
from .. import usability
from .. import transform, primitives, operations, usability
from ..math import *
from . import layers


class DimensionVisitor(dag.DAGVisitor):
	def __init__(s):
		dag.DAGVisitor.__init__(s)
		s.has2d = False
		s.has3d = False
		s.has2dTo3d = False
		s.has3dTo2d = False
		s.descendLayers = True

	def __call__(s, node):
		if isinstance(node, layers.DAGLayer):
			return s.descendLayers

		elif isinstance(node, primitives.Primitive2D):
			s.has2d = True
		elif isinstance(node, primitives.Primitive3D):
			s.has3d = True
		elif isinstance(node, operations.ExtrusionNode):
			s.has2dTo3d = True
			s.has3d = True
			return False
		elif isinstance(node, operations.ProjectionNode):
			s.has3dTo2d = True
			s.has2d = True
			return False

	@property
	def empty(s):
		return not (s.has2d or s.has3d)

	@property
	def pure(s):
		return not (s.has2dTo3d or s.has3dTo2d)


class BoundingBoxVisitor(usability.TransformVisitor):
	def __init__(s):
		usability.TransformVisitor.__init__(s)
		s.aabb_stack = list()
		s.aabb_children = list()
		s.aabb_stack.append(list())
		s.node_stack = list()
		s.node = None

	@property
	def aabb(s):
		return s.aabb_stack[0][-1]

	def __call__(s, node):
		usability.TransformVisitor.__call__(s, node)
		s.node = node

	def descent(s):
		usability.TransformVisitor.descent(s)
		s.aabb_stack.append(list())
		s.node_stack.append(s.node)

	def ascend(s):
		usability.TransformVisitor.ascend(s)

		children = s.aabb_stack.pop()
		node = s.node_stack.pop()

		new_aabb = s.reduceChildren(node, children)
		s.aabb_stack[-1].append(new_aabb)

	def reduceChildren(s, node, children):
		if isinstance(node, transform.AffineTransform):
			return sum(children, aabb_t.Empty()) * node.matrix
		elif isinstance(node, transform.untransform):
			raise NotImplementedError(
			  "bounding box computation for untransform nodes is not yet supported")
		elif isinstance(node, transform.retransform):
			raise NotImplementedError(
			  "bounding box computation for retransform nodes is not yet supported")
		elif isinstance(node, primitives.CuboidPrimitive):
			return aabb_t(-0.5 * node.extent, 0.5 * node.extent)

		elif isinstance(node, primitives.SpherePrimitive):
			return aabb_t(-0.5 * node.extent, 0.5 * node.extent)
		elif isinstance(node, primitives.CylinderPrimitive):
			return aabb_t(-0.5 * node.extent, 0.5 * node.extent)

		elif isinstance(node, primitives.RectPrimitive):
			return aabb_t(-0.5 * node.extent, 0.5 * node.extent)
		elif isinstance(node, primitives.CirclePrimitive):
			return aabb_t(-0.5 * node.extent, 0.5 * node.extent)
		elif isinstance(node, primitives.polygon):

			boxMin = list(min(v[k]) for v in node.points for k in (0, 1)) + [0]
			boxMax = list(min(v[k]) for v in node.points for k in (0, 1)) + [0]

			return aabb_t(boxMin, boxMax)

		elif isinstance(node, primitives.text):
			raise NotImplementedError(
			  "bounding box computation for text nodes is not yet supported")

		elif isinstance(node, operations.difference):

			if len(children) < 1: return aabb_t.Empty()
			else: return children[0]
		elif isinstance(node, operations.intersection):

			if len(children) < 1: return aabb_t.Empty()
			else: return children[0]

		elif isinstance(node, operations.minkowski):

			res = aabb_t.Empty()
			for box in children:
				if box.empty: continue
				if res.empty:
					res = box
				else:
					res.min -= box.min
					res.max += box.max

			return res
		elif isinstance(node, operations.offset):
			res = sum(children, aabb_t.Empty())
			res.min -= V(node.offset, node.offset, 0)
			res.max += V(node.offset, node.offset, 0)
			return res
		elif isinstance(node, operations.Hull):
			return sum(children, aabb_t.Empty()) * node.matrix

		elif isinstance(node, operations.LinearExtrude):

			res = sum(children, aabb_t.Empty())
			if not res.empty:
				res.min[2] = -0.5 * node.amount
				res.max[2] = 0.5 * node.amount
			return res
		elif isinstance(node, operations.rotate_extrude):
			res = sum(children, aabb_t.Empty())

			h = res.max.x
			if res.empty: return res
			return aabb_t(V(-h, -h, res.min.y), V(h, h, res.max.y))

		elif isinstance(node, operations.MatrixExtrusionNode):
			raise NotImplementedError(
			  "bounding box computation for matrix extrusion nodes is not yet supported"
			)

		elif isinstance(node, operations.slicePlane):
			res = sum(children, aabb_t.Empty())
			if not res.empty:
				res.min[2] = 0
				res.max[2] = 0
			return res
		elif isinstance(node, operations.projection):
			res = sum(children, aabb_t.Empty())
			if not res.empty:
				res.min[2] = 0
				res.max[2] = 0
			return res

		elif isinstance(node, dag.DAGGroup):
			return sum(children, aabb_t.Empty())
		else:
			raise NotImplementedError(
			  f"bounding box computation for {node} is not yet supported")
