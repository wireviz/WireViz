#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import re

from wireviz import __version__, APP_NAME, APP_URL
from wireviz.wv_helper import flatten2d, open_file_read, open_file_write

def generate_html_output(filename: (str, Path), bom_list):
    with open_file_write(f'{filename}.html') as file:
        file.write('<!DOCTYPE html>\n')
        file.write('<html lang="en"><head>\n')
        file.write(' <meta charset="UTF-8">\n')
        file.write(f' <meta name="generator" content="{APP_NAME} {__version__} - {APP_URL}">\n')
        file.write(f' <title>{APP_NAME} Diagram and BOM</title>\n')
        file.write('</head><body style="font-family:Arial">\n')

        file.write('<h1>Diagram</h1>')
        with open_file_read(f'{filename}.svg') as svg:
            file.write(re.sub(
                '^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>',
                '<!-- XML and DOCTYPE declarations from SVG file removed -->',
                svg.read(1024), 1))
            for svgdata in svg:
                file.write(svgdata)

        file.write('<h1>Bill of Materials</h1>')
        listy = flatten2d(bom_list)
        file.write('<table style="border:1px solid #000000; font-size: 14pt; border-spacing: 0px">')
        file.write('<tr>')
        for item in listy[0]:
            file.write(f'<th style="text-align:left; border:1px solid #000000; padding: 8px">{item}</th>')
        file.write('</tr>')
        for row in listy[1:]:
            file.write('<tr>')
            for i, item in enumerate(row):
                item_str = item.replace('\u00b2', '&sup2;')
                align = 'text-align:right; ' if listy[0][i] == 'Qty' else ''
                file.write(f'<td style="{align}border:1px solid #000000; padding: 4px">{item_str}</td>')
            file.write('</tr>')
        file.write('</table>')

        file.write('</body></html>')
