import tempfile
import subprocess
import hashlib
import pathlib
import shutil
import json
from ..math import *
import time
import os


class SCADCache:
	def lookup(s, code):
		raise NotImplementedError()

	def store(s, code, result, is3d):
		raise NotImplementedError()


class DisabledSCADCache(SCADCache):
	def lookup(s, code):
		return None, None

	def store(s, code, result, is3d):
		pass


class DirectorySCADCache(SCADCache):
	def __init__(s, fn):
		s._fn = pathlib.Path(fn)
		s._fn_meta = s._fn / "meta.json"

	def getMeta(s, key=None, create=True):
		if s._fn_meta.exists():
			with open(s._fn_meta, "r") as f:
				meta = json.load(f)
		else:
			meta = {"entries": {}}
		if key is not None:
			if key not in meta["entries"]:
				if not create:
					return meta, None
				meta["entries"][key] = {"usageCount": 0}
			return meta, meta["entries"][key]
		return meta

	def setMeta(s, meta):
		if not s._fn.exists():
			os.makedirs(s._fn)
		with open(s._fn_meta, "w") as f:
			json.dump(meta, f)

	def lookup(s, code):
		digest = hashlib.sha256(code.encode()).hexdigest()
		fn_result = s._fn / f"{digest}.dat"
		meta, entry = s.getMeta(digest, False)
		if entry is None: return None, None

		if not entry["success"]:
			return b"", None

		if not fn_result.exists(): return None, None

		entry["lastUsed"] = time.time()
		entry["usageCount"] += 1

		s.setMeta(meta)

		with open(fn_result, "rb") as f:
			raw = f.read()

		return raw, entry["is3d"]

	def store(s, code, result, is3d, renderTime):
		digest = hashlib.sha256(code.encode()).hexdigest()
		fn_result = s._fn / f"{digest}.dat"

		meta, entry = s.getMeta(digest, True)
		entry["success"] = result is not None
		if result is not None: # successful compilation
			if not s._fn.exists():
				os.makedirs(s._fn)
			with open(fn_result, "wb") as f:
				f.write(result)
			entry["is3d"] = bool(is3d)
			entry["cb"] = len(result)
		entry["usageCount"] = 0
		entry["lastUsed"] = 0
		entry["written"] = time.time()
		entry["renderTime"] = renderTime

		s.setMeta(meta)


DefaultCache = None


def GetDefaultCache():
	global DefaultCache
	if DefaultCache is None:
		import main
		if hasattr(main, "__file__"):
			DefaultCache = DirectorySCADCache(
			  pathlib.Path(main.__file__).resolve().parent / ".scadcache")
		else:
			DefaultCache = DisabledSCADCache()
	return DefaultCache


def addOpenSCADCacheArguments(cmdline, useCache):
	if useCache is None:
		p = subprocess.run(["openscad", "--help"], stderr=subprocess.PIPE)
		if re.match(".*--cache[ \\t]+arg.*", p.stderr.decode(), re.DOTALL):
			useCache = True
		else:
			useCache = False
	if useCache:
		return True, cmdline + ["--cache", "file"]
	else:
		return False, cmdline


def RenderSCADCode_raw(code, fb, useCache=None):
	fn_tmp = tempfile.mkdtemp()
	cwd = os.getcwd()
	try:
		os.chdir(fn_tmp)
		with open("code.scad", "w") as f:
			f.write(code)

		_, cmdline = addOpenSCADCacheArguments(["openscad", "-o", fb, "code.scad"],
		                                       useCache)

		p = subprocess.Popen(cmdline,
		                     stdout=subprocess.PIPE,
		                     stderr=subprocess.PIPE)

		(_, serr) = p.communicate()

		if p.returncode != 0:
			raise RuntimeError("error compiling OpenSCAD code: \n" + serr.decode())

		with open(fb, "rb") as f:
			raw_data = f.read()

	finally:
		os.chdir(cwd)
		shutil.rmtree(fn_tmp)

	return raw_data


def RenderSCADCode(code,
                   is3d,
                   rawCache=None,
                   useCache=None,
                   decode=False,
                   outputFormat=None,
                   cacheOnly=False,
                   referenceCode=None):
	if rawCache is None:
		rawCache = DisabledSCADCache()
	elif isinstance(rawCache, SCADCache):
		rawCache = rawCache
	elif rawCache:
		rawCache = GetDefaultCache()
	else:
		rawCache = DisabledSCADCache()

	if outputFormat is not None and outputFormat in {".stl", ".svg"}:
		outputFormat = None

	if outputFormat is not None:
		# cannot cache overridden output format
		if decode:
			raise RuntimeError(f"cannot load geometry from {outputFormat} files")

		return RenderSCADCode_raw(code, "out" + outputFormat)

	raw_data, cached_is3d = rawCache.lookup(code)

	if raw_data is None:
		if cacheOnly:
			if decode:
				return None, None
			else:
				return None
		fb = "out.stl" if is3d else "out.svg"

		t0 = time.time()
		try:
			try:
				raw_data = RenderSCADCode_raw(code, fb)
			finally:
				renderTime = time.time() - t0
		except RuntimeError:
			if not isinstance(rawCache, DisabledSCADCache):
				rawCache.store(code, None, None, renderTime)
				if referenceCode is not None:
					rawCache.store(referenceCode, None, None, renderTime)
			raise

		if not isinstance(rawCache, DisabledSCADCache):
			rawCache.store(code, raw_data, is3d, renderTime)
			if referenceCode is not None:
				rawCache.store(referenceCode, raw_data, is3d, renderTime)

	if decode:
		soup = FaceSoup()
		if is3d:
			soup.load_stl(raw_data.decode())
		else:
			soup.load_svg_loops(raw_data.decode())
		return raw_data, soup

	return raw_data