#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wireviz import wv_colors
from typing import List

awg_equiv_table = {
    '0.09': '28',
    '0.14': '26',
    '0.25': '24',
    '0.34': '22',
    '0.5': '21',
    '0.75': '20',
    '1': '18',
    '1.5': '16',
    '2.5': '14',
    '4': '12',
    '6': '10',
    '10': '8',
    '16': '6',
    '25': '4',
    '35': '2',
    '50': '1',
}

mm2_equiv_table = {v:k for k,v in awg_equiv_table.items()}

def awg_equiv(mm2):
    return awg_equiv_table.get(str(mm2), 'Unknown')

def mm2_equiv(awg):
    return mm2_equiv_table.get(str(awg), 'Unknown')

def nested_html_table(rows):
    # input: list, each item may be scalar or list
    # output: a parent table with one child table per parent item that is list, and one cell per parent item that is scalar
    # purpose: create the appearance of one table, where cell widths are independent between rows
    # attributes in any leading <tdX> inside a list are injected into to the preceeding <td> tag
    html = []
    html.append('<table border="0" cellspacing="0" cellpadding="0">')
    for row in rows:
        if isinstance(row, List):
            if len(row) > 0 and any(row):
                html.append(' <tr><td>')
                html.append('  <table border="0" cellspacing="0" cellpadding="3" cellborder="1"><tr>')
                for cell in row:
                    if cell is not None:
                        # Inject attributes to the preceeding <td> tag where needed
                        html.append(f'   <td balign="left">{cell}</td>'.replace('><tdX', ''))
                html.append('  </tr></table>')
                html.append(' </td></tr>')
        elif row is not None:
            html.append(' <tr><td>')
            html.append(f'  {row}')
            html.append(' </td></tr>')
    html.append('</table>')
    return html

def html_colorbar(color):
    return f'<tdX bgcolor="{wv_colors.translate_color(color, "HEX")}" width="4">' if color else None

def html_image(image):
    if not image:
        return None
    # The leading attributes belong to the preceeding tag. See where used below.
    html = f'{html_size_attr(image)}><img scale="{image.scale}" src="{image.src}"/>'
    if image.fixedsize:
        # Close the preceeding tag and enclose the image cell in a table without
        # borders to avoid narrow borders when the fixed width < the node width.
        html = f'''>
    <table border="0" cellspacing="0" cellborder="0"><tr>
     <td{html}</td>
    </tr></table>
   '''
    return f'''<tdX{' sides="TLR"' if image.caption else ''}{html}'''

def html_caption(image):
    return f'<tdX sides="BLR">{html_line_breaks(image.caption)}' if image and image.caption else None

def html_size_attr(image):
    # Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object
    return ((f' width="{image.width}"'   if image.width else '')
        +   (f' height="{image.height}"' if image.height else '')
        +   ( ' fixedsize="true"'        if image.fixedsize else '')) if image else ''


def expand(yaml_data):
    # yaml_data can be:
    # - a singleton (normally str or int)
    # - a list of str or int
    # if str is of the format '#-#', it is treated as a range (inclusive) and expanded
    output = []
    if not isinstance(yaml_data, list):
        yaml_data = [yaml_data]
    for e in yaml_data:
        e = str(e)
        if '-' in e:
            a, b = e.split('-', 1)
            try:
                a = int(a)
                b = int(b)
                if a < b:
                    for x in range(a, b + 1):
                        output.append(x)  # ascending range
                elif a > b:
                    for x in range(a, b - 1, -1):
                        output.append(x)  # descending range
                else:  # a == b
                    output.append(a)  # range of length 1
            except:
                output.append(e)  # '-' was not a delimiter between two ints, pass e through unchanged
        else:
            try:
                x = int(e)  # single int
            except Exception:
                x = e  # string
            output.append(x)
    return output


def int2tuple(inp):
    if isinstance(inp, tuple):
        output = inp
    else:
        output = (inp,)
    return output


def flatten2d(inp):
    return [[str(item) if not isinstance(item, List) else ', '.join(item) for item in row] for row in inp]


def tuplelist2tsv(inp, header=None):
    output = ''
    if header is not None:
        inp.insert(0, header)
    inp = flatten2d(inp)
    for row in inp:
        output = output + '\t'.join(str(item) for item in row) + '\n'
    return output

# Return the value indexed if it is a list, or simply the value otherwise.
def index_if_list(value, index):
    return value[index] if isinstance(value, list) else value

def html_line_breaks(inp):
    return inp.replace('\n', '<br />') if isinstance(inp, str) else inp

def graphviz_line_breaks(inp):
    return inp.replace('\n', '\\n') if isinstance(inp, str) else inp # \n generates centered new lines. http://www.graphviz.org/doc/info/attrs.html#k:escString

def remove_line_breaks(inp):
    return inp.replace('\n', ' ').strip() if isinstance(inp, str) else inp

def open_file_read(filename):
    # TODO: Intelligently determine encoding
    return open(filename, 'r', encoding='UTF-8')

def open_file_write(filename):
    return open(filename, 'w', encoding='UTF-8')

def open_file_append(filename):
    return open(filename, 'a', encoding='UTF-8')


def aspect_ratio(image_src):
    try:
        from PIL import Image
        image = Image.open(image_src)
        if image.width > 0 and image.height > 0:
            return image.width / image.height
        print(f'aspect_ratio(): Invalid image size {image.width} x {image.height}')
    # ModuleNotFoundError and FileNotFoundError are the most expected, but all are handled equally.
    except Exception as error:
        print(f'aspect_ratio(): {type(error).__name__}: {error}')
    return 1 # Assume 1:1 when unable to read actual image size


def manufacturer_info_field(manufacturer, mpn):
    if manufacturer or mpn:
        return f'{manufacturer if manufacturer else "MPN"}{": " + str(mpn) if mpn else ""}'
    else:
        return None
