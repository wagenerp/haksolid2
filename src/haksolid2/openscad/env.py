from ..primitives import *
from ..transform import *
from ..operations import *
from ..metadata import *
from ..processing import *
from ..openscad import *
from ..usability import *
from ..math import *
from ..processing.cli import climain
from ..dag import DAGModule, DAGGroup
from ..prefabs import *
from ..paradigms import *
from ..exporters import *

part.SetDefaultProcess(OpenSCADBuild())
arrangement.SetDefaultProcess(
  OpenSCADSource(useClangFormat=False,
                 layerFilter=ClassLayerFilter(previewLayer),
                 processPreview=True))
