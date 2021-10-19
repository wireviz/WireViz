# -*- coding: utf-8 -*-

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Dict

indent_count = 1


class Attribs(Dict):
    def __repr__(self):
        if len(self) == 0:
            return ""

        html = []
        for k, v in self.items():
            if v is not None:
                html.append(f' {k}="{v}"')
            # else:
            #     html.append(f" {k}")
        return "".join(html)


@dataclass
class Tag:
    contents = None
    attribs: Attribs = field(default_factory=Attribs)
    flat: bool = None
    delete_if_empty: bool = False

    def __init__(self, contents, flat=None, delete_if_empty=False, **kwargs):
        self.contents = contents
        self.flat = flat
        self.delete_if_empty = delete_if_empty
        self.attribs = Attribs({**kwargs})

    def update_attribs(self, **kwargs):
        for k, v in kwargs.items():
            self.attribs[k] = v

    @property
    def tagname(self):
        return type(self).__name__.lower()

    @property
    def auto_flat(self):
        if self.flat is not None:  # user specified
            return self.flat
        if not _is_iterable_not_str(self.contents):  # catch str, int, float, ...
            if not isinstance(self.contents, Tag):  # avoid recursion
                return not "\n" in str(self.contents)  # flatten if single line

    @property
    def is_empty(self):
        return self.get_contents(force_flat=True) == ""

    def indent_lines(self, lines, force_flat=False):
        if self.auto_flat or force_flat:
            return lines
        else:
            indenter = " " * indent_count
            return "\n".join(f"{indenter}{line}" for line in lines.split("\n"))

    def get_contents(self, force_flat=False):
        separator = "" if self.auto_flat or force_flat else "\n"
        if _is_iterable_not_str(self.contents):
            return separator.join(
                [
                    self.indent_lines(str(c), force_flat)
                    for c in self.contents
                    if c is not None
                ]
            )
        elif self.contents is None:
            return ""
        else:  # str, int, float, etc.
            return self.indent_lines(str(self.contents), force_flat)

    def __repr__(self):
        separator = "" if self.auto_flat else "\n"
        if self.delete_if_empty and self.is_empty:
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
    def __init__(self, **kwargs):
        self.attribs = Attribs({**kwargs})

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
