from ... import operations
from ... import dag


def dioffset(r, segments=None):
	return (operations.offset(-r, round=True, segments=segments) *
	        operations.offset(r, round=True, segments=segments))
