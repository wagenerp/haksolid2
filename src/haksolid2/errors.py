
class HaksolidWarning(UserWarning): pass
class HaksolidError(Exception): pass

class UnsupportedFeatureWarning(HaksolidWarning): pass
class UnsupportedFeatureError(HaksolidError): pass
