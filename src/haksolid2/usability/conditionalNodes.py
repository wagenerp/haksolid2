class OptionalConditionalNode:
	def __init__(s, baseClass, disabledClass):
		s.baseClass = baseClass
		s.disabledClass = disabledClass

	def __call__(s, *args, **kwargs):
		return s.baseClass(*args, **kwargs)

	def If(s, condition, *args, **kwargs):
		if condition:
			return s.baseClass(*args, **kwargs)
		else:
			return s.disabledClass()
