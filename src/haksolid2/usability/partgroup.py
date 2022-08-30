import inspect
from .. import dag, processing, metadata


def token_5a986b8a_a789_47b5_8b2b_2f71e3a048b0(ident, func, *args, **kwargs):
	return func(*args, **kwargs)


def token_a490036a_66ef_4622_9222_bcf65a26044e(func, *args, **kwargs):
	return func(*args, **kwargs)


@dag.DAGModule
def subpart(generator_or_ident, generator=None, hidden=False):

	ident = None
	if isinstance(generator_or_ident, str):
		ident = generator_or_ident
	else:
		generator = generator_or_ident
		ident = generator.__name__

	stack = inspect.stack()
	for i_frame, inf in enumerate(stack[1:]):

		if inf.function == "token_a490036a_66ef_4622_9222_bcf65a26044e":
			processing.part.module(ident, args=(
			  ident,
			  inf.frame.f_locals["func"]))(token_5a986b8a_a789_47b5_8b2b_2f71e3a048b0)
			return
		if inf.function == "token_5a986b8a_a789_47b5_8b2b_2f71e3a048b0":
			if inf.frame.f_locals["ident"] != ident: return
			~generator()
			return
	if not hidden:
		~generator()


@dag.DAGModule
def subassembly():
	stack = inspect.stack()
	manifest = True
	for i_frame, inf in enumerate(stack[1:]):
		if inf.function == "token_a490036a_66ef_4622_9222_bcf65a26044e":
			manifest = False
			break
		if inf.function == "token_5a986b8a_a789_47b5_8b2b_2f71e3a048b0":
			manifest = False
			break
	~metadata.conditional(manifest) * dag.DAGAnchor()


def partgroup(func):
	token_a490036a_66ef_4622_9222_bcf65a26044e(func)
	return dag.DAGModule(func)