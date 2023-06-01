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
        ranges:typing.Union[None,Range,typing.Iterable[Range]]=None):
        """ """
        self._ranges:typing.List[Range]=[]
        if ranges is not None:
            self.append(ranges)

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
            return 0.0
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
            return 0.0
        return acc

    def contains(self,other:typing.Union["Range",float])->bool:
        """
        This is the same as
            getRange(other) is not None
        """
        return self.getRange(other) is not None
    
    def getRange(self,item:typing.Union["Range",float])->typing.Optional[Range]:
        """
        Get the first range in the list that contains the given item.
        If not in any of the ranges, returns None.
        """
        for r in self._ranges:
            if r.contains(item):
                return r
        return None
    
    def getNearestRange(self,item:typing.Union["Range",float])->Range:
        """
        Get the first range in the list that contains the given item.
        If not in any of the ranges, returns the one with the edge closest to item.
        
        If there are no ranges raises exception
        """
        if not self._ranges:
            raise IndexError('There are no ranges')
        ret=self.getRange(item)
        if ret is not None:
            return ret
        bestVal=0.0
        for range in self._ranges:
            val=min(abs(float(range.low-item)),abs(float(range.high-item)))
            if ret is None or val<bestVal:
                bestVal=val
                ret=range
        return ret # type:ignore

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
