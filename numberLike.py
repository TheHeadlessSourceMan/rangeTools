"""
Represents something that can be treated like a number
"""
import typing


class NumberLike(typing.Protocol):
    """
    Represents something that can be treated like a number
    """
    def __sub__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __add__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __mul__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __div__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __truediv__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __floordiv__(self,other:typing.Any)->"NumberLike": ... # noqa: E704
    def __lt__(self, __other:typing.Any) -> bool: ... # noqa: E704
    def __gt__(self, __other:typing.Any) -> bool: ... # noqa: E704
    def __le__(self, __other:typing.Any) -> bool: ... # noqa: E704
    def __ge__(self, __other:typing.Any) -> bool: ... # noqa: E704
    def __float__(self) -> float: ... # noqa: E704
    def __int__(self) -> int: ... # noqa: E704
    def __repr__(self) -> str: ... # noqa: E704
