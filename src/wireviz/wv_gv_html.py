# -*- coding: utf-8 -*-

import re
from itertools import zip_longest
from typing import List, Optional, Union

from wireviz.DataClasses import Color, Connector, Options
from wireviz.wv_colors import translate_color
from wireviz.wv_helper import pn_info_string, remove_links
from wireviz.wv_table_util import *  # TODO: explicitly import each needed tag later

HEADER_PN = "P/N"
HEADER_MPN = "MPN"
HEADER_SPN = "SPN"

# TODO: remove harness argument; only used by get_additional_component_table()
def gv_node_connector(connector: Connector, harness_options: Options) -> str:
    # If no wires connected (except maybe loop wires)?
    if not (connector.ports_left or connector.ports_right):
        connector.ports_left = True  # Use left side pins by default

    html = []
    if connector.show_name:
        row_name = [
            f"{html_bgcolor(connector.bgcolor_title)}" f"{remove_links(connector.name)}"
        ]
    else:
        row_name = []

    row_pn = [
        pn_info_string(HEADER_PN, None, connector.pn),
        pn_info_string(HEADER_MPN, connector.manufacturer, connector.mpn),
        pn_info_string(HEADER_SPN, connector.supplier, connector.spn),
    ]
    row_pn = [html_line_breaks(cell) for cell in row_pn]

    row_info = [
        html_line_breaks(connector.type),
        html_line_breaks(connector.subtype),
        f"{connector.pincount}-pin" if connector.show_pincount else None,
        translate_color(connector.color, harness_options.color_mode),
        html_colorbar(connector.color),
    ]

    if connector.style != "simple":
        row_connector_table = "<!-- connector table -->"
    else:
        row_connector_table = None

    row_image = [html_image(connector.image)]
    row_image_caption = [html_caption(connector.image)]
    row_notes = [html_line_breaks(connector.notes)]
    # row_additional_component_table = get_additional_component_table(self, connector)
    row_additional_component_table = None

    rows = [
        row_name,
        row_pn,
        row_info,
        row_connector_table,
        row_image,
        row_image_caption,
        row_additional_component_table,
        row_notes,
    ]

    html.extend(nested_html_table(rows, html_bgcolor_attr(connector.bgcolor)))

    if connector.style != "simple":
        pinhtml = []
        # fmt: off
        # pinhtml.append('<table border="0" cellspacing="0" cellpadding="3" cellborder="1">')
        # fmt: on

        pin_tuples = zip_longest(
            connector.pins,
            connector.pinlabels,
            connector.pincolors,
        )

        contents = []
        for pinindex, (pinname, pinlabel, pincolor) in enumerate(pin_tuples):
            if connector.hide_disconnected_pins and not connector.visible_pins.get(
                pinname, False
            ):
                continue

            contents.append(gv_pin(pinindex, pinname, pinlabel, pincolor, connector))

        table_attribs = {
            "border": 0,
            "cellspacing": 0,
            "cellpadding": 3,
            "cellborder": 1,
        }
        pinhtml.append(str(Table(contents, attribs=Attribs(table_attribs))))

        pin_html_joined = "\n".join(pinhtml)

        html = [
            row.replace("<!-- connector table -->", pin_html_joined) for row in html
        ]

    html = "\n".join(html)

    return html


def gv_pin(pinindex, pinname, pinlabel, pincolor, connector):
    pinhtml = []
    pinhtml.append("   <tr>")
    if connector.ports_left:
        pinhtml.append(f'    <td port="p{pinindex+1}l">{pinname}</td>')
    if pinlabel:
        pinhtml.append(f"    <td>{pinlabel}</td>")
    if connector.pincolors:
        if pincolor in wv_colors._color_hex.keys():
            # fmt: off
            pinhtml.append(f'    <td sides="tbl">{translate_color(pincolor, harness_options.color_mode)}</td>')
            pinhtml.append( '    <td sides="tbr">')
            pinhtml.append( '     <table border="0" cellborder="1"><tr>')
            pinhtml.append(f'      <td bgcolor="{wv_colors.translate_color(pincolor, "HEX")}" width="8" height="8" fixedsize="true"></td>')
            pinhtml.append( '     </tr></table>')
            pinhtml.append( '    </td>')
            # fmt: on
        else:
            pinhtml.append('    <td colspan="2"></td>')

    if connector.ports_right:
        pinhtml.append(f'    <td port="p{pinindex+1}r">{pinname}</td>')
    pinhtml.append("   </tr>")

    pinhtml = "\n".join(pinhtml)

    return pinhtml


