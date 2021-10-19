# -*- coding: utf-8 -*-

import re
from itertools import zip_longest
from typing import Any, List, Optional, Union

from wireviz import APP_NAME, APP_URL, __version__
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
        if component.style != "simple":
            line_ports = gv_pin_table(component)
        else:
            line_ports = None
    elif isinstance(component, Cable):
        line_ports = gv_conductor_table(component, harness_options)

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

    if component.bgcolor:
        tbl_bgcolor = translate_color(component.bgcolor, "HEX")
    elif isinstance(component, Connector) and harness_options.bgcolor_connector:
        tbl_bgcolor = translate_color(harness_options.bgcolor_connector, "HEX")
    elif isinstance(component, Cable) and harness_options.bgcolor_cable:
        tbl_bgcolor = translate_color(harness_options.bgcolor_cable, "HEX")

    tbl = nested_table(lines)
    tbl.update_attribs(bgcolor=tbl_bgcolor)
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


def nested_table(lines: List[Td]) -> Table:
    cell_lists = [make_list_of_cells(line) for line in lines]
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
            inner_table = Table(
                Tr(cells), border=0, cellspacing=0, cellpadding=3, cellborder=1
            )
        rows.append(Tr(Td(inner_table)))

    if len(rows) == 0:  # create dummy row to avoid GraphViz errors due to empty <table>
        rows = Tr(Td(""))
    tbl = Table(rows, border=0, cellspacing=0, cellpadding=0)
    return tbl


def gv_pin_table(component) -> Table:
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
    tbl = Table(pin_rows, border=0, cellspacing=0, cellpadding=3, cellborder=1)
    return tbl


def gv_pin_row(pin_index, pin_name, pin_label, pin_color, connector) -> Tr:
    cell_pin_left = Td(pin_name, port=f"p{pin_index+1}l")
    cell_pin_label = Td(pin_label, delete_if_empty=True)
    cell_pin_right = Td(pin_name, port=f"p{pin_index+1}r")

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


def gv_conductor_table(cable, harness_options) -> Table:
    rows = []
    rows.append(Tr(Td("&nbsp;")))  # spacer row on top

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
        color_list = ["#000000"] + get_color_hex(connection_color, pad=harness_options._pad) + ["#000000"]
        rows.append(Tr(gv_wire_cell(i, color_list)))

        # row below the wire
        # TODO: PN stuff for bundles

    if cable.shield:
        rows.append(Tr(Td("&nbsp;")))  # spacer between wires and shield
        # row above the shield
        cells_above = [
            Td("<!-- s_in -->"),
            Td("Shield"),
            Td("<!-- s_out -->"),
        ]
        rows.append(Tr(cells_above))
        # thw shield itself
        if isinstance(cable.shield, str):
            color_list = ["#000000"] + get_color_hex(cable.shield) + ["#000000"]
        else:
            color_list = ["#000000"]
        rows.append(Tr(gv_wire_cell("s", color_list)))

    rows.append(Tr(Td("&nbsp;")))  # spacer row on bottom
    tbl = Table(rows, border=0, cellspacing=0, cellborder=0)
    return tbl


def gv_wire_cell(index, color_list) -> Td:
    wire_inner_rows = []
    for j, bgcolor in enumerate(color_list[::-1]):
        wire_inner_cell_attribs = {
            "colspan": 3,
            "cellpadding": 0,
            "height": 2,
            "border": 0,
            "bgcolor": bgcolor if bgcolor != "" else "BK",
        }
        wire_inner_rows.append(Tr(Td("", **wire_inner_cell_attribs)))
    wire_inner_table = Table(wire_inner_rows, cellspacing=0, cellborder=0, border=0)
    wire_outer_cell_attribs = {
        "colspan": 3,
        "border": 0,
        "cellspacing": 0,
        "port": f"w{index}",
        "height": 2 * len(color_list),
    }
    wire_outer_cell = Td(wire_inner_table, **wire_outer_cell_attribs)

    return wire_outer_cell


def colored_cell(contents, bgcolor) -> Td:
    return Td(contents, bgcolor=translate_color(bgcolor, "HEX"))


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


def colorbar_cell(color) -> Td:
    if color:
        return Td("", bgcolor=translate_color(color, "HEX"), width=4)
    else:
        return None


