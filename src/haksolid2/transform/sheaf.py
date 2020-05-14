from .. import dag
from .. import usability
from . import affine


@dag.DAGModule
def mirrordup(x, y=None, z=None):

	~dag.DAGAnchor()
	~affine.mirror(x, y, z) * dag.DAGAnchor()

def mirrorquad():
  return mirrordup(1,0,0) * mirrordup(0,1,0)
