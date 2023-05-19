from abc import ABCMeta, abstractmethod
import typing
import functools


class Comparable(metaclass=ABCMeta):
    @abstractmethod
    def __lt__(self,other:typing.Any)->bool:
        """ """

ComparableType=typing.TypeVar("ComparableType",bound=Comparable)


T=typing.TypeVar('T')
PS=typing.ParamSpec('PS') # a typevar for an entire parameter list pattern
    # useage fnX(*args:PS.args,**kwargs:PS.kwargs)

def deco(cls):
    @functools.wraps(cls,updated=())
    class Modified(cls):
        def addedFunc(self):
            pass
    return Modified

class qqdeco:
    def __init__(self,type:typing.Type,compatibleTypes:typing.Optional[typing.Type]=None):
        self.type:typing.Type=type
        self.compatibleTypes:typing.Optional[typing.Type]=compatibleTypes
    def __call__(self,cls):
        type=self.type
        compatibleTypes=self.compatibleTypes if self.compatibleTypes is not None else self.type
        @functools.wraps(cls,updated=())
        class Wrapper(cls):
            _elementType_=type
            _elementCompatibleTypes_=compatibleTypes
            @classmethod
            def _elementFactory_(cls,x:compatibleTypes)->type:
                return type(x)
        return Wrapper

@qqdeco(int,str)
class MyClass:
    def whatev(self):
        pass

mc=MyClass()
n=mc._elementFactory_("10")
print(mc)