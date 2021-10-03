# -*- coding: utf-8 -*-

from typing import List, Optional, Union

from wireviz.DataClasses import Image, Look
from wireviz.wv_colors import Color, translate_color
from wireviz.wv_helper import remove_links

GvHtml = str  # Graphviz HTML-like label string
GvHtmlX = str  # Graphviz HTML-like label string possibly including a leading <tdX> tag
GvHtmlAttr = str  # Attributes part of Graphviz HTML-like tag (including a leading space)

def nested_html_table(rows: List[Union[GvHtml, List[Optional[GvHtmlX]], None]], look: Optional[Look]) -> GvHtml:
    # input: list, each item may be scalar or list, and look with optional table look attributes
    # output: a parent table with one child table per parent item that is list, and one cell per parent item that is scalar
    # purpose: create the appearance of one table, where cell widths are independent between rows
    # attributes in any leading <tdX> inside a list are injected into to the preceeding <td> tag
    html = []
    attr = font_attr(look)
    font = f'<font{attr}>' if attr else ''
    html.append(f'{font}<table border="0" cellspacing="0" cellpadding="0"{table_attr(look)}>')
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
    html.append(f'</table>{"</font>" if font else ""}')
    return html

def table_attr(look: Optional[Look]) -> GvHtmlAttr:
    """Return table tag attributes containing all non-empty table option values."""
    return '' if not look else ''.join({
        f' {k}="{v}"' for k,v in look._2dict().items() if v and 'font' not in k})

def font_attr(look: Optional[Look]) -> GvHtmlAttr:
    """Return font tag attributes containing all non-empty font option values."""
    attr = {k:v for k,v in look._2dict().items() if v and 'font' in k} if look else {}
    return ((f' color="{attr["fontcolor"]}"' if attr.get('fontcolor') else '')
        +   (f' face="{attr["fontname"]}"' if attr.get('fontname') else '')
        +   (f' point-size="{attr["fontsize"]}"' if attr.get('fontsize') else ''))

def font_tag(look: Optional[Look], text: GvHtml) -> GvHtml:
    """Return text in Graphviz HTML font tag with all non-empty font option values."""
    attr = font_attr(look)
    return f'<font{attr}>{text}</font>' if attr and text > '' else text

def html_cell(look: Optional[Look], text: GvHtml = '', attr: GvHtmlAttr = '') -> GvHtmlX:
    """Return cell to be included in the rows list for nested_html_table()."""
    return f'<tdX{attr}{table_attr(look)}>{font_tag(look, text)}'

def html_colorbar(color: Optional[Color]) -> Optional[GvHtmlX]:
    """Return colored cell to be included in the rows list for nested_html_table() or None if no color."""
    return html_cell(Look(bgcolor=color), attr=' width="4"') if color else None

def html_image(image: Optional[Image]) -> Optional[GvHtmlX]:
    """Return image cell to be included in the rows list for nested_html_table() or None if no image."""
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
    return f'''<tdX{' sides="TLR"' if image.caption else ''}{table_attr(image.box)}{html}'''

def html_caption(image: Optional[Image]) -> Optional[GvHtmlX]:
    """Return image caption cell to be included just after the image cell or None if no caption."""
    return html_cell(image.box, html_line_breaks(image.caption), ' sides="BLR"') if image and image.caption else None

def html_size_attr(image: Optional[Image]) -> GvHtmlAttr:
    """Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object."""
    return ((f' width="{image.width}"'   if image.width else '')
        +   (f' height="{image.height}"' if image.height else '')
        +   ( ' fixedsize="true"'        if image.fixedsize else '')) if image else ''

def html_line_breaks(inp):
    return remove_links(inp).replace('\n', '<br />') if isinstance(inp, str) else inp
