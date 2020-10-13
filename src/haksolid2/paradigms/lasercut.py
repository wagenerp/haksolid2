from .. import dag
from .. import metadata
from .. import operations
from .. import processing
from collections import namedtuple

laser_params_t = namedtuple("laser_params_t",
                            "feedrate pwm current keyvalues",
                            defaults=(None, ))


class LasercutProcess(processing.ProcessBase):
	def __init__(s, thickness=4, **kwargs):
		processing.ProcessBase.__init__(s, **kwargs)
		s.thickness = thickness

	def __str__(s):
		return f"Lasercut({s.thickness})"


class LasercutLayer(metadata.SubprocessLayer):
	TraceContour = "trace.contour"
	FillZigZag = "fill.zigZag"

	def __init__(s, depth, mode=TraceContour, speedFactor=0.5):
		metadata.SubprocessLayer.__init__(s)
		s.depth = depth
		s.mode = mode
		s.speedFactor = speedFactor

	def __str__(s):
		return f"LasercutLaser({s.mode} {s.depth} {s.speedFactor*100}%)"


@dag.DAGModule
def engrave(depth, speedFactor=0.5):
	~LasercutLayer(depth, LasercutLayer.FillZigZag, speedFactor) * dag.DAGAnchor()


@dag.DAGModule
def trace(depth, speedFactor=0.5):
	~LasercutLayer(depth, LasercutLayer.TraceContour,
	               speedFactor) * dag.DAGAnchor()


class LaserMaterial:
	def computeParams(s, p: LasercutLayer) -> laser_params_t:
		raise NotImplementedError()


class ConstantLaserMaterial(LaserMaterial):
	def __init__(s, feedrate, pwm, current, **kwargs):
		LaserMaterial.__init__(s)
		s._params = laser_params_t(feedrate, pwm, current, dict(kwargs))

	def computeParams(s, p: LasercutLayer) -> laser_params_t:
		return s._params


class ConstantPowerLaserMaterial(LaserMaterial):
	def __init__(s, depthMin, depthMax, feedrateFunc, current, pwm=1, **kwargs):
		LaserMaterial.__init__(s)
		s.depthMin = depthMin
		s.depthMax = depthMax
		s.feedrateFunc = feedrateFunc
		s.current = current
		s.pwm = pwm
		s._keyvalues = dict(kwargs)

	def computeParams(s, p: LasercutLayer) -> laser_params_t:

		if p.depth > s.depthMax:
			raise RuntimeError(
			  f"unachievable laser depth: {p.depth} > depthMax = {s.depthMax}")
		if p.depth < s.depthMin:
			raise RuntimeError(
			  f"unachievable laser depth: {p.depth} < depthMin = {s.depthMin}")
		return laser_params_t(s.feedrateFunc(p.depth), s.pwm, s.current,
		                      dict(s._keyvalues))
