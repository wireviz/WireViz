# -*- coding: utf-8 -*-

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    contents: str
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

    def get_contents(self):
        separator = "" if self.flat else "\n"
        if isinstance(self.contents, Iterable) and not isinstance(self.contents, str):
            return separator.join([str(c) for c in self.contents if c is not None])
        elif self.contents is None:
            return ""
        else:
            return str(self.contents)

    def __repr__(self):
        separator = "" if self.flat else "\n"
        if self.contents is None and self.empty_is_none:
            return ""
        else:
            html = [
                f"<{self.tagname}{str(self.attribs)}>",
                self.get_contents(),
                f"</{self.tagname}>",
            ]
            return separator.join(html)


@dataclass
class TagSingleton(Tag):
    def __repr__(self):
        return f"<{self.tagname}{str(self.attribs)} />"


@dataclass
class Br(TagSingleton):
    pass


class Td(Tag):
    pass
    # contents: str = ""
    #
    # def __init__(self, contents, *args, **kwargs):
    #     self.contents = contents
    #     super().__init__(*args, **kwargs)
    #
    # def __repr__(self):
    #     html = [
    #         f"<td{self.attribs}>",
    #         self.contents,
    #         f"</td>",
    #     ]
    #     return "\n".join(html)


class Tr(Tag):
    pass
    # cells: List[Cell] = field(default_factory=list)
    #
    # def __init__(self, cells, *args, **kwargs):
    #     self.cells = cells
    #     super().__init__(*args, **kwargs)
    #
    # def __repr__(self):
    #     html = [
    #         f"<tr{self.attribs}>",
    #         "\n".join([str(c) for c in self.cells]),
    #         f"</tr>",
    #     ]
    #     return "\n".join(html)


class Table(Tag):
    pass
    # rows: List[Row] = field(default_factory=list)
    #
    # def __repr__(self):
    #     html = [
    #         f"<table{self.attribs}>",
    #         "\n".join([str(r) for r in self.rows]),
    #         "</table>",
    #     ]
    #     return "\n".join(html)
