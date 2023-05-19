"""
Specify ranges in timedelta form, for example "3-5 days"
"""
import typing
import re


class NumberLike(typing.Protocol):
    def __sub__(self,other:typing.Any)->"NumberLike": ...
    def __add__(self,other:typing.Any)->"NumberLike": ...
    def __mul__(self,other:typing.Any)->"NumberLike": ...
    def __truediv__(self,other:typing.Any)->"NumberLike": ...
    def __floordiv__(self,other:typing.Any)->"NumberLike": ...
    def __lt__(self, __other:typing.Any) -> bool: ...
    def __gt__(self, __other:typing.Any) -> bool: ...
    def __le__(self, __other:typing.Any) -> bool: ...
    def __ge__(self, __other:typing.Any) -> bool: ...
    def __repr__(self) -> str: ...


UnitsType=typing.Any

RangeCompatible=typing.Union[NumberLike,str]

NumberLikeT=typing.TypeVar("NumberLikeT",bound=NumberLike)
class Range(typing.Generic[NumberLikeT]):
    """
    A range of number-like values
    """

    RANGE_RE=r"""[\s\[\(]*
        (?P<from>[\-]?([0-9]|([.][0-9]))+(\s*[^;:,-.=|]+)?)
        (?P<sep>((\.+)|(-+)|(\s*))
            ([;:,|]|[.]{2,99}|[-]{2,99}|([-]\s)|(=>)|(->)|([.]\s))?\s*
        )
        (?P<to>[^\]\)]+).*"""

    def __init__(self,
        low:typing.Optional[NumberLikeT],
        high:typing.Optional[NumberLikeT]=None,
        step:typing.Optional[NumberLikeT]=None,
        center:typing.Optional[NumberLikeT]=None,
        elementFactory:typing.Optional[
            typing.Callable[[typing.Union[NumberLikeT,str,None]],NumberLikeT]
            ]=None,
        lowInclusive:bool=True,
        highInclusive:bool=False):
        """
        :low: the low value of the range
        :high: the high value of the range (if None, same as low)
        :lowInclusive: is comparison >low or >=low
        :highInclusive: is comparison <high or <=high
        """
        if elementFactory is None:
            def f(x:typing.Union[NumberLikeT,str,None]=None)->NumberLikeT:
                if x is None:
                    x=0
                elif isinstance(x,str):
                    x=float(x)
                return x
            elementFactory=f
        self.elementFactory=elementFactory
        self.low:NumberLikeT=elementFactory() if low is None else low
        self.high:NumberLikeT=self.low if high is None else high
        self.lowInclusive:bool=lowInclusive
        self.highInclusive:bool=highInclusive
        self._center:typing.Union[None,NumberLikeT]=None
        self.step:NumberLikeT=step if step is not None else elementFactory(1)
        if center is not None:
            self.center=center

    @property
    def minimum(self)->"NumberLikeT":
        """
        alias of low
        """
        return self.low
    @property
    def maximum(self)->"NumberLikeT":
        """
        alias of high
        """
        return self.high

    def _createSameType(self,
        minimum:typing.Optional[NumberLikeT]=None,
        maximum:typing.Optional[NumberLikeT]=None,
        step:typing.Optional[NumberLikeT]=None,
        center:typing.Optional[NumberLikeT]=None,
        elementFactory:typing.Optional[
            typing.Callable[[typing.Union[NumberLikeT,str,None]],NumberLikeT]
            ]=None
        )->"Range[NumberLikeT]":
        """
        Create a new class with the same type as this one
        """
        return type(self)(minimum,maximum,step,center,elementFactory)

    def __add__(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->"Range[NumberLikeT]":
        """
        Adding assumes that the values are contiguious, not parallel.
            eg 2days+1day=3days
            or TimeDeltaRange(1day,2day)+TimeDeltaRange(2day,3day)
            equals TimeDeltaRange(3day,5day)
            meaning, it takes 1-2days to drywall, then 2-3days to paint
                so the job should be finished in 3-5 days
        """
        newRange:typing.List[typing.Optional[NumberLikeT]]=[None,None,None]
        if isinstance(other,Range):
            newRange=[min(self.minimum,other.minimum),
                max(self.maximum,other.maximum),
                self._center]
            if other._center is not None:
                if self._center is not None:
                    # TODO: I think this is right(??)
                    newRange[2]=(self.center+other.center)/2 # type: ignore
                else:
                    newRange[2]=other.center
        else:
            if self._center:
                newRange=[self.minimum+other,
                    self.maximum+other,
                    self._center+other]
            else:
                newRange=[self.minimum+other,
                    self.maximum+other,
                    self._center]
        return self.__class__(minimum=newRange[0],maximum=newRange[1],center=newRange[2])
    def __add__(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        returns the maximum extents of this with other range(s)
        """
        return self.maximized(otherRanges)

    def __other_add_style__(self,other:NumberLikeT)->"Range[NumberLikeT]":
        """
        Range(1-10)+3=Range(4-13)
        """
        if self._center is not None:
            return self._createSameType(self.minimum+other,self.maximum+other,center=self._center+other)
        return self._createSameType(self.minimum+other,self.maximum+other)

    def __sub__(self,other:NumberLikeT)->"Range[NumberLikeT]":
        """
        Range(5-7)-3=Range(2-4)
        """
        if self._center is not None:
            return self._createSameType(self.minimum-other,self.maximum-other,center=self._center-other)
        return self._createSameType(self.minimum-other,self.maximum-other)
    def __sub__(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        returns the minimum extents of this with other range(s)
        """
        return self.minimized(otherRanges)

    def shift(self,other:NumberLikeT)->"Range[NumberLikeT]":
        """
        Shift the entire range relative to its current position

        Range(5-7).shift(-3)=Range(2-4)
        """
        return self+other

    def copy(self)->"Range[NumberLikeT]":
        """
        Create a new copy of this item
        """
        if self._center is not None:
            return self._createSameType(self.minimum,self.maximum,self._center)
        return self._createSameType(self.minimum,self.maximum)

    def copy(self)->'Range[NumberLikeT]':
        """
        Create a copy of this object
        """
        other=Range(self.low,self.high,self._valueClass,self.lowInclusive,self.highInclusive)
        if self._center is not None:
            other.center=self._center
        return other

    def contains(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->bool:
        """
        determinimume if this contains a timedelta or entirely contains another range

        Useful for things like determinimuming if a specified incident will
        occour during this operation

        Examples:
            TimeDeltaRange(1day,3day).contains(2day)
        """
        if isinstance(other,Range):
            return other.minimum>=self.minimum and other.maximum<=self.maximum
        return other>=self.minimum and other<=self.maximum

    @classmethod
    def __subclasscheck__(cls,subclass:type):
        if subclass is range:
            return True
        return False

    @property
    def start(self)->NumberLikeT:
        """
        same as minimum
        """
        return self.minimum

    @property
    def stop(self)->NumberLikeT:
        """
        same as maximum
        """
        return self.maximum

    @property
    def center(self)->NumberLikeT:
        """
        center is the midpoint between maximum and minimum,
        but can be manually overridden
        (to un-override, set center=None)

        NOTE: center itself can be a TimeDeltaRange... which can in turn
        have a center that is a TimeDeltaRange...  This construct would be
        useful for things such as
            AbsoluteLimits.center=WarningLimits
                WarningLimits.center=NormalOperatingLimits
                    NormalOperatingLimits.center=idealAmount
        """
        if self._center is not None:
            return self._center
        return self.average
    @center.setter
    def center(self,center:typing.Optional[NumberLikeT])->None:
        self._center=center

    def containedBy(self,other:"Range[NumberLikeT]")->bool:
        """
        determinimume if this is contained by another a TimeDeltaRange

        Useful for things like determinimuming if a specified incident will
        occour during this operation
        """
        return other.contains(self)

    def union(self,
        other:typing.Union[
            "Range[NumberLikeT]",
            NumberLikeT,
            typing.Iterable[NumberLikeT]]
        )->"Range[NumberLikeT]":
        """
        creates a new TimeDeltaRange that encomasses both this timedelta and other(s)

        Example:
            TimeDeltaRange(1day,3day).union(TimeDeltaRange(2day,5day))
            creates the overlapping
            TimeDeltaRange(1day,5day)
        """
        ret=None
        if not isinstance(other,self.__class__):
            if hasattr(other,"__iter__"):
                # it is iterable, so loop through each item and build it up
                it:typing.Iterable[NumberLikeT]=other # type: ignore
                other=self
                for item in it:
                    other=other.union(item)
                return other
            else:
                other=self.__class__(other) # type: ignore
        newminimum=min(other.minimum,self.minimum)
        newmaximum=max(other.maximum,self.maximum)
        ret=self.__class__(newminimum,newmaximum)
        if self._center is not None or other._center is not None: # pylint: disable=protected-access
            ret.center=(self.center+other.center)/2 # type: ignore
        return ret

    def centerDelta(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->NumberLikeT:
        """
        determinimume how far a value is from the center

        Useful for things like determinimuming how close a specified incident is
        to the ideal.

        Examples:
            TimeDeltaRange(1day,3day,2.5day).centerDelta(2day)
            would give you -0.5day
        """
        if isinstance(other,Range):
            other=other.center
        return other-self.center

    def __cmp__(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->typing.Optional[NumberLikeT]:
        """
        determinimume if this exactly equals, is greater than, or less than another

        NOTE: returns None when not equal, yet < and > are indeterminimumate
            Eg TimeDeltaRange(1day,3day)>TimeDeltaRange(2day,5day) is indeterminimumate
        """
        ret:typing.Optional[NumberLikeT]=None
        if isinstance(other,Range):
            if other.minimum==self.minimum and other.maximum==self.maximum:
                if other.center==self.center:
                    ret=self.elementFactory("")
            else:
                if other.minimum>self.maximum:
                    ret=self.maximum-other.minimum
                if other.maximum<self.minimum:
                    if ret:
                        ret=None # just went indeterminimumate
                    else:
                        ret=other.maximum-self.minimum
        else:
            if other<self.minimum:
                ret=other-self.minimum
            elif other>self.maximum:
                ret=other-self.maximum
            else:
                ret=self.elementFactory("")
        return ret

    def __truediv__(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->typing.Union[float,"Range[NumberLikeT]"]:
        """
        multiply/divide by a scalar results in a timedelta,
        but multiply/divide by a timedelta results in a scalar.
            Eg 6day/3=2day, but
            Eg 6day/3day=2
        """
        if not isinstance(other,self.__class__):
            return self.__class__(
                self.minimum/other,self.minimum/other,
                None if self._center is None else self._center/2)
        return (self.maximum-self.minimum)/(other.maximum-other.minimum) # type: ignore

    @property
    def tolerance(self)->NumberLikeT:
        """
        The tolerance as in value +/- tolerance

        :raises ValueError: if center point is overridden and therefore +/- tolerances cannot be expressed as a single value
        """
        if self._center is not None and self._center!=self.maximum-self.minimum:
            raise ValueError('Range with manually-overridden center point cannot be expressed as "value +/- tolerance"')
        return self.center-self.minimum
    @tolerance.setter
    def tolerance(self,tolerance:typing.Union[str,NumberLikeT,typing.Tuple[NumberLikeT,NumberLikeT]]):
        """
        can assign by:
            tolerance amount:  self.tolerance=1.5
            value+tolernace tuple:  self.tolerance=(5,1.5)
            or string: self.tolerance="5 +/- 1.5"
        """
        if hasattr(tolerance,'__sub__'):
            self.minimum=self.center-tolerance
            self.maximum=self.center+tolerance
        elif isinstance(tolerance,tuple):
            self.center=tolerance[0]
            self.minimum=self.center-tolerance[1]
            self.maximum=self.center+tolerance[1]
        else:
            self.toleranceString=(str(tolerance))

    @property
    def span(self)->NumberLikeT:
        """
        this is exactly the same as self.maximum-self.minimum
        """
        return self.maximum-self.minimum
    @span.setter
    def span(self,span:NumberLikeT):
        """
        Setting span will leave minumum unchanged and then make
            maximum=minimum+span

        NOTE: setting the span could clobber user-defined self.center
        """
        self.maximum=self.minimum+span
        if self._center is not None:
            if self._center>self.maximum:
                self._center=self.maximum

    def __iter__(self)->typing.Generator[NumberLikeT,None,None]:
        return self.iterate()
    def iterate(self,
        partSize:typing.Optional[NumberLikeT]=None
        )->typing.Generator[NumberLikeT,None,None]:
        """
        if partSize is None, uses self.step (which is exactly what that value is for anyway)

        NOTE: generates discrete values.  if you want a series of ranges, consider iterateRanges, iterateEvenly, or iterateWithGaps
        """
        if partSize is None:
            partSize=self.step
        if self.minimum==self.maximum:
            yield self.minimum
            return
        v=self.minimum
        while v<self.maximum:
            yield v
            v+=partSize

    def maxParts(self,
        partSize:NumberLikeT)->int:
        """
        calculate the maximum whole number of parts that can
        fit within this range eg
            self.span=10
            self.maxParts(3)
        gives you
            3

        NOTE: you can also use remainder() to get how much is left
        """
        return self.span//partSize

    def remainder(self,
        partSize:NumberLikeT,
        numParts:typing.Optional[int]=None
        )->NumberLikeT:
        """
        given a certain number of parts, calculate
        how much space remains.
        That is, if self.span=10 and numParts=3

        If numParts is not specified, uses self.maxParts(partSize)
        """
        if numParts is None:
            numParts=self.maxParts(partSize)
        return self.span-(partSize*numParts)

    def gapSize(self,
        partSize:typing.Optional[NumberLikeT]=None,
        numParts:typing.Optional[int]=None
        )->NumberLikeT:
        """
        given a part size, calculate the gap size

        if partSize is None, uses self.step
        """
        if partSize is None:
            partSize=self.step
        if numParts is None:
            numParts=self.maxParts(partSize)
        remainder=self.remainder(partSize,numParts)
        return remainder/max(1,numParts-1)

    def iterateRanges(self,
        partSize:typing.Optional[NumberLikeT]=None
        )->typing.Generator["Range[NumberLikeT]",None,None]:
        """
        if partSize is None, uses self.step (which is exactly what that value is for anyway)
        """
        if partSize is None:
            partSize=self.step
        if self.minimum==self.maximum:
            yield self
            return
        last:NumberLikeT=self.minimum
        while True:
            current:NumberLikeT=last+partSize
            yield self.__class__(last,current)
            last=current

    def iterateEvenly(self,numParts:int)->typing.Generator["Range[NumberLikeT]",None,None]:
        """
        Iterates evenly across an item.
        (Each item.span will be self.span/numParts)

        Useful for things like:
            PicketFence(maximum=20).iterateEvenly(5)
        gives
            Range(0-4),Range(5-9),Range(10-14),Range(14-19)
        """
        if self.minimum==self.maximum:
            yield self
            return
        partSize:NumberLikeT=self.span/numParts
        last:NumberLikeT=self.minimum
        current:NumberLikeT=partSize
        while current<self.maximum:
            yield self.__class__(last,current)
            last=current
            current+=partSize

    def iterateWithGaps(self,
        partSize:typing.Optional[NumberLikeT]=None
        )->typing.Generator["Range[NumberLikeT]",None,None]:
        """
        Generates a series of gaps between elements

        Useful for things like:
            PicketFence(maximum=10,step=3).iterateGaps()
        generates:
            [0-2],[2-2.5],[2.5-5.5],[5.5-6.0],[]

        if partSize is None, uses self.step (which is exactly what that value is for anyway)

        NOTE: generates items of the form [part,gap,part,gap,part],
            always starts annd ends with a part
        """
        if partSize is None:
            partSize=self.step
        if self.span<=partSize:
            yield self
            return
        numParts=self.maxParts(partSize)
        gapSize=self.gapSize(partSize,numParts)
        last:NumberLikeT=self.minimum
        current:NumberLikeT=partSize
        while current<self.maximum:
            yield self.__class__(last,current)
            last=current
            current+=gapSize
            if current>=self.maximum:
                return
            yield self.__class__(last,current)
            last=current
            current=current+partSize # type: ignore

    @property
    def toleranceString(self)->str:
        """
        same as getToleranceString() with default args
        """
    @toleranceString.setter
    def toleranceString(self,toleranceString:str):
        self._center=None
        val_l:typing.List[str]=[]
        tol_l:typing.List[str]=[]
        doneVal=False
        for c in toleranceString:
            if not doneVal:
                if c.isdecimal():
                    val_l.append(c)
                doneVal=True
            else:
                if c.isdecimal():
                    tol_l.append(c)
                elif tol_l: # end of tolerance
                    break
        val=self.elementFactory(''.join(val_l))
        tol=self.elementFactory(''.join(tol_l))
        self.minimum=val-tol
        self.maximum=val+tol
    def getToleranceString(self,plusMinusSeparator=' +/- ')->str:
        """
        A center+tolerance string like
        100 +/- 5

        :raises ValueError: if center point is overridden and therefore +/- tolerances cannot be expressed as a single value
        """
        return str(self.center)+plusMinusSeparator+str(self.tolerance)

    @property
    def rangeFormatted(self)->str:
        """
        get this Range formatted like a python range built-in type (start,stop,step) form
        like you'd use in
            for(x in range(10))
            for(x in range(0,10))
            for(x in range(0,10,1))
        """
        if self.step!=1:
            return 'range(%s,%s,%s)'%(str(self.start),str(self.stop),str(self.step))
        if self.minimum!=0:
            return 'range(%s,%s)'%(str(self.start),str(self.stop))
        return 'range(%s)'%(str(self.stop))

    def formatMinMax(self,sep:str=' - ')->str:
        """
        Format as string something like: "min - max"

        :param sep: what goes between min and max, defaults to ' - '
        :type sep: str, optional
        """
        return f'{self.min}{sep}{self.max}'

    @property
    def units(self)->typing.Optional[UnitsType]:
        """
        If the range has units associted with it, return them
        """
        if hasattr(self.low,'units'):
            return self.low.units
        return None

    def assign(self,
        low:NumberLikeT,high:typing.Optional[NumberLikeT]=None,
        units:typing.Optional[UnitsType]=None,
        lowInclusive:typing.Optional[bool]=None,highInclusive:typing.Optional[bool]=None
        )->None:
        """
        assign the values of this range

        :low: the low value of the range
        :high: the high value of the range (if None, same as low)
        :units: units that low and high are in
        :lowInclusive: is comparison >low or >=low
        :highInclusive: is comparison <high or <=high
        """
        if lowInclusive is not None:
            self.lowInclusive=lowInclusive
        if highInclusive is not None:
            self.highInclusive=highInclusive
        if isinstance(low,str) and not isinstance(high,str):
            if isinstance(self.RANGE_RE,str):
                self.RANGE_RE=self.RANGE_RE.replace(' ','').replace('\n','')
                self.RANGE_RE=re.compile(self.RANGE_RE,re.DOTALL)
            m=self.RANGE_RE.match(low)
            if m is None:
                raise Exception('ERR: unable to parse range string "%s"'%low)
            low=m.group('from')
            high=m.group('to')
            #sep=None
            #sep=m.group('sep')
            #print('RE:\n\t%s\n\t%s\n\t%s'%(low,sep,high))
        elif isinstance(low,Range):
            high=low.high
            low=low.low
        elif isinstance(low,(list,tuple)):
            high=max(low)
            low=min(low)
        elif high is None:
            high=low
        if self._valueClass is not None:
            if units is None:
                units=self.units
            if not isinstance(low,self._valueClass):
                low=self._valueClass(value=low,units=units)
            if not isinstance(high,self._valueClass):
                high=self._valueClass(value=high,units=units)
        self.low=low
        self.high=high

    @property
    def average(self)->NumberLikeT:
        """
        average value of this range
        """
        return (self.low+self.high)/2.0

    def minimize(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->None:
        """
        minimize this with other range(s)
        """
        if isinstance(otherRanges,Range):
            otherRanges=(otherRanges,)
        for anotherRange in otherRanges:
            if anotherRange.low==self.low:
                self.lowInclusive=not (anotherRange.lowInclusive or self.lowInclusive)
            elif anotherRange.low>self.low:
                self.low=anotherRange.low
                self.lowInclusive=anotherRange.lowInclusive
                if self.low==self.high:
                    self.low=self.high
                    self.lowInclusive=self.highInclusive
                elif self.low>self.high:
                    self.low=self.high
                    self.lowInclusive=False
                    break
            if anotherRange.high==self.high:
                self.highInclusive=anotherRange.highInclusive or self.highInclusive
            elif anotherRange.high>self.high:
                self.high=anotherRange.high
                self.highInclusive=anotherRange.highInclusive
    def minimized(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        returns the minimum extents of this with other range(s)
        """
        other=self.copy()
        other.minimize(otherRanges)
        return other

    def maximize(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->None:
        """
        maximize this with other range(s)
        """
        if isinstance(otherRanges,Range):
            otherRanges=(otherRanges,)
        for anotherRange in otherRanges:
            if anotherRange.low==self.low:
                self.lowInclusive=anotherRange.lowInclusive or self.lowInclusive
            elif anotherRange.low<self.low:
                self.low=anotherRange.low
                self.lowInclusive=anotherRange.lowInclusive
            if anotherRange.high==self.high:
                self.highInclusive=anotherRange.highInclusive or self.highInclusive
            elif anotherRange.high>self.high:
                self.high=anotherRange.high
                self.highInclusive=anotherRange.highInclusive
    def maximized(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        returns the maximum extents of this with other range(s)
        """
        other=self.copy()
        other.maximize(otherRanges)
        return other

    def intersect(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->None:
        """
        Perform a boolean intersection between this range and other range(s)
        """
        self.minimize(otherRanges)
    def intersection(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        Perform a boolean intersection between this range and other range(s)
        """
        other=self.copy()
        other.intersect(otherRanges)
        return other
    def intersection(self,
        other:typing.Union[NumberLikeT,"Range[NumberLikeT]"]
        )->typing.Optional["Range[NumberLikeT]"]:
        """
        creates a new TimeDeltaRange that fulfils both the range of this item and another

        Example:
            TimeDeltaRange(1day,3day).intersection(TimeDeltaRange(2day,5day))
            creates the overlapping
            TimeDeltaRange(2day,3day)

        Can return None if the two do not overlap!

        NOTE: any user-defined centers could be lost!
        """
        ret=None
        if not isinstance(other,Range):
            other=self.__class__(other)
        newminimum=max(other.minimum,self.minimum)
        newmaximum=min(other.maximum,self.maximum)
        if newminimum<=newmaximum:
            ret=self.__class__(newminimum,newmaximum)
            if self._center is not None or other._center is not None: # pylint: disable=protected-access
                cent:typing.Optional[NumberLikeT]
                if self._center is not None:
                    cent=self._center
                    if other._center is not None: # pylint: disable=protected-access
                        centOther=other._center # pylint: disable=protected-access
                        cent=(cent+centOther)/2 # type: ignore
                else:
                    cent=other._center # pylint: disable=protected-access
                if cent is not None and cent>=newminimum and cent<=newmaximum:
                    ret.center=cent
        return ret

    def differ(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->None:
        """
        Perform a boolean intersection between this range and other range(s)
        """
        self.minimize(otherRanges)
    def difference(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        Perform a boolean difference between this range and other range(s)
        """
        other=self.copy()
        other.differ(otherRanges)
        return other

    def unite(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->None:
        """
        Perform a boolean intersection between this range and other range(s)
        """
        self.minimize(otherRanges)
    def union(self,otherRanges:typing.Union['Range',typing.Iterable['Range']])->'Range':
        """
        Perform a boolean intersection between this range and other range(s)
        """
        other=self.copy()
        other.unite(otherRanges)
        return other

    @property
    def span(self)->NumberLikeT:
        """
        how wide a span is covered by this range
        """
        return self.high-self.low

    def contains(self,value:NumberLikeT)->bool:
        """
        if value is entirely contained in the range
        """
        if isinstance(value,Range):
            return value.low>=self.low and value.high<=self.high
        if not isinstance(value,self._valueClass):
            value=self._valueClass(value=value)
        return self.low<=value<=self.high

    def overlaps(self,value:NumberLikeT)->bool:
        """
        if value is at all within the range
        does the same thing as contains() unless value is a range
        """
        if isinstance(value,Range):
            if value.low>=self.low and value.low<=self.high:
                return True
            if value.high>=self.low and value.high<=self.high:
                return True
            return False
        if not isinstance(value,self._valueClass):
            value=self._valueClass(value=value)
        return self.low<=value<=self.high

    def __repr__(self)->str:
        """
        String representation of this range

        Prefers, in order:
            1) formatMinMax (eg "1 - 10")
            2) toleranceString ("5 +/- 2")
            3) rangeFormatted string ("range(1,3,12)")
        """
        try:
            pass # return self.getToleranceString()
        except ValueError:
            pass
        return self.rangeFormatted


a=Range[float](1.0,2.0)
b=Range[float](2.0,4.0)
print(a,b,a+b)