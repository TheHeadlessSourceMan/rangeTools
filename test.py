"""
Test playground for future features
"""
from abc import ABCMeta, abstractmethod
import typing
import functools


class Comparable(metaclass=ABCMeta):
    """
    Any class that is comparable
    """
    @abstractmethod
    def __lt__(self,other:typing.Any)->bool:
        """ """

ComparableType=typing.TypeVar("ComparableType",bound=Comparable)


T=typing.TypeVar('T')

# a typevar for an entire parameter list pattern
# usage fnX(*args:PS.args,**kwargs:PS.kwargs)
PS=typing.ParamSpec('PS')

def deco(cls):
    """
    decorate the given class
    """
    @functools.wraps(cls,updated=())
    class Modified(cls):
        """
        stand-in class
        """
        def addedFunc(self):
            """
            new function added to the mimic class
            """
    return Modified

class testDecoratorClass:
    """
    a decorator implementation via a class
    """
    def __init__(self,
        decoType:typing.Type,
        compatibleTypes:typing.Optional[typing.Type]=None):
        """ """
        self.type:typing.Type=decoType
        self.compatibleTypes:typing.Optional[typing.Type]=compatibleTypes
    def __call__(self,cls):
        callType=self.type
        if self.compatibleTypes is not None:
            compatibleTypes=self.compatibleTypes
        else:
            compatibleTypes=self.type
        @functools.wraps(cls,updated=())
        class Wrapper(cls):
            """
            wrap the class
            """
            _elementType_=callType
            _elementCompatibleTypes_=compatibleTypes
            @classmethod
            def _elementFactory_(
                cls,
                x:compatibleTypes # type: ignore
                )->callType: # type: ignore
                """
                Add a member method to create elements
                """
                return callType(x)
        return Wrapper


def test():
    """
    run whatever test we're testing
    """
    @testDecoratorClass(int,str)
    class MyClass:
        """
        sample class
        """
        def whatever(self):
            """
            sample method
            """

    mc=MyClass()
    _=mc._elementFactory_("10") # pylint: disable=no-member,protected-access
    print(mc)

test()
