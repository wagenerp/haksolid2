
class DAGTopologyError(Exception): 
	"""Error thrown if a DAG construction command would yield something that is not a DAG, e.g. circles or appending children to leaf nodes (DAGLeaf)."""
	pass

class DAGContext:
	"""Singleton used to manage __enter__ and __exit__ on DAG nodes for graph construction"""
	class __DAGContext:
		def __init__(s):
			s.stack=[]

	__instance=None
	def __new__(cls):
		if DAGContext.__instance is None:
			DAGContext.__instance=DAGContext.__DAGContext()
		return DAGContext.__instance

	@classmethod
	def Get(cls, context=None):
		return DAGContext()


class DAGVisitor:
	"""Base class of all visitors traversing a DAG."""
	class Abort(BaseException):
		pass
	def __call__(s,node):
		pass
	def descent(s):
		pass
	def ascend(s):
		pass

class DAGBase:
	"""Common base class for DAGNode and DAGNodeConcatenator. As DAGNodeConcatenator must behave like a DAGNode in many circumstances, this functionality is abstracted away in this class."""

	@property
	def node(s):
		raise NotImplementedError()

	def __call__(s):
		return s.node()

	def __enter__(s):
		DAGContext().stack.append(s)
		return s

	def __exit__(s, type, value, tb):
		DAGContext().stack.pop()
	
	def visitDescendants(s,visitor : DAGVisitor):
		s.node.visitDescendants(visitor)
	def visitAncestors(s,visitor : DAGVisitor):
		s.node.visitAncestors(visitor)

	def hasDescendant(s,node):
		class MyVisitor(DAGVisitor):
			def __init__(s,targetNode):
				s.targetNode=targetNode
			def __call__(s,node):
				if node == s.targetNode:
					raise DAGVisitor.Abort()
		
		try:
			s.visitDescendants(MyVisitor(node))
		except DAGVisitor.Abort:
			return True
		return False

	def hasAncestor(s,node):
		class MyVisitor(DAGVisitor):
			def __init__(s,targetNode):
				s.targetNode=targetNode
			def __call__(s,node):
				if node == s.targetNode:
					raise DAGVisitor.Abort()
		
		try:
			s.visitAncestors(MyVisitor(node))
		except DAGVisitor.Abort:
			return True
		return False
	
	def makeModule(s):
		class MyVisitor(DAGVisitor):
			def __init__(s):
				s.anchors=list()
				s.nodes=list()
				s.stack=list()
				s.root=None
			def __call__(s,node):
				s.root=node
				if isinstance(node,DAGAnchor):
					s.anchors.append(node)
					s.stack[-1] = (s.stack[-1][0],True)
			def descent(s):
				s.stack.append((s.root,False))
			def ascend(s):
				node,hasAnchor = s.stack.pop()
				if hasAnchor:
					s.nodes.append(node)
		
		visitor=MyVisitor()
		s.visitDescendants(visitor)

		if len(visitor.nodes)<1:
			return s

		for anchor in visitor.anchors:
			anchor.unlink()
		res=DAGNodeConcatenator(s.node,*visitor.nodes)
		return res



class DAGNodeConcatenator(DAGBase):
	"""Helper class used to realize concatenation of DAG nodes to allow using the expression's result both as a root (to place multiple instances) and as a child anchor (to attach new children to)."""
	def __init__(s,root, *anchors):
		s.root=root
		s.anchors=list(anchors)

	@property
	def node(s):
		return s.root

	def __mul__(s,node):
		if isinstance(node,DAGNode):

			for anchor in s.anchors:
				anchor * node
			return DAGNodeConcatenator(s.root,node)
		elif isinstance(node,DAGNodeConcatenator):

			for anchor in s.anchors:
				anchor * node.root
			return DAGNodeConcatenator(s,*node.anchors)
		else:
			return NotImplemented

class DAGNode(DAGBase):
	"""Base class for all nodes placable in a DAG."""
	def __init__(s):
		s.parents=set()
		s.children=list()

		ctx=DAGContext()
		if len(ctx.stack)>0:
			ctx.stack[-1] * s
		pass

	@property
	def node(s):
		return s

	def __call__(s):
		ctx=DAGContext()
		if len(ctx.stack)>0:
			ctx.stack[-1] * s


	def __mul__(s,node):
		if isinstance(node,DAGNode):

			if node.hasDescendant(s):
				raise DAGTopologyError("circle detected")

			if s not in node.parents:
				s.children.append(node)
				node.parents.add(s)
			
			return DAGNodeConcatenator(s,node)
		elif isinstance(node,DAGNodeConcatenator):
			s.__mul__(node.root)
			return DAGNodeConcatenator(s,*node.anchors)
		else:
			return NotImplemented
	
	def unlink(s):
		for parent in s.parents:
			parent.children.remove(s)
		s.parents.clear()

	def visitDescendants(s,visitor: DAGVisitor):
		res=visitor(s)
		if res is not None and not res:
			return
		visitor.descent()
		for child in s.children:
			child.visitDescendants(visitor)
		visitor.ascend()

	def visitAncestors(s,visitor : DAGVisitor):
		res=visitor(s)
		if res is not None and not res:
			return
		visitor.descent()
		for parent in s.parents:
			parent.visitAncestors(visitor)
		visitor.ascend()


class DAGLeaf(DAGNode):
	"""Abstract DAG node used to create nodes that must not have any children"""
	def __mul__(s,node):
		if isinstance(node,DAGNode):
			raise DAGTopologyError("leaf nodes cannot be extended")
		elif isinstance(node,DAGNodeConcatenator):
			raise DAGTopologyError("leaf nodes cannot be extended")
		else:
			return NotImplemented

class DAGAnchor(DAGLeaf):
	"""Signifies locations within a (sub-)DAG to which new children are to be connected to when used as a module."""
	def __str__(s):
		return "DAGAnchor"

class DAGGroup(DAGNode):
	"""Generic grouping node to be ignored by all visitors."""
	def __str__(s):
		return "DAGGroup"

def DAGModule(func):
	"""Function annotation turning that function into a DAG module that returns an expression usable in DAG construction. Attachments are defined explicitly via DAGAnchors positioned within the function. These anchors are removed after function termination. If no DAGAnchors are present, the DAGModule simply uses its root to append new nodes to."""
	def wrapper(*args, **kwargs):
		root=DAGGroup()
		with root:
			func(*args, **kwargs)
		
		return root.makeModule()

	return wrapper
