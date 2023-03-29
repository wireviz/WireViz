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
        partnumbers = [partnumbers]


    # if there's no parent, fold
    if parent_partnumbers is None:
        return PartNumberInfo.list_keep_only_eq(partnumbers).str_list

    if isinstance(parent_partnumbers, list):
        parent_partnumbers = PartNumberInfo.list_keep_only_eq(parent_partnumbers)

    partnumbers = [p.remove_eq(parent_partnumbers) for p in partnumbers]

    return [p.str_list for p in partnumbers if p]


def bom_list(bom, restrict_printed_lengths=True):
    entries_as_dict = []
    has_content = set()
    # First pass, get all bom dict and identify filled columns
    for entry in bom.values():
        entry.restrict_printed_lengths = restrict_printed_lengths
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
