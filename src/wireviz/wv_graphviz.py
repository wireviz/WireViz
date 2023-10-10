# -*- coding: utf-8 -*-

import re
import warnings
from itertools import zip_longest
from typing import Any, List, Optional, Tuple, Union

from wireviz import APP_NAME, APP_URL, __version__
from wireviz.wv_bom import partnumbers2list
from wireviz.wv_colors import MultiColor
from wireviz.wv_dataclasses import (
    ArrowDirection,
    ArrowWeight,
    Cable,
    Component,
    Connector,
    MateComponent,
    MatePin,
    Options,
    PartNumberInfo,
    ShieldClass,
    WireClass,
)
from wireviz.wv_html import Img, Table, Td, Tr
from wireviz.wv_utils import html_line_breaks, remove_links


def gv_node_component(component: Component) -> Table:
    # If no wires connected (except maybe loop wires)?
    if isinstance(component, Connector):
        if not (component.ports_left or component.ports_right):
            component.ports_left = True  # Use left side pins by default

    # generate all rows to be shown in the node
    if component.show_name:
        str_name = f"{remove_links(component.designator)}"
        line_name = Td(str_name, bgcolor=component.bgcolor_title.html)
    else:
        line_name = None

    line_pn = partnumbers2list(component.partnumbers)

    is_simple_connector = (
        isinstance(component, Connector) and component.style == "simple"
    )

    if isinstance(component, Connector):
        line_info = [
            bom_bubble(component.bom_id),
            html_line_breaks(component.type),
            html_line_breaks(component.subtype),
            f"{component.pincount}-pin" if component.show_pincount else None,
            str(component.color) if component.color else None,
        ]
    elif isinstance(component, Cable):
        line_info = [
            bom_bubble(component.bom_id) if component.category != "bundle" else None,
            html_line_breaks(component.type),
            f"{component.wirecount}x" if component.show_wirecount else None,
            component.gauge_str_with_equiv,
            "+ S" if component.shield else None,
            component.length_str,
            str(component.color) if component.color else None,
        ]

    if component.additional_parameters:
        line_additional_parameters = nested_table_dict(component.additional_parameters)
    else:
        line_additional_parameters = []

    if component.color:
        line_info.extend(colorbar_cells(component.color))

    line_image, line_image_caption = image_and_caption_cells(component)
    line_additional_component_table = gv_additional_component_table(component)
    line_notes = [Td(html_line_breaks(component.notes), balign="left")]

    if isinstance(component, Connector):
        if component.style != "simple":
            line_ports = gv_pin_table(component)
        else:
            line_ports = None
    elif isinstance(component, Cable):
        line_ports = gv_conductor_table(component)

    lines = [
        line_name,
        line_pn,
        line_info,
        line_additional_parameters,
        line_ports,
        line_image,
        line_image_caption,
        line_additional_component_table,
        line_notes,
    ]

    tbl = nested_table(lines)
    if is_simple_connector:
        # Simple connectors have no pin table, and therefore, no ports to attach wires to.
        # Manually assign left and right ports here if required.
        # Use table itself for right port, and the first cell for left port.
        # Even if the table only has one cell, two separate ports can still be assigned.
        tbl.update_attribs(port="p1r")
        first_cell_in_tbl = tbl.contents[0].contents
        first_cell_in_tbl.update_attribs(port="p1l")

    return tbl


def gv_additional_component_table(component):
    if not component.additional_components:
        return None

    rows = []
    for subitem in component.additional_components:
        firstline = [
            Td(bom_bubble(subitem.bom_id)),
            Td(f"{subitem.bom_qty}", align="right"),
            Td(f"{subitem.qty.unit if subitem.qty.unit else 'x'}", align="left"),
            Td(f"{subitem.description}", align="left"),
            Td(f"{subitem.note if subitem.note else ''}", align="left"),
        ]
        rows.append(Tr(firstline))

        if subitem.has_pn_info:
            secondline = [
                Td("", colspan=3),
                Td(f"# TODO PN string", align="left"),  # TODO
                Td(""),
            ]
            rows.append(Tr(secondline))

    return Table(rows, border=1, cellborder=0, cellpadding=3, cellspacing=0)


