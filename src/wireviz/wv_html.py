#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import List, Union
import re

from wireviz import __version__, APP_NAME, APP_URL, wv_colors
from wireviz.DataClasses import Metadata, Options
from wireviz.wv_helper import flatten2d, open_file_read, open_file_write, smart_file_resolve
from wireviz.wv_gv_html import html_line_breaks

def generate_html_output(filename: Union[str, Path], bom_list: List[List[str]], metadata: Metadata, options: Options):

    if 'name' in metadata.get('template',{}):
        # if relative path to template was provided, check directory of YAML file first, fall back to built-in template directory
        templatefile = smart_file_resolve(f'{metadata["template"]["name"]}.html', [Path(filename).parent, Path(__file__).parent / 'templates'])
    else:
        # fall back to built-in simple template if no template was provided
        templatefile = Path(__file__).parent / 'templates/simple.html'

    with open(templatefile, 'r') as file:
        html = file.read()

    # embed SVG diagram
    with open(f'{filename}.svg') as file:
        svgdata = file.read()
        svgdata = re.sub(
                  '^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>',
                  '<!-- XML and DOCTYPE declarations from SVG file removed -->',
                  svgdata, 1)
    html = html.replace('<!-- diagram -->', svgdata)

    # generate BOM table
    bom = flatten2d(bom_list)

    # generate BOM header (may be at the top or bottom of the table)
    bom_header_html = '  <tr>\n'
    for item in bom[0]:
        th_class = f'bom_col_{item.lower()}'
        bom_header_html = f'{bom_header_html}    <th class="{th_class}">{item}</th>\n'
    bom_header_html = f'{bom_header_html}  </tr>\n'

    # generate BOM contents
    bom_contents = []
    for row in bom[1:]:
        row_html = '  <tr>\n'
        for i, item in enumerate(row):
            td_class = f'bom_col_{bom[0][i].lower()}'
            row_html = f'{row_html}    <td class="{td_class}">{item}</td>\n'
        row_html = f'{row_html}  </tr>\n'
        bom_contents.append(row_html)

    bom_html = '<table>\n' + bom_header_html + ''.join(bom_contents) + '</table>\n'
    bom_html_reversed = '<table>\n' + ''.join(list(reversed(bom_contents))) + bom_header_html + '</table>\n'

    # insert BOM table
    html = html.replace('<!-- bom -->', bom_html)
    html = html.replace('<!-- bom_reversed -->', bom_html_reversed)

    # fill out title block
    if metadata:
        html = html.replace('<!-- title -->', metadata.get('title', ''))
        html = html.replace('<!-- pn -->', metadata.get('pn', ''))
        html = html.replace('<!-- company -->', metadata.get('company', ''))
        html = html.replace('<!-- description -->', html_line_breaks(metadata.get('description', '')))
        html = html.replace('<!-- notes -->', html_line_breaks(metadata.get('notes', '')))
        html = html.replace('<!-- generator -->', f'{APP_NAME} {__version__} - {APP_URL}')

        # TODO: handle multi-page documents
        html = html.replace('<!-- sheet_current -->', 'Sheet<br />1')
        html = html.replace('<!-- sheet_total -->', 'of 1')

        for i, (k, v) in enumerate(metadata.get('authors', {}).items(), 1):
            title = k
            name = v['name']
            date = v['date'].strftime('%Y-%m-%d')
            html = html.replace(f'<!-- process_{i}_title -->', title)
            html = html.replace(f'<!-- process_{i}_name -->', name)
            html = html.replace(f'<!-- process_{i}_date -->', date)

        for i, (k, v) in enumerate(metadata.get('revisions', {}).items(), 1):
            # TODO: for more than 8 revisions, keep only the 8 most recent ones
            number = k
            changelog = v['changelog']
            name = v['name']
            date = v['date'].strftime('%Y-%m-%d')
            html = html.replace(f'<!-- rev_{i}_number -->', '{:02d}'.format(number))
            html = html.replace(f'<!-- rev_{i}_changelog -->', changelog)
            html = html.replace(f'<!-- rev_{i}_name -->', name)
            html = html.replace(f'<!-- rev_{i}_date -->', date)

        html = html.replace(f'"sheetsize_default"', '"{}"'.format(metadata.get('template',{}).get('sheetsize', ''))) # include quotes so no replacement happens within <style> definition

    with open(f'{filename}.html','w') as file:
        file.write(html)
