import os

main = __import__("__main__")
fn_main_dir = os.path.dirname(os.path.realpath(main.__file__))


class ProcessResults:
	def __init__(s):
		s.files = list()
		s.data = dict()


class ProcessResultViewer:
	def wait(s):
		pass


class SubprocessResultViewer(ProcessResultViewer):
	def __init__(s, proc):
		s.proc = proc

	def wait(s):
		s.proc.wait()


class ProcessBase:
	DefaultDirectory = None

	def __init__(s, outputDirectory=None):
		s._outputDirectory = outputDirectory
	
	def __str__(s):
		return s.__class__.__name__

	def getOutputDirectory(s, create=False):

		if s._outputDirectory is not None:
			res = s._outputDirectory
		elif s.DefaultDirectory is not None:
			res = s.DefaultDirectory
		else:
			res = fn_main_dir

		res = os.path.realpath(res)
		if create and not os.path.exists(res):
			os.makedirs(res)

		return res

	def __call__(s, ent):
		raise NotImplementedError()

	def watch(s, res: ProcessResults) -> ProcessResultViewer:
		pass
