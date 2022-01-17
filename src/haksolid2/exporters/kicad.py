from ..paradigms import lasercut
import textwrap
from .. import processing
from .. import usability
from .. import metadata
from .. import paradigms
from .. import openscad
from .. import transform
from ..math import *
import shlex
import os
import subprocess
from collections import namedtuple

KiCAD_job_t = namedtuple("KiCAD_job_t", "T soup layer fill")


class KiCADLayer(metadata.SubprocessLayer):
	def __init__(s, layer, fill=False, lineWidth=0.15):

		metadata.SubprocessLayer.__init__(s)
		s.layer = layer
		s.fill = fill
		s.lineWidth = lineWidth

	def __str__(s):
		return f"KiCADLayer({s.layer}{' fill' if s.fill else ''})"



class KiCAD(processing.ProcessBase):
	def __init__(s, thickness=1.6, **kwargs):
		processing.ProcessBase.__init__(s, **kwargs)
		s.thickness = thickness

	def __str__(s):
		return f"KiCAD({s.thickness})"


	@classmethod
	def F_Cu(c,**kwargs):
		return KiCADLayer("F.Cu",**kwargs)
	@classmethod
	def B_Cu(c,**kwargs):
		return KiCADLayer("B.Cu",**kwargs)
	@classmethod
	def B_Adhes(c,**kwargs):
		return KiCADLayer("B.Adhes",**kwargs)
	@classmethod
	def F_Adhes(c,**kwargs):
		return KiCADLayer("F.Adhes",**kwargs)
	@classmethod
	def B_Paste(c,**kwargs):
		return KiCADLayer("B.Paste",**kwargs)
	@classmethod
	def F_Paste(c,**kwargs):
		return KiCADLayer("F.Paste",**kwargs)
	@classmethod
	def B_SilkS(c,**kwargs):
		return KiCADLayer("B.SilkS",**kwargs)
	@classmethod
	def F_SilkS(c,**kwargs):
		return KiCADLayer("F.SilkS",**kwargs)
	@classmethod
	def B_Mask(c,**kwargs):
		return KiCADLayer("B.Mask",**kwargs)
	@classmethod
	def F_Mask(c,**kwargs):
		return KiCADLayer("F.Mask",**kwargs)
	@classmethod
	def Dwgs_User(c,**kwargs):
		return KiCADLayer("Dwgs.User",**kwargs)
	@classmethod
	def Cmts_User(c,**kwargs):
		return KiCADLayer("Cmts.User",**kwargs)
	@classmethod
	def Eco1_User(c,**kwargs):
		return KiCADLayer("Eco1.User",**kwargs)
	@classmethod
	def Eco2_User(c,**kwargs):
		return KiCADLayer("Eco2.User",**kwargs)
	@classmethod
	def Edge_Cuts(c,**kwargs):
		return KiCADLayer("Edge.Cuts",**kwargs)
	@classmethod
	def Margin(c,**kwargs):
		return KiCADLayer("Margin",**kwargs)
	@classmethod
	def B_CrtYd(c,**kwargs):
		return KiCADLayer("B.CrtYd",**kwargs)
	@classmethod
	def F_CrtYd(c,**kwargs):
		return KiCADLayer("F.CrtYd",**kwargs)
	@classmethod
	def B_Fab(c,**kwargs):
		return KiCADLayer("B.Fab",**kwargs)
	@classmethod
	def F_Fab(c,**kwargs):
		return KiCADLayer("F.Fab",**kwargs)
	@classmethod
	def User_1(c,**kwargs):
		return KiCADLayer("User.1",**kwargs)
	@classmethod
	def User_2(c,**kwargs):
		return KiCADLayer("User.2",**kwargs)
	@classmethod
	def User_3(c,**kwargs):
		return KiCADLayer("User.3",**kwargs)
	@classmethod
	def User_4(c,**kwargs):
		return KiCADLayer("User.4",**kwargs)
	@classmethod
	def User_5(c,**kwargs):
		return KiCADLayer("User.5",**kwargs)
	@classmethod
	def User_6(c,**kwargs):
		return KiCADLayer("User.6",**kwargs)
	@classmethod
	def User_7(c,**kwargs):
		return KiCADLayer("User.7",**kwargs)
	@classmethod
	def User_8(c,**kwargs):
		return KiCADLayer("User.8",**kwargs)
	@classmethod
	def User_9(c,**kwargs):
		return KiCADLayer("User.9",**kwargs)

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
			raise RuntimeError("error retrieving geometry for kicad layer")

		soup = res.data["geometry"]

		if not isinstance(soup, FaceSoup):
			raise RuntimeError("unexpected geometry data type")

		return soup

	def __call__(s, ent: processing.EntityRecord):

		# build a list of tuples (transform, root, soup) of lasercutting subjobs
		jobs = list()

		subproc = openscad.OpenSCADBuild(outputFile=False, outputGeometry=True)

		code = ""

		if True: # add all sub-layers to the mix
			layers = metadata.LayersVisitor(shallow=False)
			ent.node.visitDescendants(layers)

			for T, layer in layers.layers:
				if layer == ent.node: continue
				if not isinstance(layer, KiCADLayer): continue

				soup = s._processLayer(T, layer, subproc)

				for face in soup.faces:
					if len(face.vertices) < 2: continue

					pts = " ".join(f"(xy {v.x} {v.y})" for v in face.vertices)
					code += f"(gr_poly (pts {pts} ) (layer \"{layer.layer}\") (width {layer.lineWidth}) (fill {'solid' if layer.fill else 'none'}))\n"

		fn_out = os.path.join(s.getOutputDirectory(True), ent.name + ".kicad_pcb")


		with open(fn_out,"w") as f:
			f.write(s.CodeTemplate.format(thickness=s.thickness,code=code))

		res = processing.ProcessResults()
		res.files.append(fn_out)

		return res

	CodeTemplate=textwrap.dedent("""		
		(kicad_pcb (version 20211014) (generator pcbnew)
			(general
				(thickness {thickness})
			)

			(paper "A4")
			(layers
				(0 "F.Cu" signal)
				(31 "B.Cu" signal)
				(32 "B.Adhes" user "B.Adhesive")
				(33 "F.Adhes" user "F.Adhesive")
				(34 "B.Paste" user)
				(35 "F.Paste" user)
				(36 "B.SilkS" user "B.Silkscreen")
				(37 "F.SilkS" user "F.Silkscreen")
				(38 "B.Mask" user)
				(39 "F.Mask" user)
				(40 "Dwgs.User" user "User.Drawings")
				(41 "Cmts.User" user "User.Comments")
				(42 "Eco1.User" user "User.Eco1")
				(43 "Eco2.User" user "User.Eco2")
				(44 "Edge.Cuts" user)
				(45 "Margin" user)
				(46 "B.CrtYd" user "B.Courtyard")
				(47 "F.CrtYd" user "F.Courtyard")
				(48 "B.Fab" user)
				(49 "F.Fab" user)
				(50 "User.1" user)
				(51 "User.2" user)
				(52 "User.3" user)
				(53 "User.4" user)
				(54 "User.5" user)
				(55 "User.6" user)
				(56 "User.7" user)
				(57 "User.8" user)
				(58 "User.9" user)
			)
			
			(net 0 "")
			
			{code}
		)
	""")