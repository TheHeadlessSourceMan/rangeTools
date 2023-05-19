"""
A set of disconnected ranges
"""
import typing
from rangeTools import Range,NumberLikeT


class Ranges(typing.Generic[NumberLikeT]):
    """
    A set of disconnected ranges
    """
    def __init__(self,
        ranges:typing.Union[None,Range,typing.Iterable[Range[NumberLikeT]]]=None,
        center:typing.Union[None,float]=None):
        """ """
        self._ranges:typing.List[Range]=[]
        if ranges is not None:
            self.append(ranges)
        Range.__init__(self,None,None,center)

    def __iter__(self)->typing.Iterator[Range]:
        return self._ranges.__iter__()

    def append(self,ranges:typing.Union[Range,typing.Iterable[Range]])->None:
        """
        Add one or more range objects.

        NOTE: will reorder and compress where possible eg
            Ranges.append([Range(5-9),Range1(3-5),Range(1-2)])
            will contain
            [Range(1-2),Range(3-9)]
        """
        if isinstance(ranges,Range) and not isinstance(ranges,Ranges):
            ranges=[ranges]
        for r in ranges:
            # TODO: fit it in, expanding groups as necessary
            raise NotImplementedError()

    @property
    def minimum(self)->float:
        """
        return the minimumimum of all ranges
        """
        acc=None
        for r in self._ranges:
            if acc is None or r.minimum<acc:
                acc=r.minimum
        if acc is None:
            acc=0
        return acc

    @property
    def maximum(self)->float:
        """
        return the maximumimum of all ranges
        """
        acc=None
        for r in self._ranges:
            if acc is None or r.maximum>acc:
                acc=r.maximum
        if acc is None:
            acc=0
        return acc

    def contains(self,other:typing.Union["Range",float])->bool:
        if not isinstance(other,Range):
            other=float(other)
        for r in self._ranges:
            if r.contains(other):
                return True
        return False

    def __cmp__(self,
        other:typing.Union[float,"Range"]
        )->typing.Optional[float]:
        """ """
        raise ArithmeticError()

    def __add__(self,
        other:typing.Union[float,"Range"]
        )->"Range":
        raise ArithmeticError()

    def __div__(self,
        other:typing.Union[float,"Range"]
        )->typing.Union[float,"Range"]:
        raise ArithmeticError()
