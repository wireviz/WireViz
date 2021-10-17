# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections.abc import Iterable


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
    one_line: bool = False

    @property
    def tagname(self):
        return type(self).__name__.lower()

    def get_contents(self):
        if isinstance(self.contents, Iterable):
            return "\n".join([str(c) for c in self.contents])
        else:
            return str(self.contents)


    def __repr__(self):
        separator = "" if self.one_line else "\n"
        html = [
            f"<{self.tagname}{str(self.attribs)}>",
            self.get_contents(),
            f"</{self.tagname}>",
        ]
        return separator.join(html)


@dataclass
class TagSingleton(Tag):
    def __repr__(self):
        return f"<{self.tagname}{self.attribs} />"


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
