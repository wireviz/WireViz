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


def bom_list(bom, restrict_printed_lengths=True, filter_entries=False):
    entries_as_dict = []
    # First pass, get all bom dict and identify filled columns
    for entry in bom.values():
        entry.restrict_printed_lengths = restrict_printed_lengths
        entries_as_dict.append(entry.bom_dict)

    has_content = {}
    bom_columns = list(entries_as_dict[0].keys())
    has_content = {
        k
        for k in bom_columns
        if any(e[k] for e in entries_as_dict)
    }

    headers = bom_columns
    if filter_entries:
        headers = [k for k in bom_columns if k in has_content]

    entries_as_list = []
    for entry in entries_as_dict:
        entries_as_list.append([v for k, v in entry.items() if k in headers])

    table = [headers] + entries_as_list

    return table


def print_bom_table(bom):
    print()
    print(tabulate_module.tabulate(bom_list(bom), headers="firstrow"))
    print()
