#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from io import StringIO

from wireviz import wv_helper

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


def generate_bom_outputs(bomdata, dialect='tsv'):
    dialect = dialect.strip().lower()
    dialect_lookup = {
        'csv': csv.unix_dialect,
        'csv_unix': csv.unix_dialect,
        'csv_excel': csv.excel,
        'tsv': WIREVIZ_TSV,
        'tsv_excel': csv.excel_tab
    }
    valid_dialects = [k for k in dialect_lookup.keys()]
    if dialect not in valid_dialects:
        raise ValueError(f'dialect "{dialect}" not supported')

    output = StringIO()
    writer = csv.writer(output, dialect=dialect_lookup[dialect])
    writer.writerows(wv_helper.flatten2d(bomdata))

    output.seek(0)

    return bytes(output.read(), encoding='utf-8')

# TODO: Possibly refactor other BOM output operations, such as HTML, into here?