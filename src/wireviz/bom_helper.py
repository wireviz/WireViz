#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from wireviz import wv_helper
from wireviz.wv_helper import open_file_write

EXCEL_CSV = csv.excel
EXCEL_TSV = csv.excel_tab
UNIX_CSV = csv.unix_dialect
WIREVIZ_TSV = type('Wireviz BOM', (csv.Dialect, object), dict(
    delimiter='\t',
    doublequote=True,
    escapechar=None,
    lineterminator='\n',
    quoting=0,
    skipinitialspace=False,
    strict=False,
    quotechar='"'
))
csv.register_dialect('Wireviz BOM', WIREVIZ_TSV)

_csv_formats = { EXCEL_CSV, UNIX_CSV }
_tsv_formats = { EXCEL_TSV, WIREVIZ_TSV }

_csv_ext = '.bom.csv'
_tsv_ext = '.bom.tsv'


def generate_bom_outputs(base_filename, bomdata, formats=None):
    if formats is None:
        formats = [EXCEL_CSV, WIREVIZ_TSV]
    elif isinstance(formats, csv.Dialect):
        formats = [formats]
    elif not isinstance(formats, list):
        raise TypeError
    expanded_csv_names =  len(_csv_formats.intersection(set(formats))) > 1
    expanded_tsv_names = len(_tsv_formats.intersection(set(formats))) > 1

    for fmt in formats:
        if fmt in _csv_formats:
            file = csv.writer(open_file_write(base_filename + ("_" + fmt.__name__ if expanded_csv_names else "") + _csv_ext, fmt.lineterminator), fmt)

        elif fmt in _tsv_formats:
            file = csv.writer(open_file_write(base_filename + ("_"+fmt.__name__ if expanded_tsv_names else "") + _tsv_ext, fmt.lineterminator), fmt)
        else:
            raise KeyError("Unknown BOM Format Specified")
        file.writerows(wv_helper.flatten2d(bomdata))

# TODO: Possibly refactor other BOM output operations, such as HTML, into here?