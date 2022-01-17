from .. import dag


class Hint(dag.DAGGroup):
	def __init__(s):
		dag.DAGGroup.__init__(s)


class hint_cache(Hint):
	pass
