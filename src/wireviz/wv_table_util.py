# -*- coding: utf-8 -*-

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Dict, List, Optional

indent_count = 1


class Attribs(Dict):
    def __repr__(self):
        if len(self) == 0:
            return ""

        html = []
        for k, v in self.items():
            if v is not None:
                html.append(f' {k}="{v}"')
            else:
                html.append(f" {k}")
        return "".join(html)


@dataclass
class Tag:
    contents: str = None
    attribs: Attribs = field(default_factory=Attribs)
    flat: bool = False
    empty_is_none: bool = False

    def __post_init__(self):
        if self.attribs is None:
            self.attribs = Attribs({})
        elif isinstance(self.attribs, Dict):
            self.attribs = Attribs(self.attribs)
        elif not isinstance(self.attribs, Attribs):
            raise Exception(
                "Tag.attribs must be of type None, Dict, or Attribs, "
                f"but type {type(self.attribs).__name__} was given instead:\n"
                f"{self.attribs}"
            )

    @property
    def tagname(self):
        return type(self).__name__.lower()

    @property
    def auto_flat(self):
        if self.flat:  # force flat
            return True
        if not _is_iterable_not_str(self.contents):  # catch str, int, float, ...
            if not isinstance(self.contents, Tag):  # avoid recursion
                return not "\n" in str(self.contents)  # flatten if single line

    def indent_lines(self, lines):
        if self.auto_flat:
            return lines
        else:
            indenter = " " * indent_count
            return "\n".join(f"{indenter}{line}" for line in lines.split("\n"))

    def get_contents(self):
        separator = "" if self.auto_flat else "\n"
        if _is_iterable_not_str(self.contents):
            return separator.join(
                [self.indent_lines(str(c)) for c in self.contents if c is not None]
            )
        elif self.contents is None:
            return ""
        else:  # str, int, float, etc.
            return self.indent_lines(str(self.contents))

    def __repr__(self):
        # if self.flat:
        #     import pudb; pudb.set_trace()

        separator = "" if self.auto_flat else "\n"
        if self.contents is None and self.empty_is_none:
            return ""
        else:
            html = [
                f"<{self.tagname}{str(self.attribs)}>",
                f"{self.get_contents()}",
                f"</{self.tagname}>",
            ]
            html_joined = separator.join(html)
            return html_joined


@dataclass
class TagSingleton(Tag):
    def __repr__(self):
        return f"<{self.tagname}{str(self.attribs)} />"


def _is_iterable_not_str(inp):
    # str is iterable, but should be treated as not iterable
    return isinstance(inp, Iterable) and not isinstance(inp, str)


@dataclass
class Br(TagSingleton):
    pass


class Img(TagSingleton):
    pass


class Td(Tag):
    pass


class Tr(Tag):
    pass


class Table(Tag):
    pass
