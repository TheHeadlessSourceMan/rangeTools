"""
Represents something that can be treated like a number
"""
import typing


class HasComparison(typing.Protocol):
    """
    Represents something that has comparison operators
    """
    def __lt__(self,__other:typing.Any)->bool: ... # noqa: E704
    def __le__(self,__other:typing.Any)->bool: ... # noqa: E704
    def __gt__(self,__other:typing.Any)->bool: ... # noqa: E704
    def __ge__(self,__other:typing.Any)->bool: ... # noqa: E704
    def __eq__(self,__other:typing.Any)->bool: ... # noqa: E704
    def __ne__(self,__other:typing.Any)->bool: ... # noqa: E704
Comparable=HasComparison

class HasMathOperators(typing.Protocol):
    """
    Represents something that has mathematical operators
    """
    def __sub__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __add__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __mul__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __div__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __truediv__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __floordiv__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __mod__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __pow__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __neg__(self)->"NumberLike": ... # noqa: E704

class HasMathAndComparison(HasComparison,HasMathOperators):
    """
    Represents something that both
        has comparison operators
        and has mathematical operators
    """

class HasFloatConversion(typing.Protocol):
    """
    Represents something that can be converted to a float
    """
    def __float__(self)->float: ... # noqa: E704

class HasIntConversion(typing.Protocol):
    """
    Represents something that can be tconverted to an int
    """
    def __int__(self)->int: ... # noqa: E704

NumberLike=typing.Union[int,float,HasIntConversion,HasFloatConversion,"HasMathAndComparison"]
