# -*- coding: utf-8 -*-

from typing import List

import tabulate as tabulate_module

from wireviz.wv_dataclasses import PartNumberInfo

# TODO: different BOM modes
# BomMode
# "normal"  # no bubbles, full PN info in GV node
# "bubbles"  # = "full" -> maximum info in GV node
# "hide PN info"
# "PN crossref" = "PN bubbles" + "hide PN info"
# "additionally: BOM table in GV graph label (#227)"
# "title block in GV graph label"


def partnumbers2list(
    partnumbers: PartNumberInfo, parent_partnumbers: PartNumberInfo = None
) -> List[str]:
    if not isinstance(partnumbers, list):
        return partnumbers.str_list

    pn = None
    for p in partnumbers:
        if pn is None:
            pn = p.copy()
        pn = pn.keep_only_eq(p)

    if pn.str_list is None and parent_partnumbers is not None:
        return parent_partnumbers.str_list
    else:
        return pn.str_list


def bom_list(bom):
    entries_as_dict = []
    has_content = set()
    # First pass, get all bom dict and identify filled columns
    for entry in bom.values():
        has_content = has_content.union(entry.bom_defined)
        entries_as_dict.append(entry.bom_dict)

    first_entry = list(bom.values())[0]  # Used for column manipulation
    keys_with_content = [k for k in first_entry.bom_keys if k in has_content]
    headers = [first_entry.bom_column(k) for k in keys_with_content]

    entries_as_list = []
    for entry in entries_as_dict:
        entries_as_list.append([v for k, v in entry.items() if k in keys_with_content])

    table = [headers] + entries_as_list

    return table


def print_bom_table(bom):
    print()
    print(tabulate_module.tabulate(bom_list(bom), headers="firstrow"))
    print()
