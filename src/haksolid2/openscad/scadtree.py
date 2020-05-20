from collections import defaultdict


class SCADNode:
	def __init__(s, ident, args, *children):
		s.ident = ident
		s.args = args
		s.nodes = list(children)

		s.code = ""
		s.surrogate = None

	def __iadd__(s, node):
		s.nodes.append(node)
		return s

	def simplify_combineNodes(s, removeColor=False):

		if removeColor:
			if s.ident == "color":
				s.ident = "union"

		if s.ident == "color":
			removeColor = True

		for node in s.nodes:
			node.simplify_combineNodes()

		if s.ident == "union":
			nodes1 = list()
			for node in s.nodes:
				if node.ident == "union":
					nodes1 += node.nodes
				else:
					nodes1.append(node)
			s.nodes = nodes1

		if s.ident in {
		  "union", "color", "multmatrix", "intersection", "linear_extrude",
		  "rotate_extrude", "projection"
		}:
			s.nodes = list(sorted(s.nodes, key=lambda v: v.code))
		elif s.ident in {"difference"}:
			s.nodes = s.nodes[:1] + list(sorted(s.nodes[1:], key=lambda v: v.code))
		else:
			print("commutates?", s.ident)

	def generateLocalCode(s):
		if s.surrogate is not None:
			s.code = f"{s.surrogate}();"
		else:
			s.code = f"{s.ident}({s.args}){{"
			for n in s.nodes:
				s.code += n.code
			s.code += "}"

	def visit(s):
		yield s
		for n in s.nodes:
			yield from n.visit()

	def visitReverse(s):
		for n in s.nodes:
			yield from n.visitReverse()
		yield s


class SCADModule(SCADNode):
	def __init__(s, ident):
		SCADNode.__init__(s, ident, "")


class SCADFile(SCADNode):
	def __init__(s):
		SCADNode.__init__(s, "", "")

	def build(s):
		for n in s.visitReverse():
			n.generateLocalCode()
		s.code=""
		for n in s.nodes:
			s.code += n.code

	def buildOptimized(s):
		s.simplify_combineNodes()
		usageTracker = defaultdict(lambda: 0)
		surrogateNodes = dict()
		surrogates = dict()

		for n in s.visitReverse():
			n.generateLocalCode()
			usageTracker[n.code] += 1
			surrogateNodes[n.code] = n

		for code, count in usageTracker.items():
			if count < 2: continue
			surrogates[code] = f"grp{len(surrogates) + 1}"

		for n in s.visitReverse():
			if n.code in surrogates:
				n.surrogate = surrogates[n.code]
			n.generateLocalCode()
		s.code = ""
		for code, ident in surrogates.items():
			n = surrogateNodes[code]
			moduleCode = f"module {ident}() {{{''.join(m.code for m in n.nodes)}}}"
			s.code += modules[ident]

		for n in s.nodes:
			s.code += n.code


if __name__=="__main__":
	f=SCADFile()

	f+=SCADNode("union","",SCADNode("union","",SCADNode("union",""),SCADNode("union","")))

	f.build()
	print(f.code)

	f.buildOptimized()
	print(f.code)