def calculate_node_bgcolor(component, harness_options):
    # assign component node bgcolor at the GraphViz node level
    # instead of at the HTML table level for better rendering of node outline
    if component.bgcolor:
        return component.bgcolor.html
    elif isinstance(component, Connector) and harness_options.bgcolor_connector:
        return harness_options.bgcolor_connector.html
    elif (
        isinstance(component, Cable)
        and component.category == "bundle"
        and harness_options.bgcolor_bundle
    ):
        return harness_options.bgcolor_bundle.html
    elif isinstance(component, Cable) and harness_options.bgcolor_cable:
        return harness_options.bgcolor_cable.html


def bom_bubble(id) -> Table:
    if id is None:
        return None
    else:
        # TODO: activate BOM bubbles
        return None
        # size and style of BOM bubble is optimized to be a rounded square,
        # big enough to hold any two-digit ID without GraphViz warnings
        text = id
        # text = f'<FONT COLOR="#FFFFFF">{id}</FONT>'
        return Table(
            Tr(
                Td(
                    text,
                    border=1,
                    cellpadding=0,
                    fixedsize="true",
                    style="rounded",
                    height=20,
                    width=20,
                    # bgcolor="#000000",
                )
            ),
            border=0,
        )


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
            continue  # no cells in list, or all cells are None
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
                Tr(cells), border=0, cellborder=1, cellpadding=3, cellspacing=0
            )
        rows.append(Tr(Td(inner_table)))

    if len(rows) == 0:  # create dummy row to avoid GraphViz errors due to empty <table>
        inner_table = Table(
            Tr(Td("")), border=0, cellborder=1, cellpadding=3, cellspacing=0
        )
        rows = [Tr(Td(inner_table))]
    tbl = Table(rows, border=0, cellspacing=0, cellpadding=0)
    return tbl


def nested_table_dict(d: dict) -> Table:
    rows = []
    for k, v in d.items():
        rows.append(
            Tr(
                [
                    Td(k, align="left", balign="left", valign="top"),
                    Td(html_line_breaks(v), align="left", balign="left"),
                ]
            )
        )
    return Table(rows, border=0, cellborder=1, cellpadding=3, cellspacing=0)


def gv_pin_table(component) -> Table:
    pin_rows = []
    for pin in component.pin_objects.values():
        if component.should_show_pin(pin.id):
            pin_rows.append(gv_pin_row(pin, component))
    if len(pin_rows) == 0:
        # TODO: write test for empty pin tables, and for unconnected connectors that hide disconnected pins
        pass
    tbl = Table(pin_rows, border=0, cellborder=1, cellpadding=3, cellspacing=0)
    return tbl