def image_and_caption_cells(component: Component) -> (Td, Td):
    if not component.image:
        return (None, None)

    image_tag = Img(scale=component.image.scale, src=component.image.src)
    image_cell_inner = Td(image_tag, flat=True)
    if component.image.fixedsize:
        # further nest the image in a table with width/height/fixedsize parameters, and place that table in a cell
        image_cell_inner.update_attribs(**html_size_attr_dict(component.image))
        image_cell = Td(
            Table(Tr(image_cell_inner), border=0, cellspacing=0, cellborder=0, id="!")
        )
    else:
        image_cell = image_cell_inner

    image_cell.update_attribs(
        balign="left",
        bgcolor=translate_color(component.image.bgcolor, "HEX"),
        sides="TLR" if component.image.caption else None,
    )

    if component.image.caption:
        caption_cell = Td(
            f"{html_line_breaks(component.image.caption)}", balign="left", sides="BLR"
        )
    else:
        caption_cell = None
    return (image_cell, caption_cell)


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


def set_dot_basics(dot, options):
    dot.body.append(f"// Graph generated by {APP_NAME} {__version__}\n")
    dot.body.append(f"// {APP_URL}\n")
    dot.attr(
        "graph",
        rankdir="LR",
        ranksep="2",
        bgcolor=translate_color(options.bgcolor, "HEX"),
        nodesep="0.33",
        fontname=options.fontname,
    )
    dot.attr(
        "node",
        shape="none",
        width="0",
        height="0",
        margin="0",  # Actual size of the node is entirely determined by the label.
        style="filled",
        fillcolor=translate_color(options.bgcolor_node, "HEX"),
        fontname=options.fontname,
    )
    dot.attr("edge", style="bold", fontname=options.fontname)


def apply_dot_tweaks(dot, tweak):
    def typecheck(name: str, value: Any, expect: type) -> None:
        if not isinstance(value, expect):
            raise Exception(
                f"Unexpected value type of {name}: Expected {expect}, got {type(value)}\n{value}"
            )

    # TODO?: Differ between override attributes and HTML?
    if tweak.override is not None:
        typecheck("tweak.override", tweak.override, dict)
        for k, d in tweak.override.items():
            typecheck(f"tweak.override.{k} key", k, str)
            typecheck(f"tweak.override.{k} value", d, dict)
            for a, v in d.items():
                typecheck(f"tweak.override.{k}.{a} key", a, str)
                typecheck(f"tweak.override.{k}.{a} value", v, (str, type(None)))

        # Override generated attributes of selected entries matching tweak.override.
        for i, entry in enumerate(dot.body):
            if not isinstance(entry, str):
                continue
            # Find a possibly quoted keyword after leading TAB(s) and followed by [ ].
            match = re.match(r'^\t*(")?((?(1)[^"]|[^ "])+)(?(1)") \[.*\]$', entry, re.S)
            keyword = match and match[2]
            if not keyword in tweak.override.keys():
                continue

            for attr, value in tweak.override[keyword].items():
                if value is None:
                    entry, n_subs = re.subn(
                        f'( +)?{attr}=("[^"]*"|[^] ]*)(?(1)| *)', "", entry
                    )
                    if n_subs < 1:
                        print(
                            f"Harness.create_graph() warning: {attr} not found in {keyword}!"
                        )
                    elif n_subs > 1:
                        print(
                            f"Harness.create_graph() warning: {attr} removed {n_subs} times in {keyword}!"
                        )
                    continue

                if len(value) == 0 or " " in value:
                    value = value.replace('"', r"\"")
                    value = f'"{value}"'
                entry, n_subs = re.subn(
                    f'{attr}=("[^"]*"|[^] ]*)', f"{attr}={value}", entry
                )
                if n_subs < 1:
                    # If attr not found, then append it
                    entry = re.sub(r"\]$", f" {attr}={value}]", entry)
                elif n_subs > 1:
                    print(
                        f"Harness.create_graph() warning: {attr} overridden {n_subs} times in {keyword}!"
                    )

            dot.body[i] = entry

    if tweak.append is not None:
        if isinstance(tweak.append, list):
            for i, element in enumerate(tweak.append, 1):
                typecheck(f"tweak.append[{i}]", element, str)
            dot.body.extend(tweak.append)
        else:
            typecheck("tweak.append", tweak.append, str)
            dot.body.append(tweak.append)
