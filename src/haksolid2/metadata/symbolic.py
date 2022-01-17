from .. import dag
from ..math import *

_GlobalDefaults = dict()


class variable(dag.DAGLeaf):
	def __init__(s,
	             ident: str,
	             default: any,
	             description: str = None,
	             domain: str = None,
	             group: str = None):

		s.ident = ident
		s._default = default
		s.description = description
		s.domain = domain
		s.group = group

		s.symbol = sympy.Symbol(f"_{ident}_actual")
		# sympy.Symbol.__init__(s,ident)
		dag.DAGLeaf.__init__(s)



	@classmethod
	def SetGlobalDefault(cls, key: str, value: any):
		_GlobalDefaults[key] = value

	@property
	def default(s):
		if s.ident in _GlobalDefaults:
			return type(s._default)(_GlobalDefaults[s.ident])
		else:
			return s._default
	
	
	def __str__(s):
		return f"variable({s.ident})"

	def __invert__(s):

		dag.DAGLeaf.__invert__(s)
		return s.symbol

	@property
	def isBool(s):
		return type(s.default) == bool


class conditional(dag.DAGNode):
	def __init__(s, expr):
		s.expr = expr

		dag.DAGNode.__init__(s)


class runtime_assertion(dag.DAGLeaf):
	def __init__(s, expr, message):
		s.expr = expr
		s.message = message

		dag.DAGLeaf.__init__(s)
