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


def gv_node_connector(connector: Connector, harness_options: Options) -> Table:
    # If no wires connected (except maybe loop wires)?
    if not (connector.ports_left or connector.ports_right):
        connector.ports_left = True  # Use left side pins by default

    # generate all rows to be shown in the node
    if connector.show_name:
        str_name = [f"{remove_links(connector.name)}"]
        if connector.bgcolor_title:
            row_name_attribs = {
                "bgcolor": translate_color(connector.bgcolor_title, "HEX")
            }
            row_name = [Td(str_name, attribs=row_name_attribs)]
        else:
            row_name = [str_name]
    else:
        row_name = []

    row_pn = [
        pn_info_string(HEADER_PN, None, connector.pn),
        pn_info_string(HEADER_MPN, connector.manufacturer, connector.mpn),
        pn_info_string(HEADER_SPN, connector.supplier, connector.spn),
    ]
    row_pn = [html_line_breaks(cell) for cell in row_pn]

    if connector.color:
        colorbar_attribs = {
            "bgcolor": translate_color(connector.color, "HEX"),
            "width": 4,
        }
        colorbar_cell = Td("", attribs=colorbar_attribs)
    else:
        colorbar_cell = None

    row_info = [
        html_line_breaks(connector.type),
        html_line_breaks(connector.subtype),
        f"{connector.pincount}-pin" if connector.show_pincount else None,
        translate_color(connector.color, harness_options.color_mode),
        colorbar_cell,
    ]

    # <tdX{' sides="TLR"' if image.caption else ''}
    # <tdX sides="BLR"{html_bgcolor_attr(image.bgcolor)}>
    # {html_size_attr(image)}
    if connector.image and connector.image.caption:
        # import pudb; pudb.set_trace()
        row_image_attribs = html_size_attr_dict(connector.image)
        row_image_attribs["balign"] = "left"
        row_image_attribs["sides"] = "TLR"
        if connector.image.bgcolor:
            row_image_attribs["bgcolor"] = translate_color(
                connector.image.bgcolor, "HEX"
            )
        row_caption_attribs = {"balign": "left", "sides": "BLR"}
        row_image = [Td(html_image_new(connector.image), attribs=row_image_attribs)]
        row_image_caption = [
            Td(
                html_caption_new(connector.image),
                attribs=row_caption_attribs,
                flat=True,
            )
        ]
    else:
        row_image = []
        row_image_caption = []
    row_notes = [html_line_breaks(connector.notes)]
    # row_additional_component_table = get_additional_component_table(self, connector)
    row_additional_component_table = None

    if connector.style != "simple":
        pin_tuples = zip_longest(
            connector.pins,
            connector.pinlabels,
            connector.pincolors,
        )

        pin_rows = []
        for pinindex, (pinname, pinlabel, pincolor) in enumerate(pin_tuples):
            if connector.should_show_pin(pinname):
                pin_rows.append(
                    gv_pin_row(pinindex, pinname, pinlabel, pincolor, connector)
                )

        table_attribs = {
            "border": 0,
            "cellspacing": 0,
            "cellpadding": 3,
            "cellborder": 1,
        }
        row_connector_table = str(Table(pin_rows, attribs=table_attribs))
    else:
        row_connector_table = None

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

    tbl = nested_table(rows)

    if connector.bgcolor:
        tbl.attribs["bgcolor"] = translate_color(connector.bgcolor, "HEX")
    elif harness_options.bgcolor_connector:
        tbl.attribs["bgcolor"]  = translate_color(harness_options.bgcolor_connector, "HEX")

    return tbl


def gv_pin_row(pin_index, pin_name, pin_label, pin_color, connector):
    cell_pin_left = Td(pin_name, attribs={"port": f"p{pin_index+1}l"}, flat=True)
    cell_pin_label = Td(pin_label, flat=True, empty_is_none=True)
    cell_pin_right = Td(pin_name, attribs={"port": f"p{pin_index+1}r"}, flat=True)

    cells = [
        cell_pin_left if connector.ports_left else None,
        cell_pin_label,
        cell_pin_right if connector.ports_right else None,
    ]
    return Tr(cells)


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


def nested_table(rows_in: List[Tr]):
    outer_rows = []
    for row in rows_in:
        if isinstance(row, List) and len(row) > 0 and any(row):
            # remove rows which are none
            row_no_empty = [cell for cell in row if cell is not None]
            inner_cells = []
            for cell in row_no_empty:
                if isinstance(cell, Td):
                    inner_cells.append(cell)
                else:
                    inner_cell_attribs = {"balign": "left"}
                    inner_cells.append(Td(cell, attribs=inner_cell_attribs, flat=True))

            inner_table_attribs = {
                "border": 0,
                "cellspacing": 0,
                "cellpadding": 3,
                "cellborder": 1,
            }
            if len(inner_cells) > 0:
                inner_table = Table(Tr(inner_cells), attribs=inner_table_attribs)
                outer_rows.append(Tr(Td(inner_table)))
        elif row is not None and any(row):
            outer_rows.append(Tr(Td(row)))
    if len(outer_rows) == 0:
        outer_rows = Tr(Td(""))  # Generate empty cell to avoid GraphViz errors
    outer_table_attribs = {"border": 0, "cellspacing": 0, "cellpadding": 0}
    outer_table = Table(outer_rows, attribs=outer_table_attribs)

    return outer_table


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


def html_image_new(image):
    from wireviz.DataClasses import Image

    if not image:
        return None
    # The leading attributes belong to the preceeding tag. See where used below.
    html = f'<img scale="{image.scale}" src="{image.src}"/>'
    if image.fixedsize:
        # Close the preceeding tag and enclose the image cell in a table without
        # borders to avoid narrow borders when the fixed width < the node width.
        html = f"""
    <table border="0" cellspacing="0" cellborder="0"><tr>
     <td>{html}</td>
    </tr></table>
   """
    return f"{html_bgcolor_attr(image.bgcolor)}{html}"


def html_caption(image):
    from wireviz.DataClasses import Image

    return (
        f'<tdX sides="BLR"{html_bgcolor_attr(image.bgcolor)}>{html_line_breaks(image.caption)}'
        if image and image.caption
        else None
    )


def html_caption_new(image):
    from wireviz.DataClasses import Image

    return f"{html_line_breaks(image.caption)}" if image and image.caption else None


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


def html_size_attr_dict(image):
    # Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object
    from wireviz.DataClasses import Image

    attr_dict = {}
    if image:
        if image.width:
            attr_dict["width"] = image.width
        if image.height:
            attr_dict["height"] = image.height
        if image.fixedsize:
            attr_dict["fixedsize"] = "true"
    return attr_dict


def html_line_breaks(inp):
    return remove_links(inp).replace("\n", "<br />") if isinstance(inp, str) else inp
