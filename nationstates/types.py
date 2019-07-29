# pylint: disable=unsubscriptable-object
# pylint says, "what even is __class_getitem__"
# this was a lot of work just to make mypy shut up...
import re
from enum import EnumMeta, Flag, auto
from functools import partial, reduce, wraps
from operator import or_
from typing import Any, Callable, Generic, Iterable, Optional, NewType, Tuple, Type, TypeVar, Union

from redbot.core import commands


import traceback


def _dec(func):
    @wraps(func)
    async def inner(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except:
            traceback.print_exc()
            raise

    return inner


commands.Command._actual_conversion = _dec(commands.Command._actual_conversion)


LINK_RE = re.compile(
    r"(?i)\b(?:https?:\/\/)?(?:www\.)?nationstates\.net\/(?:(nation|region)=)?([-\w\s]+)\b"
)
WA_RE = re.compile(
    r"(?i)\b(?:https?:\/\/)?(?:www\.)?nationstates\.net\/page=wa_past_resolution\/id=(\d+)\/council=([12])\b"
)


def link_extract(link: str, *, expected: str):
    try:
        index = ("wa", "ga", "sc").index(expected.casefold()) - 1
    except IndexError:
        pass
    else:
        return wa_link_extract(link, expected=index)
    match = LINK_RE.match(link)
    if not match:
        return link
    if (match.group(1) or "nation").casefold() != expected.casefold():
        raise commands.BadArgument()
    return match.group(2)


def wa_link_extract(link: str, *, expected: int):
    match = WA_RE.match(link)
    if not match:
        return link
    if expected > 0 and match.group(2) != expected:
        raise commands.BadArgument()
    return match.group(1)


# ENUMS
class _Options(Flag):
    pass


class Nation(_Options):
    ALL = -1
    NONE = 0
    STAT = auto()
    WA = auto()
    RMB = auto()
    CARDS = auto()


class Region(_Options):
    ALL = -1
    NONE = 0
    FOUNDER = auto()
    DELEGATE = auto()
    TAG = auto()


class WA(_Options):
    ALL = -1
    NONE = 0
    TEXT = auto()
    VOTE = auto()
    NATION = auto()
    DELEGATE = auto()


GA = NewType("GA", WA)
SC = NewType("SC", WA)


# TYPING
T = TypeVar("T", bound=_Options)


def _args(cls: type, *, supertype: bool = True, default: tuple = NotImplemented) -> tuple:
    types = getattr(cls, "__args__", NotImplemented)
    if types is NotImplemented:
        if default is not NotImplemented:
            return default
        raise TypeError(f"Parameter list to {cls.__qualname__}[...] cannot be empty")
    if supertype:
        ret = []
        for t in types:
            while True:
                try:
                    t = t.__supertype__
                except AttributeError:
                    break
            ret.append(t)
        return tuple(ret)
    else:
        return types


class Link(str, Generic[T]):
    def __new__(cls, argument: str) -> str:
        types: Tuple[Type[T], ...] = _args(cls, supertype=False)
        return link_extract(argument, expected=types[0].__name__)


class Options(Generic[T]):
    def __new__(cls, argument: str) -> T:
        types: Tuple[Type[T], ...] = _args(cls)
        return types[0][argument.upper().rstrip("S")]

    @classmethod
    def reduce(
        cls, args: Iterable, *, default: Union[T, int] = 0, operator: Callable[[T, T], T] = or_
    ) -> T:
        types: Tuple[Type[T], ...] = _args(cls)
        if not args:
            return types[0](default)
        return types[0](reduce(operator, args))
