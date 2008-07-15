

currentGlobals = globals()

class LazyPackage(object):
    
    def __init__(self):
        import sys
        import os
        sys.modules["eg"] = self
        self.__path__ = [os.path.abspath("eg")]
        import __builtin__
        __builtin__.__dict__["eg"] = self

        
    def __getattr__(self, name):
        mod = __import__("eg.Classes." + name, currentGlobals, None, [name], 0)
        self.__dict__[name] = attr = getattr(mod, name)
        return attr

LazyPackage()