def gv_connector_loops(connector: Connector) -> List:
    loop_edges = []
    if connector.ports_left:
        loop_side = "l"
        loop_dir = "w"
    elif connector.ports_right:
        loop_side = "r"
        loop_dir = "e"
    else:
        raise Exception("No side for loops")
    for loop in connector.loops:
        head = f"{connector.name}:p{loop[0]}{loop_side}:{loop_dir}"
        tail = f"{connector.name}:p{loop[1]}{loop_side}:{loop_dir}"
        loop_edges.append((head, tail))
    return loop_edges


def nested_html_table(
    rows: List[Union[str, List[Optional[str]], None]], table_attrs: str = ""
) -> str:
    # input: list, each item may be scalar or list
    # output: a parent table with one child table per parent item that is list, and one cell per parent item that is scalar
    # purpose: create the appearance of one table, where cell widths are independent between rows
    # attributes in any leading <tdX> inside a list are injected into to the preceeding <td> tag
    html = []
    html.append(
        f'<table border="0" cellspacing="0" cellpadding="0"{table_attrs or ""}>'
    )

    num_rows = 0
    for row in rows:
        if isinstance(row, List):
            if len(row) > 0 and any(row):
                html.append(" <tr><td>")
                # fmt: off
                html.append('  <table border="0" cellspacing="0" cellpadding="3" cellborder="1"><tr>')
                # fmt: on
                for cell in row:
                    if cell is not None:
                        # Inject attributes to the preceeding <td> tag where needed
                        # fmt: off
                        html.append(f'   <td balign="left">{cell}</td>'.replace("><tdX", ""))
                        # fmt: on
                html.append("  </tr></table>")
                html.append(" </td></tr>")
                num_rows = num_rows + 1
        elif row is not None:
            html.append(" <tr><td>")
            html.append(f"  {row}")
            html.append(" </td></tr>")
            num_rows = num_rows + 1
    if num_rows == 0:  # empty table
        # generate empty cell to avoid GraphViz errors
        html.append("<tr><td></td></tr>")
    html.append("</table>")
    return html


def html_bgcolor_attr(color: Color) -> str:
    """Return attributes for bgcolor or '' if no color."""
    return f' bgcolor="{translate_color(color, "HEX")}"' if color else ""


def html_bgcolor(color: Color, _extra_attr: str = "") -> str:
    """Return <td> attributes prefix for bgcolor or '' if no color."""
    return f"<tdX{html_bgcolor_attr(color)}{_extra_attr}>" if color else ""


def html_colorbar(color: Color) -> str:
    """Return <tdX> attributes prefix for bgcolor and minimum width or None if no color."""
    return html_bgcolor(color, ' width="4"') if color else None


def html_image(image):
    from wireviz.DataClasses import Image

    if not image:
        return None
    # The leading attributes belong to the preceeding tag. See where used below.
    html = f'{html_size_attr(image)}><img scale="{image.scale}" src="{image.src}"/>'
    if image.fixedsize:
        # Close the preceeding tag and enclose the image cell in a table without
        # borders to avoid narrow borders when the fixed width < the node width.
        html = f""">
    <table border="0" cellspacing="0" cellborder="0"><tr>
     <td{html}</td>
    </tr></table>
   """
    return f"""<tdX{' sides="TLR"' if image.caption else ''}{html_bgcolor_attr(image.bgcolor)}{html}"""


def html_caption(image):
    from wireviz.DataClasses import Image

    return (
        f'<tdX sides="BLR"{html_bgcolor_attr(image.bgcolor)}>{html_line_breaks(image.caption)}'
        if image and image.caption
        else None
    )


def html_size_attr(image):
    from wireviz.DataClasses import Image

    # Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object
    return (
        (
            (f' width="{image.width}"' if image.width else "")
            + (f' height="{image.height}"' if image.height else "")
            + (' fixedsize="true"' if image.fixedsize else "")
        )
        if image
        else ""
    )


def html_line_breaks(inp):
    return remove_links(inp).replace("\n", "<br />") if isinstance(inp, str) else inp
