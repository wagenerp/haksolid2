from collections import defaultdict
from ..math import V


class BoundAttributePattern:
	def __init__(s, target, data):
		s.target = target
		s.data = data

	def __call__(s, *args, **kwargs):
		return s.target(s.data, *args, **kwargs)


class BoxAnchorPattern:
	def __init__(s, target):
		s.target = target

	def __call__(s, *args, **kwargs):
		return s.target(V(0,0,0), *args, **kwargs)

	def __getattr__(s, attr):

		setloc = None
		loc = defaultdict(lambda: 0)

		for sym in attr:
			if sym == "c": setloc = 0
			elif sym == "n": setloc = -1
			elif sym == "p": setloc = 1
			elif sym == "x":
				if sym in loc: raise AttributeError("duplicate x location")
				if setloc is None:
					raise AttributeError("coordinate preceeding location")
				loc[sym] = setloc
			elif sym == "y":
				if sym in loc: raise AttributeError("duplicate y location")
				if setloc is None:
					raise AttributeError("coordinate preceeding location")
				loc[sym] = setloc
			elif sym == "z":
				if sym in loc: raise AttributeError("duplicate z location")
				if setloc is None:
					raise AttributeError("coordinate preceeding location")
				loc[sym] = setloc
			else:
				raise AttributeError("invalid sequence")

		return BoundAttributePattern(s.target, V(loc["x"], loc["y"], loc["z"]))

class CylinderAnchorPattern:
	def __init__(s, target):
		s.target = target

	def __call__(s, *args, **kwargs):
		return s.target(0, *args, **kwargs)

	def __getattr__(s, attr):

		loc = None

		for sym in attr:
			if sym == "c": loc = 0
			elif sym == "n": loc = -1
			elif sym == "p": loc = 1
			else:
				raise AttributeError("invalid sequence")

		return BoundAttributePattern(s.target, V(loc["x"], loc["y"], loc["z"]))