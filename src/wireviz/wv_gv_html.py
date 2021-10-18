# -*- coding: utf-8 -*-

import re
from itertools import zip_longest
from typing import List, Optional, Union

from wireviz.DataClasses import Cable, Color, Connector, Component, Options
from wireviz.wv_colors import get_color_hex, translate_color
from wireviz.wv_helper import pn_info_string, remove_links
from wireviz.wv_table_util import *  # TODO: explicitly import each needed tag later

HEADER_PN = "P/N"
HEADER_MPN = "MPN"
HEADER_SPN = "SPN"


def gv_node_component(component: Component, harness_options: Options, pad=None) -> Table:
    # If no wires connected (except maybe loop wires)?
    if isinstance(component, Connector):
        if not (component.ports_left or component.ports_right):
            component.ports_left = True  # Use left side pins by default

    # generate all rows to be shown in the node
    if component.show_name:
        str_name = f"{remove_links(component.name)}"
        row_name = [colored_cell(str_name, component.bgcolor_title)]
    else:
        row_name = []

    row_pn = par_number_cell_list(component)

    if isinstance(component, Connector):
        row_info = [
            html_line_breaks(component.type),
            html_line_breaks(component.subtype),
            f"{component.pincount}-pin" if component.show_pincount else None,
            translate_color(component.color, harness_options.color_mode),
            colorbar_cell(component.color),
        ]
    elif isinstance(component, Cable):
        row_info = [
            html_line_breaks(component.type),
            f"{component.wirecount}x" if component.show_wirecount else None,
            f"{component.gauge_str}" if component.gauge else None,
            "+ S" if component.shield else None,
            f"{component.length} {component.length_unit}" if component.length > 0 else None,
            translate_color(component.color, harness_options.color_mode),
            colorbar_cell(component.color),
        ]

    row_image, row_image_caption = image_and_caption_cells(component)

    # row_additional_component_table = get_additional_component_table(self, connector)
    row_additional_component_table = None
    row_notes = [html_line_breaks(component.notes)]


    if isinstance(component, Connector):
        # pin table
        if component.style != "simple":
            pin_tuples = zip_longest(
                component.pins,
                component.pinlabels,
                component.pincolors,
            )

            pin_rows = []
            for pinindex, (pinname, pinlabel, pincolor) in enumerate(pin_tuples):
                if component.should_show_pin(pinname):
                    pin_rows.append(
                        gv_pin_row(pinindex, pinname, pinlabel, pincolor, component)
                    )

            table_attribs = {
                "border": 0,
                "cellspacing": 0,
                "cellpadding": 3,
                "cellborder": 1,
            }
            row_ports = str(Table(pin_rows, attribs=table_attribs))
        else:
            row_ports = None
    elif isinstance(component, Cable):
        row_ports = str(gv_conductor_table(component, harness_options, pad))

    rows = [
        row_name,
        row_pn,
        row_info,
        row_ports,
        row_image,
        row_image_caption,
        row_additional_component_table,
        row_notes,
    ]

    tbl = nested_table(rows)

    if component.bgcolor:
        tbl.attribs["bgcolor"] = translate_color(component.bgcolor, "HEX")
    else:
        if isinstance(component, Connector) and harness_options.bgcolor_connector:
            tbl.attribs["bgcolor"] = translate_color(
                harness_options.bgcolor_connector, "HEX"
            )
        elif isinstance(component, Cable) and harness_options.bgcolor_cable:
            tbl.attribs["bgcolor"] = translate_color(
                harness_options.bgcolor_cable, "HEX"
            )


    return tbl


def gv_pin_row(pin_index, pin_name, pin_label, pin_color, connector):
    cell_pin_left = Td(pin_name, attribs={"port": f"p{pin_index+1}l"})
    cell_pin_label = Td(pin_label, empty_is_none=True)
    cell_pin_right = Td(pin_name, attribs={"port": f"p{pin_index+1}r"})

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


def gv_conductor_table(cable, harness_options, pad) -> Table:

    rows = []
    rows.append(Tr(Td("&nbsp;")))

    for i, (connection_color, wirelabel) in enumerate(
        zip_longest(cable.colors, cable.wirelabels), 1
    ):

        # row above the wire
        wireinfo = []
        if cable.show_wirenumbers:
            wireinfo.append(str(i))
        colorstr = translate_color(connection_color, harness_options.color_mode)
        if colorstr:
            wireinfo.append(colorstr)
        if cable.wirelabels:
            wireinfo.append(wirelabel if wirelabel is not None else "")

        cells_above = [
            Td(f"<!-- {i}_in -->"),
            Td(":".join(wireinfo)),
            Td(f"<!-- {i}_out -->"),
        ]
        rows.append(Tr(cells_above))

        # the wire itself
        rows.append(Tr(gv_wire_cell(i, connection_color, pad)))

    rows.append(Tr(Td("&nbsp;")))

    table_attribs = {
        "border": 0,
        "cellspacing": 0,
        "cellborder": 0,
    }
    tbl = Table(rows, attribs=table_attribs)

    return tbl


def gv_wire_cell(index, color, pad) -> Td:
    bgcolors = ["#000000"] + get_color_hex(color, pad=pad) + ["#000000"]
    wire_inner_rows = []
    for j, bgcolor in enumerate(bgcolors[::-1]):
        wire_inner_cell_attribs = {
            "colspan": 3,
            "cellpadding": 0,
            "height": 2,
            "border": 0,
            "bgcolor": bgcolor if bgcolor != "" else "BK",
        }
        wire_inner_rows.append(Tr(Td("", attribs=wire_inner_cell_attribs)))
    wire_inner_table_attribs = {"cellspacing": 0, "cellborder": 0, "border": 0}
    wire_inner_table = Table(wire_inner_rows, wire_inner_table_attribs)
    wire_outer_cell_attribs = {
        "colspan": 3,
        "border": 0,
        "cellspacing": 0,
        "port": f"w{index}",
        "height": 2 * len(bgcolors),
    }
    wire_outer_cell = Td(wire_inner_table, attribs=wire_outer_cell_attribs)

    return wire_outer_cell


