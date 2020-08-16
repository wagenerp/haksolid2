from .. import dag
from .. import errors
from . import processes
import warnings

_named_entities = dict()


class EntityRecord:
	def __init__(s,
	             cls,
	             subject,
	             name,
	             description,
	             process=None,
	             args=None,
	             kwargs=None):
		if process is None:
			process = cls.DefaultProcess

		if not isinstance(process, processes.ProcessBase):
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
		if args is None:
			args = list()
		if kwargs is None:
			kwargs = dict()
		s._args = args
		s._kwargs = kwargs

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
			s._node = s._subject(*s._args, **s._kwargs)
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

	def __new__(cls,
	            name: str,
	            description=None,
	            process=None,
	            args=None,
	            kwargs=None):
		if process is None:
			process = cls.DefaultProcess
		node = EntityNode(process)
		rec = EntityRecord(cls, node, name, description, process, args, kwargs)
		registerEntity(rec)
		return node

	@classmethod
	def module(cls,
	           nameOrFunc=None,
	           description=None,
	           process=None,
	           args=None,
	           kwargs=None):

		if process is None:
			process = cls.DefaultProcess

		if isinstance(nameOrFunc, str) or nameOrFunc is None:

			def metawrapper(func):
				name = nameOrFunc
				if name is None:
					name = func.__name__

				def wrapper(*args, **kwargs):
					root = EntityNode(process) * dag.DAGGroup()
					with root:
						func(*args, **kwargs)
					return root.makeModule()

				rec = EntityRecord(cls, wrapper, name, description, process, args,
				                   kwargs)
				registerEntity(rec)

				return wrapper

			return metawrapper
		else:

			def wrapper(*args, **kwargs):
				root = EntityNode(process) * dag.DAGGroup()
				with root:
					nameOrFunc(*args, **kwargs)
				return root.makeModule()

			rec = EntityRecord(cls, wrapper, nameOrFunc.__name__, nameOrFunc.__doc__,
			                   process, args, kwargs)
			registerEntity(rec)
			return wrapper

	@classmethod
	def classmodule(cls,
	                nameOrFunc=None,
	                description=None,
	                process=None,
	                args=None,
	                kwargs=None):
		def wrapper(func):
			def funcwrapper(*args, **kwargs):
				root = EntityNode(process) * dag.DAGGroup()
				with root:
					func(*args, **kwargs)
				return root.makeModule()

			print("setting", f"register_with_entity_{cls.__name__}")
			setattr(funcwrapper, f"register_with_entity_{cls.__name__}",
			        (nameOrFunc if isinstance(nameOrFunc, str) else func.__name__,
			         description if description is not None else func.__doc__,
			         process, args, kwargs))
			return classmethod(funcwrapper)

		if isinstance(nameOrFunc, str) or nameOrFunc is None:
			return wrapper
		else:
			return wrapper(nameOrFunc)

	@classmethod
	def moduleClass(me, it):
		key = f"register_with_entity_{me.__name__}"
		print("scanning ")
		for ident in dir(it):
			method = getattr(it, ident)
			if not hasattr(method, key): continue
			nameOrFunc, description, process, args, kwargs = getattr(method, key)
			if not isinstance(nameOrFunc, str):
				nameOrFunc = method.__name__
			rec = EntityRecord(me, method, nameOrFunc, description, process, args,
			                   kwargs)
			registerEntity(rec)

		return it

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
	def __init__(s, process: processes.ProcessBase):
		s.process = process
		dag.DAGGroup.__init__(s)

	def __str__(s):
		return f"{s.__class__.__name__}({s.process})"