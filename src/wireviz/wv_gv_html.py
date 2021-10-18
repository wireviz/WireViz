# -*- coding: utf-8 -*-

import re
from itertools import zip_longest
from typing import List, Optional, Union

from wireviz.DataClasses import Cable, Color, Component, Connector, Options
from wireviz.wv_colors import get_color_hex, translate_color
from wireviz.wv_helper import pn_info_string, remove_links
from wireviz.wv_table_util import *  # TODO: explicitly import each needed tag later

HEADER_PN = "P/N"
HEADER_MPN = "MPN"
HEADER_SPN = "SPN"


def gv_node_component(
    component: Component, harness_options: Options, pad=None
) -> Table:
    # If no wires connected (except maybe loop wires)?
    if isinstance(component, Connector):
        if not (component.ports_left or component.ports_right):
            component.ports_left = True  # Use left side pins by default

    # generate all rows to be shown in the node
    if component.show_name:
        str_name = f"{remove_links(component.name)}"
        line_name = colored_cell(str_name, component.bgcolor_title)
    else:
        line_name = None

    line_pn = part_number_str_list(component)

    if isinstance(component, Connector):
        line_info = [
            html_line_breaks(component.type),
            html_line_breaks(component.subtype),
            f"{component.pincount}-pin" if component.show_pincount else None,
            translate_color(component.color, harness_options.color_mode),
            colorbar_cell(component.color),
        ]
    elif isinstance(component, Cable):
        line_info = [
            html_line_breaks(component.type),
            f"{component.wirecount}x" if component.show_wirecount else None,
            f"{component.gauge_str}" if component.gauge else None,
            "+ S" if component.shield else None,
            f"{component.length} {component.length_unit}"
            if component.length > 0
            else None,
            translate_color(component.color, harness_options.color_mode),
            colorbar_cell(component.color),
        ]

    line_image, line_image_caption = image_and_caption_cells(component)

    # line_additional_component_table = get_additional_component_table(self, connector)
    line_additional_component_table = None
    line_notes = [html_line_breaks(component.notes)]

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
            line_ports = Table(pin_rows, attribs=table_attribs)
        else:
            line_ports = None
    elif isinstance(component, Cable):
        line_ports = gv_conductor_table(component, harness_options, pad)

    lines = [
        line_name,
        line_pn,
        line_info,
        line_ports,
        line_image,
        line_image_caption,
        line_additional_component_table,
        line_notes,
    ]

    cell_lists = [make_list_of_cells(line) for line in lines]

    tbl = nested_table(cell_lists)

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


def nested_table(cell_lists: List[Td]) -> Table:
    outer_table_attribs = {
        "border": 0,
        "cellspacing": 0,
        "cellpadding": 0,
    }
    inner_table_attribs = {
        "border": 0,
        "cellspacing": 0,
        "cellpadding": 3,
        "cellborder": 1,
    }

    rows = []
    for lst in cell_lists:
        if len(lst) == 0:
            continue  # no cells in list
        cells = [item for item in lst if item.contents is not None]
        if len(cells) == 0:
            continue  # no cells in list that are not None
        if (
            len(cells) == 1
            and isinstance(cells[0].contents, Table)
            and not "!" in cells[0].contents.attribs.get("id", "")
        ):
            # cell content is already a table, no need to re-wrap it;
            # unless explicitly asked to by a "!" in the ID field
            # as used by image_and_caption_cells()
            inner_table = cells[0].contents
        else:
            # nest cell content inside a table
            inner_table = Table(Tr(cells), attribs=inner_table_attribs)
        rows.append(Tr(Td(inner_table)))
    if len(rows) == 0:  # create dummy row to avoid GraphViz errors due to empty <table>
        rows = Tr(Td(""))
    tbl = Table(rows, attribs=outer_table_attribs)

    return tbl


def make_list_of_cells(inp) -> List[Td]:
    # inp may be List,
    if isinstance(inp, List):
        # ensure all list items are Td
        list_out = [item if isinstance(item, Td) else Td(item) for item in inp]
        return list_out
    else:
        if inp is None:
            return []
        if isinstance(inp, Td):
            return [inp]
        else:
            return [Td(inp)]


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


def image_and_caption_cells(component: Component) -> (Td, Td):
    if not component.image:
        return (None, None)

    image_tag = Img(
        attribs={"scale": component.image.scale, "src": component.image.src}
    )
    image_cell_inner = Td(image_tag, flat=True)
    if component.image.fixedsize:
        # further nest the image in a table with width/height/fixedsize parameters, and place that table in a cell
        inner_cell_attribs = html_size_attr_dict(component.image)
        image_cell_inner.attribs = Attribs(inner_cell_attribs)
        image_cell = Td(
            Table(
                Tr(image_cell_inner),
                attribs={"border": 0, "cellspacing": 0, "cellborder": 0, "id": "!"},
            )
        )
    else:
        image_cell = image_cell_inner

    outer_cell_attribs = {}
    outer_cell_attribs["balign"] = "left"
    if component.image.bgcolor:
        outer_cell_attribs["bgcolor"] = translate_color(component.image.bgcolor, "HEX")
    if component.image.caption:
        outer_cell_attribs["sides"] = "TLR"
    image_cell.attribs = Attribs(outer_cell_attribs)

    if component.image.caption:
        caption_cell_attribs = {"balign": "left", "sides": "BLR", "id": "td_caption"}
        caption_cell = Td(
            html_caption_new(component.image), attribs=caption_cell_attribs
        )
    else:
        caption_cell = None
    return (image_cell, caption_cell)


def part_number_str_list(component: Component) -> List[str]:
    cell_contents = [
        pn_info_string(HEADER_PN, None, component.pn),
        pn_info_string(HEADER_MPN, component.manufacturer, component.mpn),
        pn_info_string(HEADER_SPN, component.supplier, component.spn),
    ]
    if any(cell_contents):
        return [html_line_breaks(cell) for cell in cell_contents]
    else:
        return None


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
