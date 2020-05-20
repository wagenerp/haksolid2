from ..paradigms import lasercut
from .. import processing
from .. import usability
from .. import metadata
from .. import paradigms
from .. import openscad
from .. import transform
from ..math import *
import os
import subprocess
from collections import namedtuple

ultralaser_job_t = namedtuple("ultralaser_job_t", "T params penetrates soup")


class Ultralaser(lasercut.LasercutProcess):
	def __init__(s,
	             material: paradigms.lasercut.LaserMaterial,
	             contourDepth=None,
	             contourSpeedFactor=0.5,
	             horizontal=True,
	             **kwargs):
		lasercut.LasercutProcess.__init__(s, **kwargs)
		s.horizontal = horizontal
		s.material = material

		if contourDepth is None:
			contourDepth = s.thickness

		s.contourParams = None
		s.contourDepth = contourDepth

		if contourDepth > 0:
			proc = paradigms.lasercut.LasercutLayer(contourDepth,
			                                        speedFactor=contourSpeedFactor)
			s.contourParams = material.computeParams(proc)

	def _processLayer(s, T: M, root, subproc):

		ent = processing.EntityNode(subproc)
		fakeroot = transform.matrix(T)
		ent * fakeroot
		for child in root.node.children:
			fakeroot * child

		subent = processing.EntityRecord(processing.EntityNode, ent, "", "",
		                                 subproc)

		res = processing.buildEntity(subent)

		fakeroot.unlink()
		fakeroot.dropChildren()

		return s._extractSoup(res)

	def _extractSoup(s, res: processing.ProcessResults):

		if not "geometry" in res.data:
			raise RuntimeError("error retrieving geometry for lasercut layer")

		soup = res.data["geometry"]

		if not isinstance(soup, FaceSoup):
			raise RuntimeError("unexpected geometry data type")

		return soup

	def __call__(s, ent: processing.EntityRecord):

		# build a list of tuples (transform, root, soup) of lasercutting subjobs
		jobs = list()

		subproc = openscad.OpenSCADBuild(outputFile=False, outputGeometry=True)

		if True: # add all sub-layers to the mix
			layers = metadata.LayersVisitor(shallow=False)
			ent.node.visitDescendants(layers)

			for T, layer in layers.layers:
				if layer == ent.node: continue
				if not isinstance(layer, paradigms.lasercut.LasercutLayer): continue

				soup = s._processLayer(T, layer, subproc)
				penetrates = layer.node.depth >= s.thickness
				params = s.material.computeParams(layer)

				jobs.append(ultralaser_job_t(T, params, penetrates, soup))

		if s.contourDepth > 0: # add contour to the list
			subent = processing.EntityRecord(processing.EntityNode, ent.node.node, "",
			                                 "", subproc)
			res = processing.buildEntity(subent)
			soup = s._extractSoup(res)
			penetrates = s.contourDepth >= s.thickness

			jobs.append(ultralaser_job_t(M(), s.contourParams, penetrates, soup))
		# soup = s._processLayer(M(), ent.node, subproc)
		# jobs.append((M(), ent.node, soup))

		# extract bounding box and create transformation operator (gen_point) for raw points
		minx, maxx, miny, maxy = 1e30, -1e30, 1e30, -1e30
		for job in jobs:
			for face in job.soup.faces:
				for v in face.vertices:
					minx = min(v.x, minx)
					miny = min(-v.y, miny)
					maxx = max(v.x, maxx)
					maxy = max(-v.y, maxy)

		part_is_horizontal = (maxx - minx > maxy - miny)
		if (part_is_horizontal != s.horizontal):
			gen_point = lambda v: f"{maxy-miny-((-v.y)-miny)} {v.x-minx-(maxx-minx)}"
		else:
			gen_point = lambda v: f"{v.x-minx} {(-v.y)-miny-(maxy-miny)}"

		# start ultralaser process, feed it process and geometry data
		fn_out = os.path.join(s.getOutputDirectory(True), ent.name + ".gcode")
		p = subprocess.Popen(["ultralaser"],
		                     stdin=subprocess.PIPE,
		                     stdout=open(fn_out, "wb"),
		                     stderr=subprocess.PIPE)
		f = p.stdin

		i_process = 0

		for job in jobs:
			i_process += 1

			f.write(
			  f"define_process custom{i_process} feedrate {job.params.feedrate} power {job.params.pwm} {'penetrates' if job.penetrates else ''} end\n"
			  .encode())
			f.write(f"process custom{i_process}\n".encode())

			for face in job.soup.faces:
				if len(face.vertices) < 2:
					continue
				# todo: process filling jobs
				f.write(
				  ("segment %s close\n" % " ".join(gen_point(v)
				                                   for v in face.vertices)).encode())

		f.flush()
		f.close()
		p.wait()

		if p.returncode != 0:
			raise RuntimeError(f"Ultralaser failed: {p.stderr.read().decode()}")

		res = processing.ProcessResults()
		res.files.append(fn_out)

		return res