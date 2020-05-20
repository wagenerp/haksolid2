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
import zipfile
import inspect


class CuraLayer(metadata.previewLayer):
	def __init__(s, r, g, b, a, **kwargs):
		metadata.previewLayer.__init__(s)
		s.color = V(r, g, b)
		s.alpha = a

		s.keyvalues = dict(kwargs)


def augmentKeyvalues(loc, func, kwargs):
	keyvalues = dict(kwargs)

	for arg in inspect.signature(func).parameters:
		if arg == "s": continue
		if arg == "kwargs": continue
		if arg not in loc: continue
		if loc[arg] is None: continue

		keyvalues[arg] = loc[arg]
	return keyvalues


def infillMesh(infill_sparse_density: float = None, **kwargs):
	keyvalues = augmentKeyvalues(locals(), infillMesh, kwargs)
	return CuraLayer(1, 1, 0, 0.4, infill_mesh=True, **keyvalues)


def cuttingMesh(infill_sparse_density: float = None, **kwargs):
	keyvalues = augmentKeyvalues(locals(), cuttingMesh, kwargs)
	return CuraLayer(1, 1, 0, 0.4, cutting_mesh=True, **keyvalues)


def supportMesh():
	return CuraLayer(1, 0.5, 0, 0.4, support_mesh=True)


def supportBlock():
	return CuraLayer(1, 0, 1, 0.4, anti_overhang_mesh=True)


class Cura(processing.ProcessBase):
	def __init__(s, **kwargs):
		processing.ProcessBase.__init__(s, **kwargs)

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

		soup = s._extractSoup(res)
		return soup

	def _extractSoup(s, res: processing.ProcessResults):

		if not "geometry" in res.data:
			raise RuntimeError("error retrieving geometry for lasercut layer")

		soup = res.data["geometry"]

		if not isinstance(soup, FaceSoup):
			raise RuntimeError("unexpected geometry data type")

		return soup

	def _generateObjectXML(s, id, layer, soup: FaceSoup):
		xml = f'<object id="{id}" type="model">\n'

		xml += '<mesh>\n'
		xml += '<vertices>\n'
		for face in soup.faces:
			if len(face.vertices) != 3:
				raise RuntimeError("non-triangular mesh in cura process")
			for v in face.vertices:
				xml += f'<vertex x="{v.x}" y="{v.z}" z="{-v.y}" />\n'
		xml += '</vertices>\n'
		xml += '<triangles>\n'
		i_vertex = 0
		for face in soup.faces:
			xml += f'<triangle v1="{i_vertex}" v2="{i_vertex+1}" v3="{i_vertex+2}" />\n'
			i_vertex += 3
		xml += '</triangles>\n'
		xml += '</mesh>\n'

		if isinstance(layer, CuraLayer) and len(layer.keyvalues) > 0:
			xml += '<metadatagroup>\n'
			for k, v in layer.keyvalues.items():
				xml += f'<metadata name="cura:{k}" preserve="true" type="xs:string">{v}</metadata>\n'
			xml += '</metadatagroup>\n'
		xml += '</object>\n'

		return xml

	def __call__(s, ent: processing.EntityRecord):

		# build a list of tuples (transform, root, soup) of lasercutting subjobs
		xml_objects = ""
		object_count = 0

		subproc = openscad.OpenSCADBuild(outputFile=False, outputGeometry=True)

		if True: # build the main geometry
			subent = processing.EntityRecord(processing.EntityNode, ent.node.node, "",
			                                 "", subproc)
			res = processing.buildEntity(subent)
			soup = s._extractSoup(res)
			xml_objects += s._generateObjectXML(object_count + 2, None, soup)
			object_count += 1

		if True: # add all sub-layers to the mix
			layers = metadata.LayersVisitor(shallow=False)
			ent.node.visitDescendants(layers)

			for T, layer in layers.layers:
				if layer == ent.node: continue
				if not isinstance(layer, CuraLayer): continue

				soup = s._processLayer(T, layer, subproc)
				xml_objects += s._generateObjectXML(object_count + 2, layer, soup)
				object_count += 1

		fn_out = os.path.join(s.getOutputDirectory(True), ent.name + ".3mf")

		# group all objects in this part
		xml_model = (
		  '<?xml version="1.0"?>\n'
		  '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:cura="http://software.ultimaker.com/xml/cura/3mf/2015/10" xml:lang="en-US">\n'
		  '<resources>\n')

		xml_model += '<object id="1" type="model"><components>'
		for i in range(len(xml_objects)):
			xml_model += f'<component objectid="{i+2}" transform="1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0" />'
		xml_model += '</components></object>'
		xml_model += xml_objects

		xml_model += '</resources>\n'
		xml_model += '<build>\n'
		xml_model += '<item objectid="1" transform="1.0 0.0 0.0 0.0 0.0 1.0 0.0 -1.0 0.0 111.5 111.5 5.0" />\n'
		xml_model += '</build>\n'
		xml_model += '</model>\n'

		fout = zipfile.ZipFile(fn_out, "w")
		fout.writestr("3D/3dmodel.model", xml_model)
		fout.close()

		res = processing.ProcessResults()
		res.files.append(fn_out)
