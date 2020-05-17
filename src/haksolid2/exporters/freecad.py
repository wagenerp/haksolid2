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
import tempfile
import shutil
import subprocess

ultralaser_job_t = namedtuple("ultralaser_job_t", "T params penetrates soup")


class FreeCAD(openscad.OpenSCADBuild):
	def __init__(s, format=".fcstd"):
		openscad.OpenSCADBuild.__init__(s,
		                                outputFile=False,
		                                outputRaw=True,
		                                outputFormat=".csg",
		                                useSegmentCount=False)
		s.format = format

	def __call__(s, ent: processing.EntityRecord):

		res = openscad.OpenSCADBuild.__call__(s, ent)

		if not "raw" in res.data:
			raise RuntimeError("error getting CSG for FreeCAD output")

		fn_out = os.path.join(s.getOutputDirectory(True), ent.name + s.format)

		fn_tmp = tempfile.mkdtemp()
		cwd = os.getcwd()
		try:
			os.chdir(fn_tmp)

			with open("in.csg", "wb") as f:
				f.write(res.data["raw"])

			p = subprocess.Popen(["freecad", "-c"], stdin=subprocess.PIPE)

			p.stdin.write((f'import FreeCAD\n'
			               f'import importCSG\n'
			               f'importCSG.insert(u"in.csg","Unnamed")\n').encode())

			if s.format == ".fcstd":
				p.stdin.write(
				  (f'App.getDocument("Unnamed").saveAs(u"{fn_out}")\n').encode())
			elif s.format == ".step":
				p.stdin.write((
				  f'import Import\n'
				  f'Import.export(FreeCAD.getDocument("Unnamed").findObjects()[-1:],u"{fn_out}")\n'
				).encode())
			else:
				raise RuntimeError(
				  f"unsupported format for FreeCAD process: {s.format}")

			p.stdin.write(b'exit()\n')
			p.stdin.flush()
			# p.stdin.close()
			p.wait()
			if p.returncode != 0:
				raise RuntimeError("error translating CSG to FreeCAD: \n" +
				                   p.stderr.read().decode())

			res.files.append(fn_out)

		finally:
			os.chdir(cwd)
			shutil.rmtree(fn_tmp)

		return res