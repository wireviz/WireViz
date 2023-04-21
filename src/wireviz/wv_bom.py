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
    bom_columns = []
    has_content = set()
    # First pass, get all bom dict and identify filled columns
    for entry in bom.values():
        entry.restrict_printed_lengths = restrict_printed_lengths
        entry_as_dict = entry.bom_dict_pretty_column
        entries_as_dict.append(entry_as_dict)
        for k in entry_as_dict:
            if k not in bom_columns:
                bom_columns.append(k)
            if entry_as_dict[k] is not None and entry_as_dict[k] != "":
                has_content.add(k)

    headers = bom_columns
    if filter_entries:
        headers = [k for k in bom_columns if k in has_content]

    entries_as_list = []
    for entry in entries_as_dict:
        entries_as_list.append([entry.get(k, "") for k in headers])

    # sanity check
    expected_length = len(entries_as_list[0])
    for e in entries_as_list:
        assert len(e) == expected_length, f'entries {e} length is not {expected_length}'

    table = [headers] + entries_as_list

    return table


def print_bom_table(bom):
    print()
    print(tabulate_module.tabulate(bom_list(bom), headers="firstrow"))
    print()
