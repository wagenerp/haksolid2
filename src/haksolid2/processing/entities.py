from .. import dag
from .. import errors
import warnings

_named_entities = dict()


class EntityDefinitionWarning(errors.HaksolidWarning):
	pass


class EntityDefinitionError(errors.HaksolidError):
	pass


def getEntities() -> dict:
	global _named_entities
	return dict(_named_entities)


def registerEntity(ent):
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


def buildEntity(ent):
	if ent.process is None:
		raise EntityDefinitionError(f"process undefined for entity {ent.name}")

	if isinstance(ent, EntityNode):
		return ent.process(ent)
	else:
		node = ent()
		return ent.process(node)


class EntityType:
	DefaultProcess = None

	def __new__(cls, name: str, description=None, process=None):
		return EntityNode(cls, name, description, process)

	@classmethod
	def module(cls, nameOrFunc, description=None, process=None):

		if process is None:
			process = cls.DefaultProcess

		if isinstance(nameOrFunc, str):

			def metawrapper(func):

				func.type = cls
				func.name = func.nameOrFunc
				func.description = description
				func.process = process

				registerEntity(func)

				def wrapper(*args, **kwargs):
					root = dag.DAGGroup()
					with root:
						func(*args, **kwargs)
					return root.makeModule()

			return metawrapper
		else:

			nameOrFunc.type = cls
			nameOrFunc.name = nameOrFunc.__name__
			nameOrFunc.description = nameOrFunc.__doc__
			nameOrFunc.process = process

			registerEntity(nameOrFunc)

			def wrapper(*args, **kwargs):
				root = dag.DAGGroup()
				with root:
					nameOrFunc(*args, **kwargs)
				return root.makeModule()

			return wrapper

	@classmethod
	def SetDefaultProcess(cls, process):
		if not callable(process):
			raise TypeError(f"not callable: {process}")
		setattr(cls, "DefaultProcess", process)


class part(EntityType):
	pass


class arrangement(EntityType):
	pass


class EntityNode(dag.DAGGroup):
	def __init__(s, entityType: EntityType, name, description=None, process=None):
		s.type = entityType
		if process is None:
			process = entityType.DefaultProcess

		s.name = name
		s.description = description
		s.process = process

		registerEntity(s)
