from .. import dag
from .. import processing
from .. import errors
from .. import metadata
from . import codegen
from ..math import *
import warnings

import os
import subprocess

import tempfile
import shutil


class OpenSCADSource(processing.ProcessBase):
	def __init__(s,
	             useClangFormat=False,
	             layerFilter=None,
	             processPreview=False,
	             useSegmentCount=True,
	             defaultSegments=None,
	             *args,
	             **kwargs):
		processing.ProcessBase.__init__(s, *args, **kwargs)
		s.layerFilter = layerFilter
		s.processPreview = processPreview
		s.useClangFormat = useClangFormat
		s.useSegmentCount = useSegmentCount
		s.defaultSegments = None

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

		viewer_process = subprocess.Popen(["openscad", fn])
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

	def __call__(s, ent: processing.EntityRecord):

		res = processing.ProcessResults()

		vcodegen = codegen.OpenSCADcodeGen(layerFilter=s.layerFilter,
		                                   processPreview=s.processPreview,
		                                   useSegmentCount=s.useSegmentCount)
		ent.node.visitDescendants(vcodegen)
		vcodegen.finish()

		vdim = metadata.DimensionVisitor()
		ent.node.visitDescendants(vdim)
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

		fn_tmp = tempfile.mkdtemp()
		cwd = os.getcwd()
		try:
			os.chdir(fn_tmp)
			with open("code.scad", "w") as f:
				if s.defaultSegments is not None:
					f.write(f"$fn={codegen.scad_repr(s.defaultSegments)};")
				f.write(vcodegen.code)

			p = subprocess.Popen(["openscad", "-o", fn_out, "code.scad"],
			                     stdout=subprocess.PIPE,
			                     stderr=subprocess.PIPE)

			(_, serr) = p.communicate()
			if p.returncode != 0:
				raise RuntimeError("error compiling OpenSCAD code: \n" + serr.decode())

			if s.outputFile:
				res.files.append(fn_out)

			if s.outputRaw or s.outputGeometry:
				with open(fn_out, "rb") as f:
					raw_data = f.read()
					if s.outputRaw:
						res.data["raw"] = raw_data

		finally:
			os.chdir(cwd)
			shutil.rmtree(fn_tmp)

		if s.outputGeometry:
			soup = FaceSoup()
			res.data["geometry"] = soup

			if extension == ".stl":
				soup.load_stl(raw_data.decode())
			elif extension == ".svg":
				soup.load_svg_loops(raw_data.decode())
			else:
				raise RuntimeError(f"cannot load geometry from {extension} files")

		return res
