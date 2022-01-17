import cli
import json
from collections import namedtuple
import os
import jsonschema
from .. import metadata

fn_schema = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         "customizer-schema.json")

customizer_record_t = namedtuple("customizer_record_t", "fn preset")

customizerPresets = list()


@cli.command("c", "customizer")
def _(fn: cli.file_path, preset):
	"""Select a customizer json file and preset name to apply, replacing previous defaults"""
	customizerPresets.append(customizer_record_t(fn, preset))


customizer_schema = None


def getSchema():
	global customizer_schema
	if customizer_schema is None:
		with open(fn_schema, "r") as f:
			customizer_schema = json.load(f)

	return customizer_schema


class PresetFile:
	def __init__(s, fn):
		with open(fn, "r") as f:
			data = json.load(f)
		jsonschema.validate(data, getSchema())

		s.presets = data["parameterSets"]

	def applyPreset(s, ident):
		if ident in s.presets:
			for k, v in s.presets[ident].items():
				metadata.variable.SetGlobalDefault(k, v)


@cli.check
def check_customizer():
	if len(customizerPresets) < 1: return
	parameterSets = dict()

	for fn, preset in customizerPresets:
		if fn in parameterSets: continue
		try:
			parametersets[fn] = PresetFile(fn)
		except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as e:
			raise cli.clex(f"error loading customizer file {fn}: {e}")

	for fn, preset in customizerPresets:
		paramFile = parameterSets[fn]
		if not preset in paramFile.presets:
			raise cli.clex(f"missing parameter set {preset} in {fn}")

		paramFile.applyPreset(preset)
