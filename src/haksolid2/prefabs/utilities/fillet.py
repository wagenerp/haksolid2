from ... import operations
from ... import dag
from ... import primitives
from ... import usability
from ... import transform


def dioffset(r, segments=None):
	return (operations.offset(-r, round=True, segments=segments) *
	        operations.offset(r, round=True, segments=segments))


class FlatFactory:
	def __init__(s):
		pass

	def __call__(s, anchor, size, segments=90, **kwargs):

		return transform.translate(size * anchor) * (
		  transform.translate(-0.5 * size * anchor) * primitives.rect(size) -
		  primitives.circle(r=size, segments=segments, **kwargs))


flatround = usability.BoxAnchorPattern(FlatFactory())
