# -*- coding: utf-8 -*-

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

from wireviz.wv_utils import html_line_breaks

BOM_HASH_FIELDS = "description unit partnumbers"
BomHash = namedtuple("BomHash", BOM_HASH_FIELDS)
BomHashList = namedtuple("BomHashList", BOM_HASH_FIELDS)

BomCategory = Enum(
    "BomEntry", "CONNECTOR CABLE WIRE ADDITIONAL_INSIDE ADDITIONAL_OUTSIDE"
)

PartNumberInfo = namedtuple("PartNumberInfo", "pn manufacturer mpn supplier spn")

PART_NUMBER_HEADERS = PartNumberInfo(
    pn="P/N", manufacturer=None, mpn="MPN", supplier=None, spn="SPN"
)


@dataclass
class BomEntry:
    hash: BomHash  # includes description, part number info,
    description: str
    qty: Union[int, float]
    unit: str
    designators: List[str]
    _category: BomCategory  # for sorting


def partnumbers_to_list(partnumbers: PartNumberInfo) -> List[str]:
    cell_contents = [
        pn_info_string(PART_NUMBER_HEADERS.pn, None, partnumbers.pn),
        pn_info_string(
            PART_NUMBER_HEADERS.mpn, partnumbers.manufacturer, partnumbers.mpn
        ),
        pn_info_string(PART_NUMBER_HEADERS.spn, partnumbers.supplier, partnumbers.spn),
    ]
    if any(cell_contents):
        return [html_line_breaks(cell) for cell in cell_contents]
    else:
        return None


def pn_info_string(
    header: str, name: Optional[str], number: Optional[str]
) -> Optional[str]:
    """Return the company name and/or the part number in one single string or None otherwise."""
    number = str(number).strip() if number is not None else ""
    if name or number:
        return f'{name if name else header}{": " + number if number else ""}'
    else:
        return None
