# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List, Union
import re

from wireviz import __version__, APP_NAME, APP_URL, wv_colors
from wireviz.DataClasses import Metadata, Options
from wireviz.wv_helper import flatten2d, open_file_read, open_file_write

def generate_html_output(filename: Union[str, Path], bom_list: List[List[str]], metadata: Metadata, options: Options):
    with open_file_write(f'{filename}.html') as file:
        file.write('<!DOCTYPE html>\n')
        file.write('<html lang="en"><head>\n')
        file.write(' <meta charset="UTF-8">\n')
        file.write(f' <meta name="generator" content="{APP_NAME} {__version__} - {APP_URL}">\n')
        file.write(f' <title>{metadata["title"]}</title>\n')
        file.write(f'</head><body style="{options.html_style()}">\n')
        file.write(f'<h1>{metadata["title"]}</h1>\n')
        description = metadata.get('description')
        if description:
            file.write(f'<p>{description}</p>\n')
        file.write('<h2>Diagram</h2>\n')
        with open_file_read(f'{filename}.svg') as svg:
            file.write(re.sub(
                '^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>',
                '<!-- XML and DOCTYPE declarations from SVG file removed -->',
                svg.read(1024), 1))
            for svgdata in svg:
                file.write(svgdata)

        file.write('<h2>Bill of Materials</h2>\n')
        listy = flatten2d(bom_list)
        border = options.html_style(color_prefix="border: 1px solid", include_all=False)
        file.write(f'<table style="{border} border-spacing: 0px;">\n')
        file.write(' <tr>\n')
        for item in listy[0]:
            file.write(f'  <th style="{border} padding: 8px; text-align:left;">{item}</th>\n')
        file.write(' </tr>\n')
        for row in listy[1:]:
            file.write(' <tr>\n')
            for i, item in enumerate(row):
                item_str = item.replace('\u00b2', '&sup2;')
                align = '; text-align:right' if listy[0][i] == 'Qty' else ''
                file.write(f'  <td style="{border} padding: 4px{align};">{item_str}</td>\n')
            file.write(' </tr>\n')
        file.write('</table>\n')

        notes = metadata.get('notes')
        if notes:
            file.write(f'<h2>Notes</h2>\n<p>{notes}</p>\n')

        file.write('</body></html>\n')
