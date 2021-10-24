# -*- coding: utf-8 -*-

import re
from itertools import zip_longest
from typing import Any, List, Union

from wireviz import APP_NAME, APP_URL, __version__
from wireviz.wv_bom import partnumbers_to_list
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
        line_name = colored_cell(str_name, component.bgcolor_title)
    else:
        line_name = None

    line_pn = partnumbers_to_list(component.partnumbers)

    is_simple_connector = (
        isinstance(component, Connector) and component.style == "simple"
    )

    if isinstance(component, Connector):
        line_info = [
            html_line_breaks(component.type),
            html_line_breaks(component.subtype),
            f"{component.pincount}-pin" if component.show_pincount else None,
            str(component.color) if component.color else None,
            colorbar_cell(component.color) if component.color else None,
        ]
    elif isinstance(component, Cable):
        line_info = [
            html_line_breaks(component.type),
            f"{component.wirecount}x" if component.show_wirecount else None,
            component.gauge_str_with_equiv,
            "+ S" if component.shield else None,
            component.length_str,
            str(component.color) if component.color else None,
            colorbar_cell(component.color) if component.color else None,
        ]

    x = colorbar_cell(component.color) if component.color else None

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
        line_ports = gv_conductor_table(component)

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
                Tr(cells), border=0, cellborder=1, cellpadding=3, cellspacing=0
            )
        rows.append(Tr(Td(inner_table)))

    if len(rows) == 0:  # create dummy row to avoid GraphViz errors due to empty <table>
        rows = Tr(Td(""))
    tbl = Table(rows, border=0, cellspacing=0, cellpadding=0)
    return tbl


def gv_pin_table(component) -> Table:
    pin_rows = []
    for pin in component.pin_objects:
        if component.should_show_pin(pin.id):  # TODO remove True
            pin_rows.append(gv_pin_row(pin, component))
    tbl = Table(pin_rows, border=0, cellborder=1, cellpadding=3, cellspacing=0)
    return tbl


def gv_pin_row(pin, connector) -> Tr:
    # ports in GraphViz are 1-indexed for more natural maping to pin/wire numbers
    cell_pin_left = Td(pin.id, port=f"p{pin.index+1}l")
    cell_pin_label = Td(pin.label, delete_if_empty=True)
    cell_pin_color = Td(str(pin.color), delete_if_empty=True)
    cell_pin_right = Td(pin.id, port=f"p{pin.index+1}r")

    cells = [
        cell_pin_left if connector.ports_left else None,
        cell_pin_label,
        cell_pin_color,  # TODO: generate proper color mini-table too
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
        head = f"{connector.designator}:p{loop[0]}{loop_side}:{loop_dir}"
        tail = f"{connector.designator}:p{loop[1]}{loop_side}:{loop_dir}"
        loop_edges.append((head, tail))
    return loop_edges


def gv_conductor_table(cable) -> Table:
    rows = []
    rows.append(Tr(Td("&nbsp;")))  # spacer row on top

    inserted_break_inbetween = False
    for wire in cable.wire_objects:

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
            Td(", ".join(ins), align="left"),
            Td(":".join([wi for wi in wireinfo if wi is not None and wi != ""])),
            Td(", ".join(outs), align="right"),
        ]
        rows.append(Tr(cells_above))

        # the wire itself
        rows.append(Tr(gv_wire_cell(wire)))

        # row below the wire
        # TODO: PN stuff for bundles
        # wire_pn_stuff() see below

    rows.append(Tr(Td("&nbsp;")))  # spacer row on bottom
    tbl = Table(rows, border=0, cellborder=0, cellspacing=0)
    return tbl


def gv_wire_cell(wire: Union[WireClass, ShieldClass]) -> Td:
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
            "colspan": 3,
            "height": 2,
        }
        wire_inner_rows.append(Tr(Td("", **wire_inner_cell_attribs)))
    wire_inner_table = Table(wire_inner_rows, border=0, cellborder=0, cellspacing=0)
    wire_outer_cell_attribs = {
        "border": 0,
        "cellspacing": 0,
        "cellpadding": 0,
        "colspan": 3,
        "height": 2 * len(color_list),
        "port": f"w{wire.index+1}",
    }
    # ports in GraphViz are 1-indexed for more natural maping to pin/wire numbers
    wire_outer_cell = Td(wire_inner_table, **wire_outer_cell_attribs)

    return wire_outer_cell


def wire_pn_stuff():
    # # for bundles, individual wires can have part information
    # if cable.category == "bundle":
    #     # create a list of wire parameters
    #     wireidentification = []
    #     if isinstance(cable.pn, list):
    #         wireidentification.append(
    #             pn_info_string(
    #                 HEADER_PN, None, remove_links(cable.pn[i - 1])
    #             )
    #         )
    #     manufacturer_info = pn_info_string(
    #         HEADER_MPN,
    #         cable.manufacturer[i - 1]
    #         if isinstance(cable.manufacturer, list)
    #         else None,
    #         cable.mpn[i - 1] if isinstance(cable.mpn, list) else None,
    #     )
    #     supplier_info = pn_info_string(
    #         HEADER_SPN,
    #         cable.supplier[i - 1]
    #         if isinstance(cable.supplier, list)
    #         else None,
    #         cable.spn[i - 1] if isinstance(cable.spn, list) else None,
    #     )
    #     if manufacturer_info:
    #         wireidentification.append(html_line_breaks(manufacturer_info))
    #     if supplier_info:
    #         wireidentification.append(html_line_breaks(supplier_info))
    #     # print parameters into a table row under the wire
    #     if len(wireidentification) > 0:
    #         # fmt: off
    #         wirehtml.append('   <tr><td colspan="3">')
    #         wirehtml.append('    <table border="0" cellspacing="0" cellborder="0"><tr>')
    #         for attrib in wireidentification:
    #             wirehtml.append(f"     <td>{attrib}</td>")
    #         wirehtml.append("    </tr></table>")
    #         wirehtml.append("   </td></tr>")
    #         # fmt: on
    pass


def gv_edge_wire(harness, cable, connection) -> (str, str, str):
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


def gv_edge_mate(mate) -> (str, str, str, str):
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


def colored_cell(contents, bgcolor) -> Td:
    return Td(contents, bgcolor=bgcolor.html)


def colorbar_cell(color) -> Td:
    return Td("", bgcolor=color.html, width=4)


def image_and_caption_cells(component: Component) -> (Td, Td):
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
                        print(
                            "Harness.create_graph() warning: "
                            f"{attr} not found in {keyword}!"
                        )
                    elif n_subs > 1:
                        print(
                            "Harness.create_graph() warning: "
                            f"{attr} removed {n_subs} times in {keyword}!"
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
                        "Harness.create_graph() warning: "
                        f"{attr} overridden {n_subs} times in {keyword}!"
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