def gv_pin_row(pin, connector) -> Tr:
    # ports in GraphViz are 1-indexed for more natural maping to pin/wire numbers
    has_pincolors = any([_pin.color for _pin in connector.pin_objects.values()])
    cells = [
        Td(pin.id, port=f"p{pin.index+1}l") if connector.ports_left else None,
        Td(pin.label, delete_if_empty=True),
        Td(str(pin.color) if pin.color else "", sides="TBL") if has_pincolors else None,
        Td(color_minitable(pin.color), sides="TBR") if has_pincolors else None,
        Td(pin.id, port=f"p{pin.index+1}r") if connector.ports_right else None,
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
        head = f"{connector.designator}:p{loop[0]}{loop_side}:{loop_dir}"
        tail = f"{connector.designator}:p{loop[1]}{loop_side}:{loop_dir}"
        loop_edges.append((head, tail))
    return loop_edges


def gv_conductor_table(cable) -> Table:
    rows = []
    rows.append(Tr(Td("&nbsp;")))  # spacer row on top

    inserted_break_inbetween = False
    for wire in cable.wire_objects.values():
        # insert blank space between wires and shields
        if isinstance(wire, ShieldClass) and not inserted_break_inbetween:
            rows.append(Tr(Td("&nbsp;")))  # spacer row between wires and shields
            inserted_break_inbetween = True

        # row above the wire
        wireinfo = []
        if cable.show_wirenumbers and not isinstance(wire, ShieldClass):
            wireinfo.append(str(wire.id))
        wireinfo.append(str(wire.color))
        wireinfo.append(wire.label)

        ins, outs = [], []
        for conn in cable._connections:
            if conn.via.id == wire.id:
                if conn.from_ is not None:
                    ins.append(str(conn.from_))
                if conn.to is not None:
                    outs.append(str(conn.to))

        cells_above = [
            Td(" " + ", ".join(ins), align="left"),
            Td(" "),  # increase cell spacing here
            Td(bom_bubble(wire.bom_id)) if cable.category == "bundle" else None,
            Td(":".join([wi for wi in wireinfo if wi is not None and wi != ""])),
            Td(" "),  # increase cell spacing here
            Td(", ".join(outs) + " ", align="right"),
        ]
        cells_above = [cell for cell in cells_above if cell is not None]
        rows.append(Tr(cells_above))

        # the wire itself
        rows.append(Tr(gv_wire_cell(wire, len(cells_above))))

        # row below the wire
        if wire.partnumbers:
            cells_below = partnumbers2list(
                wire.partnumbers, parent_partnumbers=cable.partnumbers
            )
            if cells_below is not None and len(cells_below) > 0:
                table_below = (
                    Table(
                        Tr([Td(cell) for cell in cells_below]),
                        border=0,
                        cellborder=0,
                        cellspacing=0,
                    ),
                )
                rows.append(Tr(Td(table_below, colspan=len(cells_above))))

    rows.append(Tr(Td("&nbsp;")))  # spacer row on bottom
    tbl = Table(rows, border=0, cellborder=0, cellspacing=0)
    return tbl


def gv_wire_cell(wire: Union[WireClass, ShieldClass], colspan: int) -> Td:
    if wire.color:
        color_list = ["#000000"] + wire.color.html_padded_list + ["#000000"]
    else:
        color_list = ["#000000"]

    wire_inner_rows = []
    for j, bgcolor in enumerate(color_list[::-1]):
        wire_inner_cell_attribs = {
            "bgcolor": bgcolor if bgcolor != "" else "#000000",
            "border": 0,
            "cellpadding": 0,
            "colspan": colspan,
            "height": 2,
        }
        wire_inner_rows.append(Tr(Td("", **wire_inner_cell_attribs)))
    wire_inner_table = Table(wire_inner_rows, border=0, cellborder=0, cellspacing=0)
    wire_outer_cell_attribs = {
        "border": 0,
        "cellspacing": 0,
        "cellpadding": 0,
        "colspan": colspan,
        "height": 2 * len(color_list),
        "port": f"w{wire.index+1}",
    }
    # ports in GraphViz are 1-indexed for more natural maping to pin/wire numbers
    wire_outer_cell = Td(wire_inner_table, **wire_outer_cell_attribs)

    return wire_outer_cell


def gv_edge_wire(harness, cable, connection) -> Tuple[str, str, str, str, str]:
    if connection.via.color:
        # check if it's an actual wire and not a shield
        color = f"#000000:{connection.via.color.html_padded}:#000000"
    else:  # it's a shield connection
        color = "#000000"

    if connection.from_ is not None:  # connect to left
        from_port_str = (
            f":p{connection.from_.index+1}r"
            if harness.connectors[connection.from_.parent].style != "simple"
            else ""
        )
        code_left_1 = f"{connection.from_.parent}{from_port_str}:e"
        code_left_2 = f"{connection.via.parent}:w{connection.via.index+1}:w"
        # ports in GraphViz are 1-indexed for more natural maping to pin/wire numbers
    else:
        code_left_1, code_left_2 = None, None

    if connection.to is not None:  # connect to right
        to_port_str = (
            f":p{connection.to.index+1}l"
            if harness.connectors[connection.to.parent].style != "simple"
            else ""
        )
        code_right_1 = f"{connection.via.parent}:w{connection.via.index+1}:e"
        code_right_2 = f"{connection.to.parent}{to_port_str}:w"
    else:
        code_right_1, code_right_2 = None, None

    return color, code_left_1, code_left_2, code_right_1, code_right_2


def parse_arrow_str(inp: str) -> ArrowDirection:
    if inp[0] == "<" and inp[-1] == ">":
        return ArrowDirection.BOTH
    elif inp[0] == "<":
        return ArrowDirection.BACK
    elif inp[-1] == ">":
        return ArrowDirection.FORWARD
    else:
        return ArrowDirection.NONE


def gv_edge_mate(mate) -> Tuple[str, str, str, str]:
    if mate.arrow.weight == ArrowWeight.SINGLE:
        color = "#000000"
    elif mate.arrow.weight == ArrowWeight.DOUBLE:
        color = "#000000:#000000"

    dir = mate.arrow.direction.name.lower()

    if isinstance(mate, MatePin):
        from_pin_index = mate.from_.index
        from_port_str = f":p{from_pin_index+1}r"
        from_designator = mate.from_.parent
        to_pin_index = mate.to.index
        to_port_str = f":p{to_pin_index+1}l"
        to_designator = mate.to.parent
    elif isinstance(mate, MateComponent):
        from_designator = mate.from_
        from_port_str = ""
        to_designator = mate.to
        to_port_str = ""
    else:
        raise Exception(f"Unknown type of mate:\n{mate}")

    code_from = f"{from_designator}{from_port_str}:e"
    code_to = f"{to_designator}{to_port_str}:w"

    return color, dir, code_from, code_to


def colorbar_cells(color, mini=False) -> List[Td]:
    cells = []
    mini = {"height": 8, "width": 8, "fixedsize": "true"} if mini else {}
    for index, subcolor in enumerate(color.colors):
        sides_l = "L" if index == 0 else ""
        sides_r = "R" if index == len(color.colors) - 1 else ""
        sides = "TB" + sides_l + sides_r
        cells.append(Td("", bgcolor=subcolor.html, sides=sides, **mini))
    return cells


def color_minitable(color: Optional[MultiColor]) -> Union[Table, str]:
    if color is None or len(color) == 0:
        return ""

    cells = colorbar_cells(color, mini=True)

    return Table(
        Tr(cells),
        border=0,
        cellborder=1,
        cellspacing=0,
        height=8,
        width=8 * len(cells),
        fixedsize="true",
    )


def image_and_caption_cells(component: Component) -> Tuple[Td, Td]:
    if not component.image:
        return (None, None)

    image_tag = Img(scale=component.image.scale, src=component.image.src)
    image_cell_inner = Td(image_tag, flat=True)
    if component.image.fixedsize:
        # further nest the image in a table with width/height/fixedsize parameters,
        # and place that table in a cell
        image_cell_inner.update_attribs(**html_size_attr_dict(component.image))
        image_cell = Td(
            Table(Tr(image_cell_inner), border=0, cellborder=0, cellspacing=0, id="!")
        )
    else:
        image_cell = image_cell_inner

    image_cell.update_attribs(
        balign="left",
        bgcolor=component.image.bgcolor.html,
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
    pass

    attr_dict = {}
    if image:
        if image.width:
            attr_dict["width"] = image.width
        if image.height:
            attr_dict["height"] = image.height
        if image.fixedsize:
            attr_dict["fixedsize"] = "true"
    return attr_dict


def set_dot_basics(dot, options):
    dot.body.append(f"// Graph generated by {APP_NAME} {__version__}\n")
    dot.body.append(f"// {APP_URL}\n")
    dot.attr(
        "graph",
        rankdir="LR",
        ranksep="2",
        bgcolor=options.bgcolor.html,
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
        fillcolor=options.bgcolor_node.html,
        fontname=options.fontname,
    )
    dot.attr("edge", style="bold", fontname=options.fontname)


def apply_dot_tweaks(dot, tweak):
    def typecheck(name: str, value: Any, expect: type) -> None:
        if not isinstance(value, expect):
            raise Exception(
                f"Unexpected value type of {name}: "
                f"Expected {expect}, got {type(value)}\n{value}"
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
                        warnings.warn(f"tweak: {attr} not found in {keyword}!")
                    elif n_subs > 1:
                        warnings.warn(f"tweak: {attr} removed {n_subs} times in {keyword}!")
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
                    warnings.warn(f"tweak: {attr} overridden {n_subs} times in {keyword}!")

            dot.body[i] = entry

    if tweak.append is not None:
        if isinstance(tweak.append, list):
            for i, element in enumerate(tweak.append, 1):
                typecheck(f"tweak.append[{i}]", element, str)
            dot.body.extend(tweak.append)
        else:
            typecheck("tweak.append", tweak.append, str)
            dot.body.append(tweak.append)
