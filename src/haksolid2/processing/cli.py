import cli
from . import entities, customizer
import re
import sys
import pyinotify
import os
import warnings
import queue
import threading
import subprocess


class entname_t:
	"""Regular expression used to match against entity names"""
	def __init__(s, v):
		s.code = v
		try:
			s.expr = re.compile(v)
		except re.error as e:
			raise TypeError(f"not a valid filter: {v} ({e})")


vBuildCustomizer = cli.Variable(
  str, None, "C", "build-customizer",
  "Name of a customizer file from which multiple variants are built")
fBuildAll = cli.Flag("B", "build-all", "build all parts")
lBuildFilters = cli.VariableList(
  entname_t, "b", "build",
  "specify a filter for selecting parts. Processed as a regular expression. Multiple filters are or-ed together."
)

vBuildArrangement = cli.Variable(entname_t, None, "a", "arrange",
                                 "build an arrangement")
fViewArrangement = cli.Flag(
  "v", "view-arrangement",
  "run the arrangement (selected with -a) into a suitable viewer program")
fWatch = cli.Flag(
  "w", "watch",
  "keep running in the background and re-execute when files changed")

partsToBuild = set()
presetsToBuild = set()
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
	global partsToBuild, arrangementToBuild, presetsToBuild

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
		else:
			if fViewArrangement.value:
				raise cli.clex("-v is useless without -a")

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

	if True: # load customizer presets to build
		if vBuildCustomizer.value is not None:
			presetFile = customizer.PresetFile(vBuildCustomizer.value)
			for k, v in presetFile.presets.items():
				presetsToBuild.add((presetFile, k))
		else:
			presetsToBuild.add((None, None))

	if len(partsToBuild) < 1 and arrangementToBuild is None:
		raise cli.clex("nothing to do")


def climain():
	cli.process()

	global partsToBuild, arrangementToBuild, presetsToBuild

	viewer = None

	if arrangementToBuild is not None:
		res = entities.buildEntity(arrangementToBuild)
		if fViewArrangement.value:
			viewer = arrangementToBuild.process.watch(res)

	for presetFile, presetName in presetsToBuild:
		if presetFile is not None:
			presetFile.applyPreset(presetName)
		for part in partsToBuild:
			if presetName is not None:
				part = part.namedCopy(f"{part.name}-{presetName}")
			entities.buildEntity(part)

	if fWatch.value:

		# list files we need to watch for changes
		watchlist = list()
		mgr = pyinotify.WatchManager()
		for mod in sys.modules.values():
			if not hasattr(mod, "__file__"): continue
			if mod.__file__ is None: continue
			fn = os.path.realpath(mod.__file__)
			if not os.path.exists(fn):
				warnings.warn(
				  f"cannot watch for changes in module {mod.__name__}: file could not be located\n"
				)
				continue

			if not os.access(fn, os.W_OK): continue
			watchlist.append(fn)
			mgr.add_watch(fn, pyinotify.IN_MODIFY)

		new_cmdline = [sys.executable] + [
		  v for v in sys.argv
		  if v not in {"-w", "--watch", "-v", "--view-arrangement"}
		]

		# go multithreaded:
		#  - create and wait for viewer process (if an arrangement is created)
		#  - wait for modification notifications
		evq = queue.Queue()
		EV_MODIFY = 1
		EV_TERMINATE = 2

		class EventHandler(pyinotify.ProcessEvent):
			def process_IN_MODIFY(s, ev):
				evq.put(EV_MODIFY)

		def thrdf_viewer():

			# todo: get file name from actual method call above
			viewer.wait()
			evq.put(EV_TERMINATE)

		def thrdf_inotify():

			handler = EventHandler()
			notifier = pyinotify.Notifier(mgr, handler)
			notifier.loop()
			thrd_inotify = threading.Thread(target=notifier.loop)
			thrd_inotify.start()
			evq.put(EV_TERMINATE)

		if viewer is not None:
			threading.Thread(target=thrdf_viewer, daemon=True).start()
		threading.Thread(target=thrdf_inotify, daemon=True).start()

		# process events coming from threads above
		while True:
			ev = evq.get()
			if ev == EV_TERMINATE: break
			elif ev == EV_MODIFY:
				subprocess.run(new_cmdline)
