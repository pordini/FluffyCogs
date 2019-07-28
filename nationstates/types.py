# pylint: disable=unsubscriptable-object
# pylint says, "what even is __class_getitem__"
# this was a lot of work just to make mypy shut up...
import re
from enum import Flag, auto
from functools import reduce, partial
from operator import or_
from typing import Callable, Generic, NewType, TypeVar, Union

from redbot.core import commands


LINK_RE = re.compile(
    r"(?i)\b(?:https?:\/\/)?(?:www\.)?nationstates\.net\/(?:(nation|region)=)?([-\w\s]+)\b"
)


def link_extract(link: str, *, expected):
    match = LINK_RE.match(link)
    if not match:
        return link
    if (match.group(1) or "nation").lower() != expected.lower():
        raise commands.BadArgument()
    return match.group(2)


# TYPING
Nation = NewType("Nation", object)
Region = NewType("Region", object)
T = TypeVar("T", Nation, Region)


class NSC(str, Generic[T]):
    @classmethod  # pylint says, "what even is an implied classmethod"
    def __class_getitem__(cls, item):
        if isinstance(item, tuple):
            return Union[tuple(cls[t] for t in item)]
        if item in (Nation, Region):
            return partial(link_extract, expected=item.__name__.lower())
        raise TypeError(f"Unknown generic type {item!r}.")


# ENUMS
class Options(Flag):
    @classmethod
    def __call__(cls, value, *args, **kwargs):
        try:
            # pylint: disable=no-member
            return super().__call__(value, *args, **kwargs)
        except AttributeError as e:
            raise TypeError(f"{cls.__name__!r} object is not callable") from e
        except ValueError:
            if args or kwargs:
                raise
            return cls._convert(value)

    @classmethod
    def _convert(cls, argument: str):
        argument = argument.upper().rstrip("S")
        try:
            return cls[argument]
        except KeyError as ke:
            raise commands.BadArgument() from ke

    @classmethod
    def reduce(
        cls,
        *args: "Options",
        default: Union["Options", int] = 0,
        func: Callable[["Options", "Options"], "Options"] = or_,
    ):
        if not args:
            return cls(default)
        return cls(reduce(func, args))


class NationOptions(Options):
    ALL = -1
    NONE = 0
    STATS = auto()
    WA = auto()
    RMB = auto()
    CARDS = auto()


class RegionOptions(Options):
    ALL = -1
    NONE = 0
    FOUNDER = auto()
    DELEGATE = auto()
    TAGS = auto()


class WAOptions(Options):
    ALL = -1
    NONE = 0
    TEXT = auto()
    VOTE = auto()
    NATION = auto()
    DELEGATE = auto()