def colored_cell(contents, bgcolor) -> Td:
    if bgcolor:
        attribs = {"bgcolor": translate_color(bgcolor, "HEX")}
    else:
        attribs = {}
    return Td(contents, attribs=attribs)


def colorbar_cell(color) -> Td:
    if color:
        colorbar_attribs = {
            "bgcolor": translate_color(color, "HEX"),
            "width": 4,
        }
        return Td("", attribs=colorbar_attribs)
    else:
        return None


# def html_image_new(image):
#     from wireviz.DataClasses import Image
#     if not image:
#         return None
#     image_tag = Img(attribs={"scale": image.scale, "src": image.src})
#     image_table = Table(Tr(Td(image_tag, attribs=html_size_attr_dict(image))), attribs={"border": 0, "cellspacing": 0, "cellborder": 0})
#     return image_table

def image_and_caption_cells(component):
    if component.image:
        # outer_cell_attribs = {}
        # outer_cell_attribs["balign"] = "left"
        # outer_cell_attribs["bgcolor"] = translate_color(
        #     component.image.bgcolor, "HEX"
        # )
        # if component.image.caption:
        #     outer_cell_attribs["sides"] = "TLR"

        image_tag = Img(attribs={"scale": component.image.scale, "src": component.image.src})
        cell_attribs = html_size_attr_dict(component.image)
        image_cell = Td(image_tag, attribs=cell_attribs)
        image_row = Tr(image_cell)
        image_table_attribs = {
            "border": 0,
            "cellspacing": 0,
            "cellpadding": 0,
            "cellborder": 1,
        }
        image_table = Table(image_row, attribs=image_table_attribs)
        outer_cell = Td(image_table)
        # return:
        row_image = outer_cell

        if component.image.caption:
            row_caption_attribs = {"balign": "left", "sides": "BLR", "id": "td_caption"}
            row_image_caption = Td(
                html_caption_new(component.image),
                attribs=row_caption_attribs,
            )
        else:
            row_image_caption = None
        return (row_image, row_image_caption)
    else:
        return (None, None)


def par_number_cell_list(component) -> List[Td]:
    cell_contents = [
        pn_info_string(HEADER_PN, None, component.pn),
        pn_info_string(HEADER_MPN, component.manufacturer, component.mpn),
        pn_info_string(HEADER_SPN, component.supplier, component.spn),
    ]
    if any(cell_contents):
        return [Td(html_line_breaks(cell)) for cell in cell_contents]
    else:
        return None


def nested_table(rows_in: List[Tr]) -> Table:
    outer_rows = []
    for row in rows_in:
        if isinstance(row, List) and len(row) > 0 and any(row):
            # row is a nested list
            # remove rows which are none
            row_no_empty = [cell for cell in row if cell is not None]
            # if row item is Td, append directly; else convert to Td
            inner_cells = []
            for cell in row_no_empty:
                if isinstance(cell, Td):
                    inner_cells.append(cell)
                else:
                    inner_cell_attribs = {"balign": "left"}
                    inner_cells.append(Td(cell, attribs=inner_cell_attribs))

            inner_table_attribs = {
                "border": 0,
                "cellspacing": 0,
                "cellpadding": 3,
                "cellborder": 1,
            }
            if len(inner_cells) > 0:
                inner_table = Table(Tr(inner_cells), attribs=inner_table_attribs)
                outer_rows.append(Tr(Td(inner_table)))
        elif row is not None:
            if isinstance(row, Iterable) and not any(row):
                continue
            # row is a single item
            # if item is Td, append directly; else convert to Td
            cell = row if isinstance(row, Td) else Td(row)
            outer_rows.append(Tr(cell))
    if len(outer_rows) == 0:
        outer_rows = Tr(Td(""))  # Generate empty cell to avoid GraphViz errors
    outer_table_attribs = {"border": 0, "cellspacing": 0, "cellpadding": 0}
    outer_table = Table(outer_rows, attribs=outer_table_attribs)

    return outer_table




# def html_image(image):
#     from wireviz.DataClasses import Image
#     if not image:
#         return None
#     # The leading attributes belong to the preceeding tag. See where used below.
#     html = f'{html_size_attr(image)}><img scale="{image.scale}" src="{image.src}"/>'
#     if image.fixedsize:
#         # Close the preceeding tag and enclose the image cell in a table without
#         # borders to avoid narrow borders when the fixed width < the node width.
#         html = f""">
#     <table border="0" cellspacing="0" cellborder="0"><tr>
#      <td{html}</td>
#     </tr></table>
#    """
#     return f"""<tdX{' sides="TLR"' if image.caption else ''}{html_bgcolor_attr(image.bgcolor)}{html}"""




def html_caption_new(image):
    from wireviz.DataClasses import Image

    return f"{html_line_breaks(image.caption)}" if image and image.caption else None


# def html_size_attr(image):
#     from wireviz.DataClasses import Image
#
#     # Return Graphviz HTML attributes to specify minimum or fixed size of a TABLE or TD object
#     return (
#         (
#             (f' width="{image.width}"' if image.width else "")
#             + (f' height="{image.height}"' if image.height else "")
#             + (' fixedsize="true"' if image.fixedsize else "")
#         )
#         if image
#         else ""
#     )


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
