from .. import dag
from .. import errors
from . import processes
import warnings

_named_entities = dict()


class EntityRecord:
	def __init__(s, cls, subject, name, description, process=None):
		if process is None:
			process = cls.DefaultProcess

		if not isinstance(process,processes.ProcessBase):
			raise TypeError(f"not a process: {process}")

		s._subject = subject
		if isinstance(subject, EntityNode):
			s._node = subject
		else:
			s._node = None

		s._type = cls
		s._name = name
		s._description = description
		s._process = process

	@property
	def type(s):
		return s._type

	@property
	def name(s):
		return s._name

	@property
	def description(s):
		return s._description

	@property
	def process(s):
		return s._process

	@property
	def node(s):
		if s._node is None:
			s._node = s._subject()
		return s._node


class EntityDefinitionWarning(errors.HaksolidWarning):
	pass


class EntityDefinitionError(errors.HaksolidError):
	pass


def getEntities() -> dict:
	global _named_entities
	return dict(_named_entities)


def registerEntity(ent: EntityRecord):
	if ent.process is None:
		warnings.warn(
		  EntityDefinitionWarning(f"no process defined for entity {ent.name}"))

	global _named_entities
	if ent.name not in _named_entities:
		_named_entities[ent.name] = ent
	else:
		warnings.warn(
		  EntityDefinitionWarning(
		    f"entity {ent.name} redefined, ignored in entity list"))


def buildEntity(ent: EntityRecord):
	if ent.process is None:
		raise EntityDefinitionError(f"process undefined for entity {ent.name}")

	return ent.process(ent)


class EntityType:
	DefaultProcess = None

	def __new__(cls, name: str, description=None, process=None):
		node = EntityNode()
		rec = EntityRecord(cls, node, name, description, process)
		registerEntity(rec)
		return node

	@classmethod
	def module(cls, nameOrFunc, description=None, process=None):

		if isinstance(nameOrFunc, str):

			def metawrapper(func):
				def wrapper(*args, **kwargs):
					root = dag.DAGGroup() * dag.DAGGroup()
					with root:
						func(*args, **kwargs)
					return root.makeModule()

				rec = EntityRecord(cls, wrapper, nameOrFunc, description, process)
				registerEntity(rec)

			return metawrapper
		else:

			def wrapper(*args, **kwargs):
				root = dag.DAGGroup() * dag.DAGGroup()
				with root:
					nameOrFunc(*args, **kwargs)
				return root.makeModule()

			rec = EntityRecord(cls, wrapper, nameOrFunc.__name__, nameOrFunc.__doc__,
			                   process)
			registerEntity(rec)
			return wrapper

	@classmethod
	def SetDefaultProcess(cls, process: processes.ProcessBase):
		if not isinstance(process, processes.ProcessBase):
			raise TypeError(f"not a process: {process}")
		setattr(cls, "DefaultProcess", process)


class part(EntityType):
	pass


class arrangement(EntityType):
	pass


class EntityNode(dag.DAGGroup):
	def __init__(s):
		dag.DAGGroup.__init__(s)