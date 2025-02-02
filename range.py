"""
Specify ranges in timedelta form, for example "3-5 days"
"""
import typing
import collections.abc
import math
import regex # type: ignore
from rangeTools.numberLike import NumberLike


UnitsType=typing.Any

RangeCompatible=typing.Union[NumberLike,str]

def asRange(
    rangeCompatible:typing.Union["Range",RangeCompatible]
    )->"Range":
    """
    Convert something to a Range.

    If it already is a Range, simply return it
    """
    if isinstance(rangeCompatible,Range):
        return rangeCompatible
    return Range(rangeCompatible)

NumberLikeT=typing.TypeVar("NumberLikeT",bound=NumberLike) # A Range's low and high values will be of this type # noqa: E501 # pylint: disable=line-too-long
NumberLikeCompatibilityT=typing.TypeVar("NumberLikeCompatibilityT") # when setting a Range's low and high values, these types will be acceptable # noqa: E501 # pylint: disable=line-too-long


class Range(typing.Generic[NumberLikeT,NumberLikeCompatibilityT]):
    """
    A range of number-like values

    This is generally a low/high, min/max, start/stop type of idea, but
    to ensure compatibility with python ranges (eg, for i in range(1,10,2)),
    there is also a step member.
    """

    RANGE_RE=r"""[\s\[\(]*
        (?P<from>[\-]?(([0-9]+([.][0-9]+)?)|([.][0-9]+)))
        ((?P<sep>((\.+)|(-+)|(\s*))
            ([;:,|]|[.]{2,99}|[-]{2,99}|([-]\s)|(=>)|(->)|([.]\s))?\s*
        )
        (?P<to>[^\]\)]+).*)?
        """.replace('\r','').replace('\n','').replace(' ','')

    # ---- Object housekeeping ----
    def __init__(self,
        low:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT]]],
        high:typing.Union[None,NumberLikeT,NumberLikeCompatibilityT]=None,
        step:typing.Union[None,NumberLikeT,NumberLikeCompatibilityT]=None,
        center:typing.Union[None,NumberLikeT,NumberLikeCompatibilityT]=None,
        lowInclusive:bool=True,
        highInclusive:bool=False,
        elementFactory:typing.Optional[
            typing.Callable[[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT]],
                NumberLikeT]
            ]=None,
        ):
        """
        :low: the low value of the range
        :high: the high value of the range (if None, same as low)
        :lowInclusive: is comparison >low or >=low
        :highInclusive: is comparison <high or <=high
        """
        self._low:NumberLikeT
        self._high:NumberLikeT
        self._center:typing.Optional[NumberLikeT]=None
        self._step:typing.Optional[NumberLikeT]=None
        if elementFactory is None:
            def f(x:typing.Any)->NumberLikeT:
                if x is None:
                    x=0
                elif isinstance(x,str):
                    x=float(x)
                return x
            elementFactory=f
        self.elementFactory:typing.Callable[
            [typing.Union[NumberLikeT,NumberLikeCompatibilityT]],
            NumberLikeT]=elementFactory
        self.lowInclusive:bool=lowInclusive
        self.highInclusive:bool=highInclusive
        if step is not None:
            self.step=step # type:ignore
        if center is not None:
            self.center=center # type:ignore
        self.assign(low,high)

    @classmethod
    def __subclasscheck__(cls,subclass:type)->bool:
        if subclass is range:
            return True
        return False

    def assign(self,
        low:typing.Union[
            float,
            NumberLikeT,
            NumberLikeCompatibilityT,
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT]]],
        high:typing.Union[
            None,
            float,
            NumberLikeT,
            NumberLikeCompatibilityT]=None):
        """
        Assign the value of this range.
        """
        if isinstance(low,str):
            d=regex.match(self.RANGE_RE,low,regex.MULTILINE).groupdict()
            low=float(d.group('from'))
            if high is None:
                h=d.get('to')
                if h is not None:
                    high=float(h)
                else:
                    high=low
            self.low=typing.cast(NumberLikeT,low)
            self.high=typing.cast(NumberLikeT,high)
        elif isinstance(low,collections.abc.Iterable):
            self.low=min(low)
            self.high=max(low)
        else:
            self.low=low # type:ignore
            if high is not None:
                self.high=high # type:ignore
            else:
                self.high=low # type:ignore

    def copy(self)->"Range[NumberLikeT,NumberLikeCompatibilityT]":
        """
        Create a new copy of this item
        """
        return self.__class__(
            self.low,
            self.high,
            self.step,
            self.center,
            self.lowInclusive,
            self.highInclusive,
            self.elementFactory)

    @classmethod
    def asRanges(cls,
        ranges:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT,
                'Range[NumberLikeT,NumberLikeCompatibilityT]']]]
        )->typing.Generator[
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            None,None]:
        """
        Given one or more numbers and/or number ranges,
        yield up a series of Range objects
        """
        if isinstance(ranges,Range) \
            or not hasattr(ranges,'__iter__'):
            #
            ranges=[ranges]
        for rangeItem in ranges:
            if not isinstance(rangeItem,Range):
                rangeItem=asRange(rangeItem) # type: ignore
            yield rangeItem

    def split(self,
        sectionSize:typing.Union[
            None,NumberLikeT,NumberLikeCompatibilityT]=None,
        numSections:typing.Optional[float]=None,
        endSizes:typing.Union[
            None,NumberLikeT,NumberLikeCompatibilityT]=None,
        separatorSizes:typing.Union[
            None,NumberLikeT,NumberLikeCompatibilityT]=None,
        remainderHandling:str="section_stretch",
        yieldEnds:bool=True,
        yieldSections:bool=True,
        yieldSeparators:bool=True
        )->typing.Generator[
            'Range[NumberLikeT,NumberLikeCompatibilityT]',None,None]:
        """
        Very versatile function to split up a range into range parts.

        :sectionSize: the size of the parts to split into
            must specify this OR numParts.
            if neither is specified, use self.step as size
        :numSections: the number of equally-sized parts to split into
            must specify this OR size.
            if neither is specified, use self.step as size
        :endSizes: if specified, will generate ranges of this size on both ends
        :separatorSizes: if specified, will generate separators of this size
            between all sections
        :remainderHandling: how to treat remainder
            "remainder_section" = create an extra section with remainder
            "section_stretch" = stretch the existing ranges to take remainder
            "section_shrink" = add an extra section and shrink
                the difference across all sections
            "section_stretch_shrink" = stretch or shrink(by removing one)
                to whichever number of sections is the closest fit
            "total_shrink" = ignore remainder and allow total size to shrink
            "total_grow" = allow total size to grow so there is no remainder
            "total_shrink_grow" = either total_shrink or total_grow, depending
                on which is the closest way to achieve full-sized sections
            NOTE: this is unused for numParts, since what they're doing is
                essentially "stretch"
        :yieldEnds: whether to yield the ends as Range objects (default=True)
        :yieldSections: whether to yield the the sections themselves
            as Range objects (default = True)
        :yieldSeparators: whether to yield the separators between sections
            as Range objects (default = True)

        Example:
            create a 12inch box with 3inch sections, 1/2inch end boards,
            and 1/4inch dividers between sections
                Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25)
            get just the end boards
                Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,yieldEnds=False,yieldSections=False,yieldSeparators)
            get just the separators boards
                Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,yieldEnds=False,yieldSections=False,yieldSeparators=True)
            How many separators are there?
                len(list(Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,yieldEnds=False,yieldSections=False,yieldSeparators=True)))
            How many sections are there?
                len(list(Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,yieldEnds=False,yieldSections=True,yieldSeparators=False)))
            What is the width of the sections?
                for section in Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,yieldEnds=False,yieldSections=True,yieldSeparators=False)))
                    print(section.span)
                    break
            ignore any extra space to keep the box to keep exactly 3inch sections
                Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,remainderHandling='total_shrink')
            just for fun, get the new size after doing that
                Range(Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,remainderHandling='total_shrink')).span
            actually, it's probably more efficient to go off just the end boards
                Range(Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,remainderHandling='total_shrink',yieldEnds=True,yieldSections=False,yieldSeparators=False)).span
            instead of that, take up remainder by keeping exactly 3inch sections, but leave whatever is left over in its own small section
                Range(0,12).split(sectionSize=3,endSizes=0.5,separatorSizes=0.25,remainderHandling='remainder_section')

        TODO: typing is pretty jacked up in this function
        """ # noqa: E501 # pylint: disable=line-too-long
        if endSizes is not None:
            endSizes=typing.cast(NumberLikeT,self.elementFactory(endSizes))
        if separatorSizes is not None:
            separatorSizes=self.elementFactory(separatorSizes)
        remainderSection:typing.Optional[NumberLikeT]=None
        # figure out what the sizes of things will be
        if numSections is not None:
            # using number of sections we have to calculate sectionSize
            # this is simpler because we don't have to mess with remainders!
            if not isinstance(numSections,(float,int)):
                numSections=float(numSections)
            span:NumberLikeT=self.span
            totalSize:NumberLikeT=span
            if endSizes is not None:
                totalSize-=endSizes*2 # type:ignore
            if separatorSizes is not None:
                totalSize-=(separatorSizes*(numSections-1)) # type:ignore
            sectionSize=totalSize/numSections # type:ignore
        else:
            # a section size was specified, so we have to figure out
            # numSections as well as pushing things around if
            # there is a remainder
            if sectionSize is None:
                sectionSize=self.step
            else:
                sectionSize=self.elementFactory(sectionSize)
            totalSize=self.span
            if endSizes is not None:
                totalSize-=endSizes*2 # type:ignore
            if separatorSizes is not None:
                numSectionsExact=\
                    (totalSize+separatorSizes)/\
                    (sectionSize+separatorSizes)
            else:
                numSectionsExact=totalSize/sectionSize
            numSections=math.floor(numSectionsExact)
            remainder:NumberLikeT=\
                sectionSize*(numSectionsExact-numSections) # type:ignore
            if remainder!=0:
                # there is a remainder that must be handled!
                if remainderHandling=='remainder_section':
                    # create a section at the end for the remainder
                    remainderSection=remainder
                elif remainderHandling=='section_stretch':
                    sectionSize+=remainder/numSections # type:ignore
                elif remainderHandling=='section_shrink':
                    # add a section and shrink the size of all
                    numSections+=1
                    if separatorSizes is not None:
                        sectionSize=\
                            ((totalSize+separatorSizes)/numSections)\
                            -separatorSizes # type: ignore
                    else:
                        sectionSize=totalSize/numSections # type:ignore
                elif remainderHandling=='section_stretch_shrink':
                    if remainder/sectionSize>=0.5:
                        # remainder is large so add a new section
                        numSections+=1
                        if separatorSizes is not None:
                            sectionSize=\
                                ((totalSize+separatorSizes)/numSections)\
                                -separatorSizes # type:ignore
                        else:
                            sectionSize=totalSize/numSections # type:ignore
                    else:
                        # remainder is small so stretch existing
                        # sections to fill in
                        sectionSize+=remainder/numSections # type:ignore
                elif remainderHandling=='total_shrink':
                    # simply keep the floor'ed numSections as it stands
                    pass
                elif remainderHandling=='total_grow':
                    numSections+=1
                elif remainderHandling=='total_shrink_grow':
                    if remainder/sectionSize>=0.5:
                        # remainder is large, so grow total size
                        numSections+=1
                    else:
                        # remainder is small, so shrink total size
                        pass
                else:
                    raise NotImplementedError(f'Unknown remainder handling mode "{remainderHandling}"') # noqa: E501 # pylint: disable=line-too-long
        # now that we have a numParts and partSize, we can iterate
        pos=self.min # type:ignore
        if endSizes is not None:
            # the beginning end
            if yieldEnds:
                yield Range(pos,pos+endSizes) # type:ignore
            pos+=endSizes # type:ignore
        for _ in range(numSections): # type:ignore
            if yieldSections:
                yield Range[NumberLikeT,NumberLikeCompatibilityT](
                    pos,pos+sectionSize) # type:ignore
            pos+=sectionSize # type:ignore
            # any separator
            if separatorSizes is not None:
                if yieldSeparators:
                    yield Range(pos,pos+separatorSizes) # type:ignore
                pos+=separatorSizes # type:ignore
        if remainderSection is not None:
            # an extra range to make up the remainder amount
            if yieldSections:
                yield Range(pos,pos+remainderSection) # type:ignore
            pos+=remainderSection # type:ignore
        if endSizes is not None:
            # the ending end
            if yieldEnds:
                yield Range(pos,pos+endSizes) # type:ignore
            pos+=endSizes # type:ignore

    # ---- Values ----
    @property
    def low(self)->NumberLikeT:
        """
        low value of the range
        """
        return self._low
    @low.setter
    def low(self,low:typing.Union[NumberLikeT,NumberLikeCompatibilityT])->None:
        """
        If assigning a low greater than the current high,
        the high will change to equal low
        """
        self._low=self.elementFactory(low)
        if hasattr(self,'_high') and self._low>self._high:
            self._high=self._low
    min=low
    minimum=low
    start=low

    @property
    def high(self)->NumberLikeT:
        """
        high value of the range
        """
        return self._high
    @high.setter
    def high(self,
        high:typing.Union[NumberLikeT,NumberLikeCompatibilityT]
        )->None:
        """
        If assigning a high less than the current low,
        the low will change to equal high
        """
        self._high=self.elementFactory(high)
        if self._high<self._low:
            self._low=self._high
    max=high
    maximum=high
    stop=high

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
    def center(self,
        center:typing.Union[NumberLikeT,NumberLikeCompatibilityT]
        )->None:
        """
        Center point of the range.
        """
        self._center=self.elementFactory(center)

    @property
    def step(self)->NumberLikeT:
        """
        For an incrementing range (like a python range)
        this is the increment step size
        """
        if self._step is None:
            return self.elementFactory(1) # type:ignore
        return self._step
    @step.setter
    def step(self,
        step:typing.Union[NumberLikeT,NumberLikeCompatibilityT]
        )->None:
        """ """
        self._step=self.elementFactory(step)

    @property
    def units(self)->typing.Optional[UnitsType]:
        """
        If the range has units associated with it, return them
        """
        if hasattr(self.low,'units'):
            return self.low.units
        return None

    @property
    def average(self)->NumberLikeT:
        """
        average value of this range
        """
        return typing.cast(NumberLikeT,(self.low+self.high)/2.0)

    @property
    def tolerance(self)->NumberLikeT:
        """
        The tolerance as in value +/- tolerance

        :raises ValueError: if center point is overridden and
        therefore +/- tolerances cannot be expressed as a single value
        """
        if self._center is not None and self._center!=self.high-self.low:
            raise ValueError('Range with manually-overridden center point cannot be expressed as "value +/- tolerance"') # noqa: E501 # pylint: disable=line-too-long
        return typing.cast(NumberLikeT,self.center-self.low)
    @tolerance.setter
    def tolerance(self,
        tolerance:typing.Union[
            str,
            NumberLikeT,
            typing.Tuple[NumberLikeT,NumberLikeT]]
        )->None:
        """
        can assign by:
            tolerance amount:  self.tolerance=1.5
            value+tolerance tuple:  self.tolerance=(5,1.5)
            or string: self.tolerance="5 +/- 1.5"
        """
        if hasattr(tolerance,'__sub__'):
            self.low=typing.cast(NumberLikeT,self.center-tolerance)
            self.high=typing.cast(NumberLikeT,self.center+tolerance)
        elif isinstance(tolerance,tuple):
            self.center=tolerance[0]
            self.low=typing.cast(NumberLikeT,self.center-tolerance[1])
            self.high=typing.cast(NumberLikeT,self.center+tolerance[1])
        else:
            self.toleranceString=(str(tolerance))

    @property
    def span(self)->NumberLikeT:
        """
        this is exactly the same as self.high-self.low
        """
        return typing.cast(NumberLikeT,self.high-self.low)
    @span.setter
    def span(self,span:NumberLikeCompatibilityT):
        """
        Setting span will leave minimum unchanged and then make
            maximum=minimum+span

        NOTE: setting the span could clobber user-defined self.center
        """
        self.high=typing.cast(NumberLikeT,self.low+self.elementFactory(span))
        if self._center is not None:
            if self._center>self.high:
                self._center=self.high

    # ----- Math -----
    def minimize(self,
        otherRanges:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT,
                'Range[NumberLikeT,NumberLikeCompatibilityT]']]]
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        minimize intersection difference with this in regards other range(s)

        returns self to make chaining easier
        """
        for anotherRange in self.asRanges(otherRanges):
            if not isinstance(anotherRange,Range):
                anotherRange=self.__class__(anotherRange)
            if anotherRange.low==self.low:
                self.lowInclusive=not (
                    anotherRange.lowInclusive
                    or self.lowInclusive)
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
                self.highInclusive=\
                    anotherRange.highInclusive \
                    or self.highInclusive
            elif anotherRange.high>self.high:
                self.high=anotherRange.high
                self.highInclusive=anotherRange.highInclusive
        return self
    intersect=minimize
    differ=minimize
    subtract=minimize
    def minimized(self,
        otherRanges:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT,
                'Range[NumberLikeT,NumberLikeCompatibilityT]']]]
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        returns the minimum intersection difference of this with other range(s)
        """
        return self.copy().minimize(otherRanges)
    intersection=minimized
    difference=minimized
    subtraction=minimized

    def maximize(self,
        otherRanges:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT,
                'Range[NumberLikeT,NumberLikeCompatibilityT]']]]
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        maximize this with other range(s)

        returns self to make chaining easier
        """
        for anotherRange in self.asRanges(otherRanges):
            if anotherRange.low==self.low:
                self.lowInclusive=\
                    anotherRange.lowInclusive \
                    or self.lowInclusive
            elif anotherRange.low<self.low:
                self.low=anotherRange.low
                self.lowInclusive=anotherRange.lowInclusive
            if anotherRange.high==self.high:
                self.highInclusive=\
                    anotherRange.highInclusive \
                    or self.highInclusive
            elif anotherRange.high>self.high:
                self.high=anotherRange.high
                self.highInclusive=anotherRange.highInclusive
        return self
    expand=maximize
    add=maximize
    unite=maximize

    def maximized(self,
        otherRanges:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]',
            typing.Iterable[typing.Union[
                NumberLikeT,
                NumberLikeCompatibilityT,
                'Range[NumberLikeT,NumberLikeCompatibilityT]']]]
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        returns the maximum extents of this with other range(s)
        """
        return self.copy().maximize(otherRanges)
    expanded=maximized
    addition=maximized
    union=maximized

    def __add__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]']
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        returns the maximum extents of this with other range(s)
        """
        return self.maximized(other)

    def __sub__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            'Range[NumberLikeT,NumberLikeCompatibilityT]']
        )->'Range[NumberLikeT,NumberLikeCompatibilityT]':
        """
        returns the minimum extents of this with other range(s)
        """
        return self.minimized(other)

    def __truediv__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->typing.Union[
            float,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]:
        """
        multiply/divide by a scalar results in a timedelta,
        but multiply/divide by a timedelta results in a scalar.
            Eg 6day/3=2day, but
            Eg 6day/3day=2
        """
        if not isinstance(other,Range):
            other=self.elementFactory(other)
            center=None
            if self._center is not None:
                center=self._center/2
            return self.__class__(
                low=self.low/other, # type: ignore
                high=self.high/other, # type: ignore
                center=center) # type: ignore
        return (self.high-self.low)\
            /(other.maximum-other.minimum) # type: ignore

    def shift(self,
        other:typing.Union[NumberLikeT,NumberLikeCompatibilityT]
        )->"Range[NumberLikeT,NumberLikeCompatibilityT]":
        """
        Shift the entire range relative to its current position

        :return: self - for easy operation chaining
        """
        other=self.elementFactory(other)
        self.low+=other # type:ignore
        self.high+=other # type:ignore
        return self
    def shifted(self,
        other:typing.Union[NumberLikeT,NumberLikeCompatibilityT]
        )->"Range[NumberLikeT,NumberLikeCompatibilityT]":
        """
        Shift the entire range relative to its current position

        Range(5-7).shifted(-3)=Range(2-4)
        """
        return self.copy().shift(other)

    def centerDelta(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->NumberLikeT:
        """
        determine how far a value is from the center

        Useful for things like determining how close a specified incident is
        to the ideal.

        Examples:
            TimeDeltaRange(1day,3day,2.5day).centerDelta(2day)
            would give you -0.5day
        """
        if isinstance(other,Range):
            other=other.center
        else:
            other=self.elementFactory(other)
        return typing.cast(NumberLikeT,other-self.center)

    def _numberLikeAbs(self,val:NumberLike)->NumberLikeT:
        """
        Utility to perform absolute value on a NumberLike object
        and cast result as NumberLikeT
        """
        if val<0:
            return typing.cast(NumberLikeT,val*(-1))
        return typing.cast(NumberLikeT,val)

    def minimumDistance(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->NumberLikeT:
        """
        determine the distance from the edge of this range
        to the nearest edge of another
        """
        if not isinstance(other,Range):
            if self.contains(other):
                return typing.cast(NumberLikeT,0)
            other=self.elementFactory(other)
            return min(
                self._numberLikeAbs(other-self.high),
                self._numberLikeAbs(other-self.low))
        if self.overlaps(other):
            return typing.cast(NumberLikeT,0)
        return min(
            self._numberLikeAbs(other.high-self.high),
            self._numberLikeAbs(other.high-self.low),
            self._numberLikeAbs(other.low-self.high),
            self._numberLikeAbs(other.low-self.low))
    minDistance=minimumDistance
    distance=minimumDistance

    # --- Comparison Operators ---
    def __lt__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->bool:
        """
        less-than operator
        """
        if isinstance(other,Range):
            return self.high<other.low
        return self.high<self.elementFactory(other)
    def __gt__(self,other:typing.Union[
        NumberLikeT,
        NumberLikeCompatibilityT,
        "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->bool:
        """
        greater-than operator
        """
        if isinstance(other,Range):
            return self.low>other.high
        return self.low>self.elementFactory(other)
    def __le__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->bool:
        """
        The <= operator for ranges means < or overlaps
        """
        if isinstance(other,Range):
            if self<other:
                return True
            return self.overlaps(other)
        return self.high<=self.elementFactory(other)
    def __ge__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->bool:
        """
        The >= operator for ranges means > or overlaps
        """
        if isinstance(other,Range):
            if self>other:
                return True
            return self.overlaps(other)
        return self.low>=self.elementFactory(other)
    def __eq__(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]",
            typing.Any]
        )->bool: # type:ignore
        """
        equals operator
        """
        if isinstance(other,Range):
            return self.high<other.low
        other=self.elementFactory(other)
        return self.high==other \
            and self.low==other \
            and self.lowInclusive \
            and self.highInclusive

    def contains(self,
        other:typing.Union[
            NumberLikeT,
            NumberLikeCompatibilityT,
            "Range[NumberLikeT,NumberLikeCompatibilityT]"]
        )->bool:
        """
        determine if this contains a value or entirely contains another range

        Useful for things like determining if a specified incident will
        occur during this operation

        Examples:
            TimeDeltaRange(1day,3day).contains(2day)
        """
        if isinstance(other,Range):
            return other.low>=self.low and other.high<=self.high
        other=self.elementFactory(other)
        return other>=self.low and other<=self.high
    def containedBy(self,
        other:"Range[NumberLikeT,NumberLikeCompatibilityT]"
        )->bool:
        """
        determine if this is contained by another range

        Useful for things like determining if a specified incident will
        occur during this operation
        """
        return other.contains(self)

    def overlaps(self,
        other:'Range[NumberLikeT,NumberLikeCompatibilityT]'
        )->bool:
        """
        Do we overlap with another range?

        if other is at all within the range
        does the same thing as contains() unless other is a range
        """
        if self.low>=other.low:
            if self.low<=other.high:
                return True
        elif other.high>=self.high:
            return True
        return False
    intersects=overlaps

    # ---- Iteration and access -----
    def __len__(self)->int:
        """
        TODO: Instead of [low,high] should we be doing like iteration?
        """
        return 2
    def __getitem__(self,idx:int)->NumberLikeT:
        if idx==0:
            return self.low
        if idx==1:
            return self.high
        raise IndexError()

    def __iter__(self)->typing.Generator[NumberLikeT,None,None]:
        return self.iterate()
    def iterate(self,
        partSize:typing.Optional[NumberLikeT]=None
        )->typing.Generator[NumberLikeT,None,None]:
        """
        if partSize is None, uses self.step
        (which is exactly what that value is for anyway)

        NOTE: generates discrete values.  If you want a series of ranges,
            consider iterateRanges, iterateEvenly, or iterateWithGaps
        """
        if partSize is None:
            partSize=self.step
        if self.low==self.high:
            yield self.low
            return
        v=self.low
        while v<self.high:
            yield v
            v=typing.cast(NumberLikeT,v+partSize)

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
        return int(self.span//partSize)

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
        return typing.cast(NumberLikeT,self.span-(partSize*numParts))

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
        numParts=numParts-1
        if numParts<1:
            numParts=1
        return typing.cast(NumberLikeT,remainder/numParts)

    def iterateRanges(self,
        partSize:typing.Union[None,NumberLikeT,NumberLikeCompatibilityT]=None
        )->typing.Generator[
            "Range[NumberLikeT,NumberLikeCompatibilityT]",None,None]:
        """
        if partSize is None, uses self.step
        (which is exactly what that value is for anyway)
        """
        if partSize is None:
            partSize=self.step
        if self.low==self.high:
            yield self
            return
        last:NumberLikeT=self.low
        while True:
            current:NumberLikeT=typing.cast(NumberLikeT,last+partSize)
            yield self.__class__(last,current)
            last=current

    def iterateEvenly(self,
            numParts:int
        )->typing.Generator[
            "Range[NumberLikeT,NumberLikeCompatibilityT]",None,None]:
        """
        Iterates evenly across an item.
        (Each item.span will be self.span/numParts)

        Useful for things like:
            PicketFence(maximum=20).iterateEvenly(5)
        gives
            Range(0-4),Range(5-9),Range(10-14),Range(14-19)
        """
        if self.low==self.high:
            yield self
            return
        partSize:NumberLikeT=typing.cast(NumberLikeT,self.span/numParts)
        last:NumberLikeT=self.low
        current:NumberLikeT=partSize
        while current<self.high:
            yield self.__class__(last,current)
            last=current
            current=typing.cast(NumberLikeT,current+partSize)

    def iterateWithGaps(self,
        partSize:typing.Union[None,NumberLikeT,NumberLikeCompatibilityT]=None
        )->typing.Generator[
            "Range[NumberLikeT,NumberLikeCompatibilityT]",None,None]:
        """
        Generates a series of gaps between elements

        Useful for things like:
            PicketFence(maximum=10,step=3).iterateGaps()
        generates:
            [0-2],[2-2.5],[2.5-5.5],[5.5-6.0],[]

        if partSize is None, uses self.step
        (which is exactly what that value is for anyway)

        NOTE: generates items of the form [part,gap,part,gap,part],
            always starts and ends with a part
        """
        if partSize is None:
            partSize=self.step
        if self.span<=partSize:
            yield self
            return
        partSize=self.elementFactory(partSize)
        numParts=self.maxParts(partSize)
        gapSize=self.gapSize(partSize,numParts)
        last:NumberLikeT=self.low
        current:NumberLikeT=partSize
        while current<self.high:
            yield self.__class__(last,current)
            last=current
            current=typing.cast(NumberLikeT,current+gapSize)
            if current>=self.high:
                return
            yield self.__class__(last,current)
            last=current
            current=current+partSize # type: ignore

    # ---- Stringification ----
    def formatMinMax(self,sep:str=' - ')->str:
        """
        Format as string something like: "min - max"

        :param sep: what goes between min and max, defaults to ' - '
        :type sep: str, optional
        """
        return f'{self.low}{sep}{self.high}'

    @property
    def rangeFormatted(self)->str:
        """
        get this Range formatted like a python range built-in
        type (start,stop,step) form like you'd use in
            for(x in range(10))
            for(x in range(0,10))
            for(x in range(0,10,1))
        """
        if self.step!=1:
            return 'range(%s,%s,%s)'%(
                str(self.start),str(self.stop),str(self.step))
        if self.low!=0:
            return 'range(%s,%s)'%(
                str(self.start),str(self.stop))
        return 'range(%s)'%(str(self.stop))

    @property
    def toleranceString(self)->str:
        """
        same as getToleranceString() with default args
        """
        return self.getToleranceString()
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
        val=self.elementFactory(float(''.join(val_l))) # type:ignore
        tol=self.elementFactory(float(''.join(tol_l))) # type:ignore
        self.low=typing.cast(NumberLikeT,val-tol)
        self.high=typing.cast(NumberLikeT,val+tol)
    def getToleranceString(self,plusMinusSeparator=' +/- ')->str:
        """
        A center+tolerance string like
        100 +/- 5

        :raises ValueError: if center point is overridden and
        therefore +/- tolerances cannot be expressed as a single value
        """
        return f'{self.center} {plusMinusSeparator} {self.tolerance}'

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


def test():
    """
    Run the test
    """
    a=Range[float](1.0,2.0)
    b=Range[float](2.0,4.0)
    print(a,b,a+b)
