from collections import defaultdict
from ..math import V


class BoundAttributePattern:
	def __init__(s, target, data):
		s.target = target
		s.data = data

	def __call__(s, *args, **kwargs):
		return s.target(s.data, *args, **kwargs)


class AttributePattern:
	def __init__(s, target):
		s.target = target

	def clone(s):
		return s.__class__(s.target)

	def __call__(s, *args, **kwargs):
		args = list(args)
		kwargs = dict(kwargs)
		s.augmentArguments(args, kwargs)

		return s.target(*args, **kwargs)

	def augmentArguments(s, args, kwargs):
		pass

	def consumePrefix(s, attr):
		pass

	def afterParse(s):
		pass

	def __getattr__(s, attr):
		t = s.clone()

		while len(attr) > 0:
			n = t.consumePrefix(attr)
			if n is None or n <= 0:
				raise AttributeError(f"invalid sequence ({attr}, {n})")
			attr = attr[n:]

		return t


class BoxAnchorPattern(AttributePattern):
	def __init__(s, target, defaultAnchor=V(0, 0, 0)):
		AttributePattern.__init__(s, target)
		s.anchor = V(*defaultAnchor)
		s.setloc = None
		s.loc = defaultdict(lambda: 0)

	def clone(s):
		return BoxAnchorPattern(s.target, s.anchor)

	def augmentArguments(s, args: list, kwargs: dict):
		args.insert(0, s.anchor)

	def consumePrefix(s, attr):
		sym = attr[:1]
		if sym == "c": s.setloc = 0
		elif sym == "n": s.setloc = -1
		elif sym == "p": s.setloc = 1
		elif sym == "x":
			if sym in s.loc: raise AttributeError("duplicate x location")
			if s.setloc is None:
				raise AttributeError("coordinate preceeding location")
			s.anchor[0] = s.setloc
			s.loc[sym] = s.setloc
		elif sym == "y":
			if sym in s.loc: raise AttributeError("duplicate y location")
			if s.setloc is None:
				raise AttributeError("coordinate preceeding location")
			s.anchor[1] = s.setloc
			s.loc[sym] = s.setloc
		elif sym == "z":
			if sym in s.loc: raise AttributeError("duplicate z location")
			if s.setloc is None:
				raise AttributeError("coordinate preceeding location")
			s.anchor[2] = s.setloc
			s.loc[sym] = s.setloc
		else:
			return 0
		return 1


class CylinderAnchorPattern(AttributePattern):
	def __init__(s, target, defaultAnchor=0):
		AttributePattern.__init__(s, target)
		s.anchor = defaultAnchor

	def clone(s):
		return CylinderAnchorPattern(s.target, s.anchor)

	def augmentArguments(s, args: list, kwargs: dict):
		args.insert(0, s.anchor)

	def consumePrefix(s, attr):
		sym = attr[:1]
		if sym == "c": s.anchor = 0
		elif sym == "n": s.anchor = -1
		elif sym == "p": s.anchor = 1
		else:
			return 0
		return 1
