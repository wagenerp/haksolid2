
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

	Adapters = list()

	@property
	def node(s):
		raise NotImplementedError()

	def __str__(s):
		return s.__class__.__name__
		
	def __call__(s):
		return s.node()

	def __enter__(s):
		DAGContext().stack.append(s)
		return s

	def __exit__(s, type, value, tb):
		DAGContext().stack.pop()

	def runAdapter(s,attr,*args,**kwargs):

		for adapter in DAGBase.Adapters:
			if not hasattr(adapter,attr): continue

			res = getattr(adapter,attr)(*args,**kwargs)
			if res is not NotImplemented:
				return res
		return NotImplemented
	
	def __add__(s,b):
		return s.runAdapter("__add__",s,b)
	def __sub__(s,b):
		return s.runAdapter("__sub__",s,b)
	def __matmul__(s,b):
		return s.runAdapter("__matmul__",s,b)
	def __truediv__(s,b):
		return s.runAdapter("__truediv__",s,b)
	def __floordiv__(s,b):
		return s.runAdapter("__floordiv__",s,b)
	def __mod__(s,b):
		return s.runAdapter("__mod__",s,b)
	def __divmod__(s,b):
		return s.runAdapter("__divmod__",s,b)
	def __pow__(s,b):
		return s.runAdapter("__pow__",s,b)
	def __lshift__(s,b):
		return s.runAdapter("__lshift__",s,b)
	def __rshift__(s,b):
		return s.runAdapter("__rshift__",s,b)
	def __and__(s,b):
		return s.runAdapter("__and__",s,b)
	def __xor__(s,b):
		return s.runAdapter("__xor__",s,b)
	def __or__(s,b):
		return s.runAdapter("__or__",s,b)

	def __radd__(s,b):
		return s.runAdapter("__radd__",s,b)
	def __rsub__(s,b):
		return s.runAdapter("__rsub__",s,b)
	def __rmatmul__(s,b):
		return s.runAdapter("__rmatmul__",s,b)
	def __rtruediv__(s,b):
		return s.runAdapter("__rtruediv__",s,b)
	def __rfloordiv__(s,b):
		return s.runAdapter("__rfloordiv__",s,b)
	def __rmod__(s,b):
		return s.runAdapter("__rmod__",s,b)
	def __rdivmod__(s,b):
		return s.runAdapter("__rdivmod__",s,b)
	def __rpow__(s,b):
		return s.runAdapter("__rpow__",s,b)
	def __rlshift__(s,b):
		return s.runAdapter("__rlshift__",s,b)
	def __rrshift__(s,b):
		return s.runAdapter("__rrshift__",s,b)
	def __rand__(s,b):
		return s.runAdapter("__rand__",s,b)
	def __rxor__(s,b):
		return s.runAdapter("__rxor__",s,b)
	def __ror__(s,b):
		return s.runAdapter("__ror__",s,b)

	def __iadd__(s,b):
		return s.runAdapter("__iadd__",s,b)
	def __isub__(s,b):
		return s.runAdapter("__isub__",s,b)
	def __imatmul__(s,b):
		return s.runAdapter("__imatmul__",s,b)
	def __itruediv__(s,b):
		return s.runAdapter("__itruediv__",s,b)
	def __ifloordiv__(s,b):
		return s.runAdapter("__ifloordiv__",s,b)
	def __imod__(s,b):
		return s.runAdapter("__imod__",s,b)
	def __idivmod__(s,b):
		return s.runAdapter("__idivmod__",s,b)
	def __ipow__(s,b):
		return s.runAdapter("__ipow__",s,b)
	def __ilshift__(s,b):
		return s.runAdapter("__ilshift__",s,b)
	def __irshift__(s,b):
		return s.runAdapter("__irshift__",s,b)
	def __iand__(s,b):
		return s.runAdapter("__iand__",s,b)
	def __ixor__(s,b):
		return s.runAdapter("__ixor__",s,b)
	def __ior__(s,b):
		return s.runAdapter("__ior__",s,b)
	
	def __neg__(s):
		return s.runAdapter("__neg__",s)
	def __pos__(s):
		return s.runAdapter("__pos__",s)

	def __invert__(s):

		ctx=DAGContext()
		if len(ctx.stack)>0:
			ctx.stack[-1] * s
		return s
	
	
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

def DAGAdapter(cls):
	DAGBase.Adapters.append(cls)
	return cls


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
	
	def emplace(s,node):
		node.unlink()
		for parent in s.parents:
			parent * node
		s.unlink()
		node * s

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
		root=DAGGroup() * DAGGroup()
		with root:
			func(*args, **kwargs)
		
		return root.makeModule()

	return wrapper
