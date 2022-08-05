# -*- coding: utf-8 -*-

from collections import namedtuple
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import List, Optional, Union

import tabulate as tabulate_module

from wireviz.wv_utils import html_line_breaks

BOM_HASH_FIELDS = "description qty_unit amount partnumbers"


BomEntry = namedtuple("BomEntry", "category qty designators")
BomHash = namedtuple("BomHash", BOM_HASH_FIELDS)
BomHashList = namedtuple("BomHashList", BOM_HASH_FIELDS)
PartNumberInfo = namedtuple("PartNumberInfo", "pn manufacturer mpn supplier spn")

# TODO: different BOM modes
# BomMode
# "normal"  # no bubbles, full PN info in GV node
# "bubbles"  # = "full" -> maximum info in GV node
# "hide PN info"
# "PN crossref" = "PN bubbles" + "hide PN info"
# "additionally: BOM table in GV graph label (#227)"
# "title block in GV graph label"


BomCategory = IntEnum(  # to enforce ordering in BOM
    "BomEntry", "CONNECTOR CABLE WIRE ADDITIONAL_INSIDE ADDITIONAL_OUTSIDE"
)
QtyMultiplierConnector = Enum(
    "QtyMultiplierConnector", "PINCOUNT POPULATED CONNECTIONS"
)
QtyMultiplierCable = Enum(
    "QtyMultiplierCable", "WIRECOUNT TERMINATION LENGTH TOTAL_LENGTH"
)

PART_NUMBER_HEADERS = PartNumberInfo(
    pn="P/N", manufacturer=None, mpn="MPN", supplier=None, spn="SPN"
)


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


def print_bom_debug(bom):
    headers = "# qty unit description amount unit designators category".split(" ")
    rows = []
    rows.append(headers)
    # fill rows
    for hash, entry in bom.items():
        cells = [
            entry["id"],
            entry["qty"],
            hash.qty_unit,
            hash.description,
            hash.amount.number if hash.amount else None,
            hash.amount.unit if hash.amount else None,
            ", ".join(sorted(entry["designators"])),
            f"{entry['category']} ({entry['category'].name})",
        ]
        rows.append(cells)
    # remove empty columns
    transposed = list(map(list, zip(*rows)))
    transposed = [
        column
        for column in transposed
        if any([cell is not None for cell in column[1:]])
        #                                           ^ ignore header cell in check
    ]
    rows = list(map(list, zip(*transposed)))
    # output
    print()
    print(tabulate_module.tabulate(rows, headers="firstrow"))
    print()
