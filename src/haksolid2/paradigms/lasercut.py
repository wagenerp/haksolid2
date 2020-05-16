from .. import dag
from .. import metadata
from .. import operations
from .. import processing


class LasercutProcess(processing.ProcessBase):
	def __init__(s, thickness=4, **kwargs):
		processing.ProcessBase.__init__(s, **kwargs)
		s.thickness = thickness

	def __str__(s):
		return f"Lasercut({s.thickness}"


class LasercutLayer(metadata.SubprocessLayer):
	TraceContour = 0
	FillZigZag = 1

	def __init__(s, depth, mode=TraceContour, speedFactor=0.5):
		metadata.SubprocessLayer.__init__(s)
		s.depth = depth
		s.mode = mode
		s.speedFactor = speedFactor


@dag.DAGModule
def engrave(depth, speedFactor=0.5):
	~LasercutLayer(depth, LasercutLayer.FillZigZag, speedFactor) * dag.DAGAnchor()


@dag.DAGModule
def trace(depth, speedFactor=0.5):
	~LasercutLayer(depth, LasercutLayer.TraceContour,
	               speedFactor) * dag.DAGAnchor()
