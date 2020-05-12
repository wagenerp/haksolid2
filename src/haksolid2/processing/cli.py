import cli
from . import entities
import re


class entname_t:
	"""Regular expression used to match against entity names"""
	def __init__(s, v):
		s.code = v
		try:
			s.expr = re.compile(v)
		except re.error as e:
			raise TypeError(f"not a valid filter: {v} ({e})")


fBuildAll = cli.Flag("B", "build-all", "build all parts")
lBuildFilters = cli.VariableList(
  entname_t, "b", "build",
  "specify a filter for selecting parts. Processed as a regular expression. Multiple filters are or-ed together."
)

vBuildArrangement = cli.Variable(entname_t, None, "a", "arrange",
                                 "build an arrangement")

partsToBuild = set()
arrangementToBuild = None


def filterEntities(typeFilter, nameFilters=None):
	ents = entities.getEntities()

	for k, v in ents.items():
		if not typeFilter(v.type): continue
		if nameFilters is None:
			yield v
		else:
			for nameFilter in nameFilters:
				if nameFilter.expr.match(k):
					yield v
					break


@cli.help_printer
def help_list_parts(f):

	ents = entities.getEntities()

	for (title, filter) in (
	  ("Parts", lambda v: (v.type is entities.part)),
	  ("Arrangements", lambda v: (v.type is entities.arrangement)),
	  ("Other entities", lambda v: not ((v.type is entities.part) or
	                                    (v.type is entities.arrangement))),
	):
		f.write(title + ":\n")

		count = 0

		for k, v in sorted(ents.items()):
			if not filter(v): continue
			count += 1
			if v.description is not None:
				f.write(f"  {k}:\n    {v.description}\n")
			else:
				f.write(f"  {k}\n")


@cli.check
def check_inputs():
	global partsToBuild, arrangementToBuild

	if True: # extract singular name of an arrangement to build
		if vBuildArrangement.value is not None:
			ents = list(
			  filterEntities(lambda t: t is entities.arrangement,
			                 [vBuildArrangement.value]))
			if len(ents) < 1:
				raise cli.clex(f"no arrangement matches {vBuildArrangement.value.code}")
			if len(ents) > 1:
				raise cli.clex(
				  f"ambiguous arrangement expression: {vBuildArrangement.value.code}")
			arrangementToBuild = ents[0]

	if True: # generate list of parts to build
		partsToBuildDict = dict()
		if fBuildAll:
			for part in filterEntities(lambda t: t is entities.part):
				partsToBuildDict[part.name] = part
		else:
			for part in filterEntities(lambda t: t is entities.part,
			                           lBuildFilters.values):
				partsToBuildDict[part.name] = part
		partsToBuild = list(partsToBuildDict.values())

	if len(partsToBuild) < 1 and arrangementToBuild is None:
		raise cli.clex("nothing to do")


def climain():
	cli.process()

	global partsToBuild, arrangementToBuild

	if arrangementToBuild is not None:
		entities.buildEntity(arrangementToBuild)

	for part in partsToBuild:
		entities.buildEntity(part)
