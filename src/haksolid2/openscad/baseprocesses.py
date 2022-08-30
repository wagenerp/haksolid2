from .. import dag
from .. import processing
from .. import errors
from .. import metadata
from . import codegen
from ..math import *
import warnings
import time

import os
import subprocess

import tempfile
import shutil
import pathlib
from .cache import SCADCache, DisabledSCADCache, DirectorySCADCache, addOpenSCADCacheArguments, RenderSCADCode


class OpenSCADSource(processing.ProcessBase):
	def __init__(s,
	             useClangFormat=False,
	             layerFilter=None,
	             processPreview=False,
	             useSegmentCount=True,
	             defaultSegments=None,
	             useCache=None,
	             *args,
	             **kwargs):
		processing.ProcessBase.__init__(s, *args, **kwargs)
		s.layerFilter = layerFilter
		s.processPreview = processPreview
		s.useClangFormat = useClangFormat
		s.useSegmentCount = useSegmentCount
		s.defaultSegments = None
		s.useCache = useCache

	def __call__(s, ent: processing.EntityRecord):

		res = processing.ProcessResults()

		visitor = codegen.OpenSCADcodeGen(layerFilter=s.layerFilter,
		                                  processPreview=s.processPreview,
		                                  useSegmentCount=s.useSegmentCount)
		ent.node.visitDescendants(visitor)
		visitor.finish()

		fn_scad = os.path.join(s.getOutputDirectory(True), ent.name + ".scad")
		res.files.append(fn_scad)

		code = visitor.code

		if s.useClangFormat:
			try:
				p = subprocess.Popen(["clang-format", "-style=file"],
				                     stdout=subprocess.PIPE,
				                     stderr=subprocess.PIPE,
				                     stdin=subprocess.PIPE)

				(sout, serr) = p.communicate(code.encode())
				if p.returncode == 0:
					code = sout.decode()
				else:
					warnings.warn(
					  "error processing OpenSCAD code through clang-format: " +
					  serr.decode(), RuntimeWarning)
			except FileNotFoundError as e:
				warnings.warn(
				  "error processing OpenSCAD code through clang-format: " + str(e),
				  RuntimeWarning)

		with open(fn_scad, "w") as f:
			if s.defaultSegments is not None:
				f.write(f"$fn={codegen.scad_repr(s.defaultSegments)};")
			f.write(code)

		return res

	def watch(s,
	          res: processing.ProcessResults) -> processing.ProcessResultViewer:
		if len(res.files) != 1:
			raise errors.UnsupportedFeatureError(
			  "cannot view more than one SCAD file at a time")

		fn = res.files[0]
		fe = os.path.splitext(fn)[1]
		if fe.lower() != ".scad":
			raise ValueError(f"not a scad result: {res}")

		s.useCache, cmdline = addOpenSCADCacheArguments(["openscad", fn],
		                                                s.useCache)
		viewer_process = subprocess.Popen(cmdline)
		return processing.SubprocessResultViewer(viewer_process)


class OpenSCADBuild(processing.ProcessBase):
	def __init__(s,
	             layerFilter=None,
	             processPreview=False,
	             outputFile=True,
	             outputRaw=False,
	             outputGeometry=False,
	             outputFormat=None,
	             useSegmentCount=True,
	             defaultSegments=None,
	             useCache=None,
	             rawCache=False,
	             *args,
	             **kwargs):
		processing.ProcessBase.__init__(s, *args, **kwargs)
		s.layerFilter = layerFilter
		s.processPreview = processPreview
		s.outputFile = outputFile
		s.outputRaw = outputRaw
		s.outputGeometry = outputGeometry
		s.outputFormat = outputFormat
		s.useSegmentCount = useSegmentCount
		s.defaultSegments = None
		s.useCache = useCache
		s.rawCache = rawCache

	@classmethod
	def RenderModule(_, m, silentFail=False, **kwargs):
		subproc = OpenSCADBuild(outputFile=False, outputGeometry=True, **kwargs)
		ent = processing.EntityNode(subproc)
		ent * m
		subent = processing.EntityRecord(processing.EntityNode, ent, "", "",
		                                 subproc)

		try:
			res = processing.buildEntity(subent)
		except RuntimeError:
			if silentFail: return FaceSoup()
			raise

		if not "geometry" in res.data:
			if silentFail: return FaceSoup()
			raise RuntimeError("error retrieving geometry for lasercut layer")

		soup = res.data["geometry"]

		if not isinstance(soup, FaceSoup):
			if silentFail: return FaceSoup()
			raise RuntimeError("unexpected geometry data type")

		return soup

	def __call__(s, ent: processing.EntityRecord):

		res = processing.ProcessResults()

		vcodegen = codegen.OpenSCADcodeGen(layerFilter=s.layerFilter,
		                                   processPreview=s.processPreview,
		                                   useSegmentCount=s.useSegmentCount)
		ent.node.visitDescendants(vcodegen)
		vcodegen.finish()

		vdim = metadata.DimensionVisitor()
		ent.node.visitDescendants(vdim)

		code = ""
		if s.defaultSegments is not None:
			code += (f"$fn={codegen.scad_repr(s.defaultSegments)};")
		code += (vcodegen.code)

		raw = RenderSCADCode(code,
		                     vdim.has3d or vdim.empty,
		                     rawCache=s.rawCache,
		                     useCache=s.useCache,
		                     decode=s.outputGeometry,
		                     outputFormat=s.outputFormat)

		if s.outputGeometry:
			raw_data, res.data["geometry"] = raw
		else:
			raw_data = raw

		if s.outputFormat is not None:
			extension = s.outputFormat
		elif vdim.has3d or vdim.empty:
			extension = ".stl"
		else:
			extension = ".svg"

		if s.outputFile:
			fn_out = os.path.join(s.getOutputDirectory(True), ent.name + extension)
		else:
			fn_out = "out" + extension

		if s.outputFile:
			with open(fn_out, "wb") as f:
				f.write(raw_data)
		if s.outputRaw:
			res.data["raw"] = raw_data

		if s.outputFile:
			res.files.append(fn_out)

		return res
