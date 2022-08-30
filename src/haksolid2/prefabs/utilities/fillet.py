from ... import operations
from ... import dag
from ... import primitives
from ... import usability
from ... import transform


def dioffset(r, segments=None):
	return (operations.offset(-r, round=True, segments=segments) *
	        operations.offset(r, round=True, segments=segments))

@dag.DAGModule
def grow(element):
	with ~operations.minkowski():
		~dag.DAGGroup() * dag.DAGAnchor()
		~element

@dag.DAGModule
def erode(element,diam):
	with ~operations.difference():
		~primitives.cuboid(diam*2)
		with ~grow(element) * operations.difference():
			~primitives.cuboid(diam*4)
			~dag.DAGGroup() * dag.DAGAnchor()

@dag.DAGModule
def closing(element,diam):
	~erode(element,diam)  * grow(element) * dag.DAGAnchor()

@dag.DAGModule
def opening(element,diam):
	~ grow(element) * erode(element,diam) * dag.DAGAnchor()


class FlatFactory:
	def __init__(s):
		pass

	def __call__(s, anchor, size, segments=90, **kwargs):

		return transform.translate(size * anchor) * (
		  transform.translate(-0.5 * size * anchor) * primitives.rect(size) -
		  primitives.circle(r=size, segments=segments, **kwargs))


flatround = usability.BoxAnchorPattern(FlatFactory())
