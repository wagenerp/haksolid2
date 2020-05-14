from .. import dag
from .. import processing
from .. import errors
from .. import metadata
from . import codegen
import warnings

import os
import subprocess

import tempfile
import shutil


class OpenSCADSource(processing.ProcessBase):
	def __init__(s, useClangFormat=False, *args, **kwargs):
		processing.ProcessBase.__init__(s, *args, **kwargs)
		s.useClangFormat = useClangFormat

	def __call__(s, ent: processing.EntityRecord):

		res = processing.ProcessResults()

		visitor = codegen.OpenSCADcodeGen()
		ent.node.visitDescendants(visitor)

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
	def __init__(s, *args, **kwargs):
		processing.ProcessBase.__init__(s, *args, **kwargs)
		s.useClangFormat = False

	def __call__(s, ent: processing.EntityRecord):

		res = processing.ProcessResults()

		vcodegen = codegen.OpenSCADcodeGen()
		ent.node.visitDescendants(vcodegen)

		vdim=metadata.DimensionVisitor()
		ent.node.visitDescendants(vdim)
		if vdim.has3d or vdim.empty:
			extension = ".stl"
		else:
			extension = ".svg"

		fn_out = os.path.join(s.getOutputDirectory(True), ent.name + extension)

		fn_tmp = tempfile.mkdtemp()
		cwd = os.getcwd()
		try:
			os.chdir(fn_tmp)
			with open("code.scad", "w") as f:
				f.write(vcodegen.code)

			p = subprocess.Popen(["openscad", "-o", fn_out, "code.scad"],
			                     stdout=subprocess.PIPE,
			                     stderr=subprocess.PIPE)

			(_, serr) = p.communicate()
			if p.returncode != 0:
				raise RuntimeError("error compiling OpenSCAD code: \n" + serr.decode())

		finally:
			os.chdir(cwd)
			shutil.rmtree(fn_tmp)

		res.files.append(fn_out)

		return res
