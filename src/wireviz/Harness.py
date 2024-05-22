# -*- coding: utf-8 -*-

import re
from collections import Counter
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Any, List, Union

from graphviz import Graph

from wireviz import APP_NAME, APP_URL, __version__, wv_colors
from wireviz.DataClasses import (
    Cable,
    Connector,
    MateComponent,
    MatePin,
    Metadata,
    Options,
    Tweak,
    Side,
)
from wireviz.svgembed import embed_svg_images_file
from wireviz.wv_bom import (
    HEADER_MPN,
    HEADER_PN,
    HEADER_SPN,
    bom_list,
    component_table_entry,
    generate_bom,
    get_additional_component_table,
    pn_info_string,
)
from wireviz.wv_colors import get_color_hex, translate_color
from wireviz.wv_gv_html import (
    html_bgcolor,
    html_bgcolor_attr,
    html_caption,
    html_colorbar,
    html_image,
    html_line_breaks,
    nested_html_table,
    remove_links,
)
from wireviz.wv_helper import (
    awg_equiv,
    flatten2d,
    is_arrow,
    mm2_equiv,
    open_file_read,
    open_file_write,
    tuplelist2tsv,
)
from wireviz.wv_html import generate_html_output

OLD_CONNECTOR_ATTR = {
    "pinout": "was renamed to 'pinlabels' in v0.2",
    "pinnumbers": "was renamed to 'pins' in v0.2",
    "autogenerate": "is replaced with new syntax in v0.4",
}

def check_old(node: str, old_attr: dict, args: dict) -> None:
    """Raise exception for any outdated attributes in args."""
    for attr, descr in old_attr.items():
        if attr in args:
            raise ValueError(f"'{attr}' in {node}: '{attr}' {descr}")

@dataclass
class Harness:
    metadata: Metadata
    options: Options
    tweak: Tweak

    def __post_init__(self):
        self.connectors = {}
        self.cables = {}
        self.mates = []
        self._bom = []  # Internal Cache for generated bom
        self.additional_bom_items = []

    def add_connector(self, name: str, *args, **kwargs) -> None:
        check_old(f"Connector '{name}'", OLD_CONNECTOR_ATTR, kwargs)
        self.connectors[name] = Connector(name, *args, **kwargs)

    def add_cable(self, name: str, *args, **kwargs) -> None:
        self.cables[name] = Cable(name, *args, **kwargs)

    def add_mate_pin(self, from_name, from_pin, to_name, to_pin, arrow_type) -> None:
        self.mates.append(MatePin(from_name, from_pin, to_name, to_pin, arrow_type))
        self.connectors[from_name].activate_pin(from_pin, Side.RIGHT)
        self.connectors[to_name].activate_pin(to_pin, Side.LEFT)

    def add_mate_component(self, from_name, to_name, arrow_type) -> None:
        self.mates.append(MateComponent(from_name, to_name, arrow_type))

    def add_bom_item(self, item: dict) -> None:
        self.additional_bom_items.append(item)

    def connect(
        self,
        from_name: str,
        from_pin: (int, str),
        via_name: str,
        via_wire: (int, str),
        to_name: str,
        to_pin: (int, str),
    ) -> None:
        # check from and to connectors
        for name, pin in zip([from_name, to_name], [from_pin, to_pin]):
            if name is not None and name in self.connectors:
                connector = self.connectors[name]
                # check if provided name is ambiguous
                if pin in connector.pins and pin in connector.pinlabels:
                    if connector.pins.index(pin) != connector.pinlabels.index(pin):
                        raise Exception(
                            f"{name}:{pin} is defined both in pinlabels and pins, for different pins."
                        )
                    # TODO: Maybe issue a warning if present in both lists but referencing the same pin?
                if pin in connector.pinlabels:
                    if connector.pinlabels.count(pin) > 1:
                        raise Exception(f"{name}:{pin} is defined more than once.")
                    index = connector.pinlabels.index(pin)
                    pin = connector.pins[index]  # map pin name to pin number
                    if name == from_name:
                        from_pin = pin
                    if name == to_name:
                        to_pin = pin
                if not pin in connector.pins:
                    raise Exception(f"{name}:{pin} not found.")

        # check via cable
        if via_name in self.cables:
            cable = self.cables[via_name]
            # check if provided name is ambiguous
            if via_wire in cable.colors and via_wire in cable.wirelabels:
                if cable.colors.index(via_wire) != cable.wirelabels.index(via_wire):
                    raise Exception(
                        f"{via_name}:{via_wire} is defined both in colors and wirelabels, for different wires."
                    )
                # TODO: Maybe issue a warning if present in both lists but referencing the same wire?
            if via_wire in cable.colors:
                if cable.colors.count(via_wire) > 1:
                    raise Exception(
                        f"{via_name}:{via_wire} is used for more than one wire."
                    )
                # list index starts at 0, wire IDs start at 1
                via_wire = cable.colors.index(via_wire) + 1
            elif via_wire in cable.wirelabels:
                if cable.wirelabels.count(via_wire) > 1:
                    raise Exception(
                        f"{via_name}:{via_wire} is used for more than one wire."
                    )
                via_wire = (
                    cable.wirelabels.index(via_wire) + 1
                )  # list index starts at 0, wire IDs start at 1

        # perform the actual connection
        self.cables[via_name].connect(from_name, from_pin, via_wire, to_name, to_pin)
        if from_name in self.connectors:
            self.connectors[from_name].activate_pin(from_pin, Side.RIGHT)
        if to_name in self.connectors:
            self.connectors[to_name].activate_pin(to_pin, Side.LEFT)

    def create_graph(self) -> Graph:
        dot = Graph()
        dot.body.append(f"// Graph generated by {APP_NAME} {__version__}\n")
        dot.body.append(f"// {APP_URL}\n")
        dot.attr(
            "graph",
            rankdir="LR",
            ranksep="2",
            bgcolor=wv_colors.translate_color(self.options.bgcolor, "HEX"),
            nodesep="0.33",
            fontname=self.options.fontname,
        )
        dot.attr(
            "node",
            shape="none",
            width="0",
            height="0",
            margin="0",  # Actual size of the node is entirely determined by the label.
            style="filled",
            fillcolor=wv_colors.translate_color(self.options.bgcolor_node, "HEX"),
            fontname=self.options.fontname,
        )
        dot.attr("edge", style="bold", fontname=self.options.fontname)

        for connector in self.connectors.values():

            # If no wires connected (except maybe loop wires)?
            if not (connector.ports_left or connector.ports_right):
                connector.ports_left = True  # Use left side pins.

            html = []
            # fmt: off
            rows = [[f'{html_bgcolor(connector.bgcolor_title)}{remove_links(connector.name)}'
                        if connector.show_name else None],
                    [pn_info_string(HEADER_PN, None, remove_links(connector.pn)),
                     html_line_breaks(pn_info_string(HEADER_MPN, connector.manufacturer, connector.mpn)),
                     html_line_breaks(pn_info_string(HEADER_SPN, connector.supplier, connector.spn))],
                    [html_line_breaks(connector.type),
                     html_line_breaks(connector.subtype),
                     f'{connector.pincount}-pin' if connector.show_pincount else None,
                     translate_color(connector.color, self.options.color_mode) if connector.color else None,
                     html_colorbar(connector.color)],
                    '<!-- connector table -->' if connector.style != 'simple' else None,
                    [html_image(connector.image)],
                    [html_caption(connector.image)]]
            # fmt: on

            rows.extend(get_additional_component_table(self, connector))
            rows.append([html_line_breaks(connector.notes)])
            html.extend(nested_html_table(rows, html_bgcolor_attr(connector.bgcolor)))

            if connector.style != "simple":
                pinhtml = []
                pinhtml.append(
                    '<table border="0" cellspacing="0" cellpadding="3" cellborder="1">'
                )

                for pinindex, (pinname, pinlabel, pincolor) in enumerate(
                    zip_longest(
                        connector.pins, connector.pinlabels, connector.pincolors
                    )
                ):
                    if (
                        connector.hide_disconnected_pins
                        and not connector.visible_pins.get(pinname, False)
                    ):
                        continue

                    pinhtml.append("   <tr>")
                    if connector.ports_left:
                        pinhtml.append(f'    <td port="p{pinindex+1}l">{pinname}</td>')
                    if pinlabel:
                        pinhtml.append(f"    <td>{pinlabel}</td>")
                    if connector.pincolors:
                        if pincolor in wv_colors._color_hex.keys():
                            # fmt: off
                            pinhtml.append(f'    <td sides="tbl">{translate_color(pincolor, self.options.color_mode)}</td>')
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

                pinhtml.append("  </table>")

                html = [
                    row.replace("<!-- connector table -->", "\n".join(pinhtml))
                    for row in html
                ]

            html = "\n".join(html)
            dot.node(
                connector.name,
                label=f"<\n{html}\n>",
                shape="box",
                style="filled",
                fillcolor=translate_color(self.options.bgcolor_connector, "HEX"),
            )

            if len(connector.loops) > 0:
                dot.attr("edge", color="#000000:#ffffff:#000000")
                if connector.ports_left:
                    loop_side = "l"
                    loop_dir = "w"
                elif connector.ports_right:
                    loop_side = "r"
                    loop_dir = "e"
                else:
                    raise Exception("No side for loops")
                for loop in connector.loops:
                    dot.edge(
                        f"{connector.name}:p{loop[0]}{loop_side}:{loop_dir}",
                        f"{connector.name}:p{loop[1]}{loop_side}:{loop_dir}",
                    )

        # determine if there are double- or triple-colored wires in the harness;
        # if so, pad single-color wires to make all wires of equal thickness
        pad = any(
            len(colorstr) > 2
            for cable in self.cables.values()
            for colorstr in cable.colors
        )

        for cable in self.cables.values():

            html = []

            awg_fmt = ""
            if cable.show_equiv:
                # Only convert units we actually know about, i.e. currently
                # mm2 and awg --- other units _are_ technically allowed,
                # and passed through as-is.
                if cable.gauge_unit == "mm\u00B2":
                    awg_fmt = f" ({awg_equiv(cable.gauge)} AWG)"
                elif cable.gauge_unit.upper() == "AWG":
                    awg_fmt = f" ({mm2_equiv(cable.gauge)} mm\u00B2)"

            # fmt: off
            rows = [[f'{html_bgcolor(cable.bgcolor_title)}{remove_links(cable.name)}'
                        if cable.show_name else None],
                    [pn_info_string(HEADER_PN, None,
                        remove_links(cable.pn)) if not isinstance(cable.pn, list) else None,
                     html_line_breaks(pn_info_string(HEADER_MPN,
                        cable.manufacturer if not isinstance(cable.manufacturer, list) else None,
                        cable.mpn if not isinstance(cable.mpn, list) else None)),
                     html_line_breaks(pn_info_string(HEADER_SPN,
                        cable.supplier if not isinstance(cable.supplier, list) else None,
                        cable.spn if not isinstance(cable.spn, list) else None))],
                    [html_line_breaks(cable.type),
                     f'{cable.wirecount}x' if cable.show_wirecount else None,
                     f'{cable.gauge} {cable.gauge_unit}{awg_fmt}' if cable.gauge else None,
                     '+ S' if cable.shield else None,
                     f'{cable.length} {cable.length_unit}' if cable.length > 0 else None,
                     translate_color(cable.color, self.options.color_mode) if cable.color else None,
                     html_colorbar(cable.color)],
                    '<!-- wire table -->',
                    [html_image(cable.image)],
                    [html_caption(cable.image)]]
            # fmt: on

            rows.extend(get_additional_component_table(self, cable))
            rows.append([html_line_breaks(cable.notes)])
            html.extend(nested_html_table(rows, html_bgcolor_attr(cable.bgcolor)))

            wirehtml = []
            # conductor table
            wirehtml.append('<table border="0" cellspacing="0" cellborder="0">')
            wirehtml.append("   <tr><td>&nbsp;</td></tr>")

            for i, (connection_color, wirelabel) in enumerate(
                zip_longest(cable.colors, cable.wirelabels), 1
            ):
                wirehtml.append("   <tr>")
                wirehtml.append(f"    <td><!-- {i}_in --></td>")
                wirehtml.append(f"    <td>")

                wireinfo = []
                if cable.show_wirenumbers:
                    wireinfo.append(str(i))
                colorstr = wv_colors.translate_color(
                    connection_color, self.options.color_mode
                )
                if colorstr:
                    wireinfo.append(colorstr)
                if cable.wirelabels:
                    wireinfo.append(wirelabel if wirelabel is not None else "")
                wirehtml.append(f'     {":".join(wireinfo)}')

                wirehtml.append(f"    </td>")
                wirehtml.append(f"    <td><!-- {i}_out --></td>")
                wirehtml.append("   </tr>")

                # fmt: off
                bgcolors = ['#000000'] + get_color_hex(connection_color, pad=pad) + ['#000000']
                wirehtml.append(f"   <tr>")
                wirehtml.append(f'    <td colspan="3" border="0" cellspacing="0" cellpadding="0" port="w{i}" height="{(2 * len(bgcolors))}">')
                wirehtml.append('     <table cellspacing="0" cellborder="0" border="0">')
                for j, bgcolor in enumerate(bgcolors[::-1]):  # Reverse to match the curved wires when more than 2 colors
                    wirehtml.append(f'      <tr><td colspan="3" cellpadding="0" height="2" bgcolor="{bgcolor if bgcolor != "" else wv_colors.default_color}" border="0"></td></tr>')
                wirehtml.append("     </table>")
                wirehtml.append("    </td>")
                wirehtml.append("   </tr>")
                # fmt: on

                # for bundles, individual wires can have part information
                if cable.category == "bundle":
                    # create a list of wire parameters
                    wireidentification = []
                    if isinstance(cable.pn, list):
                        wireidentification.append(
                            pn_info_string(
                                HEADER_PN, None, remove_links(cable.pn[i - 1])
                            )
                        )
                    manufacturer_info = pn_info_string(
                        HEADER_MPN,
                        (
                            cable.manufacturer[i - 1]
                            if isinstance(cable.manufacturer, list)
                            else None
                        ),
                        cable.mpn[i - 1] if isinstance(cable.mpn, list) else None,
                    )
                    supplier_info = pn_info_string(
                        HEADER_SPN,
                        (
                            cable.supplier[i - 1]
                            if isinstance(cable.supplier, list)
                            else None
                        ),
                        cable.spn[i - 1] if isinstance(cable.spn, list) else None,
                    )
                    if manufacturer_info:
                        wireidentification.append(html_line_breaks(manufacturer_info))
                    if supplier_info:
                        wireidentification.append(html_line_breaks(supplier_info))
                    # print parameters into a table row under the wire
                    if len(wireidentification) > 0:
                        # fmt: off
                        wirehtml.append('   <tr><td colspan="3">')
                        wirehtml.append('    <table border="0" cellspacing="0" cellborder="0"><tr>')
                        for attrib in wireidentification:
                            wirehtml.append(f"     <td>{attrib}</td>")
                        wirehtml.append("    </tr></table>")
                        wirehtml.append("   </td></tr>")
                        # fmt: on

            if cable.shield:
                wirehtml.append("   <tr><td>&nbsp;</td></tr>")  # spacer
                wirehtml.append("   <tr>")
                wirehtml.append("    <td><!-- s_in --></td>")
                wirehtml.append("    <td>Shield</td>")
                wirehtml.append("    <td><!-- s_out --></td>")
                wirehtml.append("   </tr>")
                if isinstance(cable.shield, str):
                    # shield is shown with specified color and black borders
                    shield_color_hex = wv_colors.get_color_hex(cable.shield)[0]
                    attributes = (
                        f'height="6" bgcolor="{shield_color_hex}" border="2" sides="tb"'
                    )
                else:
                    # shield is shown as a thin black wire
                    attributes = f'height="2" bgcolor="#000000" border="0"'
                # fmt: off
                wirehtml.append(f'   <tr><td colspan="3" cellpadding="0" {attributes} port="ws"></td></tr>')
                # fmt: on

            wirehtml.append("   <tr><td>&nbsp;</td></tr>")
            wirehtml.append("  </table>")

            html = [
                row.replace("<!-- wire table -->", "\n".join(wirehtml)) for row in html
            ]

            # connections
            for connection in cable.connections:
                if isinstance(connection.via_port, int):
                    # check if it's an actual wire and not a shield
                    dot.attr(
                        "edge",
                        color=":".join(
                            ["#000000"]
                            + wv_colors.get_color_hex(
                                cable.colors[connection.via_port - 1], pad=pad
                            )
                            + ["#000000"]
                        ),
                    )
                else:  # it's a shield connection
                    # shield is shown with specified color and black borders, or as a thin black wire otherwise
                    dot.attr(
                        "edge",
                        color=(
                            ":".join(["#000000", shield_color_hex, "#000000"])
                            if isinstance(cable.shield, str)
                            else "#000000"
                        ),
                    )
                if connection.from_pin is not None:  # connect to left
                    from_connector = self.connectors[connection.from_name]
                    from_pin_index = from_connector.pins.index(connection.from_pin)
                    from_port_str = (
                        f":p{from_pin_index+1}r"
                        if from_connector.style != "simple"
                        else ""
                    )
                    code_left_1 = f"{connection.from_name}{from_port_str}:e"
                    code_left_2 = f"{cable.name}:w{connection.via_port}:w"
                    dot.edge(code_left_1, code_left_2)
                    if from_connector.show_name:
                        from_info = [
                            str(connection.from_name),
                            str(connection.from_pin),
                        ]
                        if from_connector.pinlabels:
                            pinlabel = from_connector.pinlabels[from_pin_index]
                            if pinlabel != "":
                                from_info.append(pinlabel)
                        from_string = ":".join(from_info)
                    else:
                        from_string = ""
                    html = [
                        row.replace(f"<!-- {connection.via_port}_in -->", from_string)
                        for row in html
                    ]
                if connection.to_pin is not None:  # connect to right
                    to_connector = self.connectors[connection.to_name]
                    to_pin_index = to_connector.pins.index(connection.to_pin)
                    to_port_str = (
                        f":p{to_pin_index+1}l" if to_connector.style != "simple" else ""
                    )
                    code_right_1 = f"{cable.name}:w{connection.via_port}:e"
                    code_right_2 = f"{connection.to_name}{to_port_str}:w"
                    dot.edge(code_right_1, code_right_2)
                    if to_connector.show_name:
                        to_info = [str(connection.to_name), str(connection.to_pin)]
                        if to_connector.pinlabels:
                            pinlabel = to_connector.pinlabels[to_pin_index]
                            if pinlabel != "":
                                to_info.append(pinlabel)
                        to_string = ":".join(to_info)
                    else:
                        to_string = ""
                    html = [
                        row.replace(f"<!-- {connection.via_port}_out -->", to_string)
                        for row in html
                    ]

            style, bgcolor = (
                ("filled,dashed", self.options.bgcolor_bundle)
                if cable.category == "bundle"
                else ("filled", self.options.bgcolor_cable)
            )
            html = "\n".join(html)
            dot.node(
                cable.name,
                label=f"<\n{html}\n>",
                shape="box",
                style=style,
                fillcolor=translate_color(bgcolor, "HEX"),
            )

        def typecheck(name: str, value: Any, expect: type) -> None:
            if not isinstance(value, expect):
                raise Exception(
                    f"Unexpected value type of {name}: Expected {expect}, got {type(value)}\n{value}"
                )

        # TODO?: Differ between override attributes and HTML?
        if self.tweak.override is not None:
            typecheck("tweak.override", self.tweak.override, dict)
            for k, d in self.tweak.override.items():
                typecheck(f"tweak.override.{k} key", k, str)
                typecheck(f"tweak.override.{k} value", d, dict)
                for a, v in d.items():
                    typecheck(f"tweak.override.{k}.{a} key", a, str)
                    typecheck(f"tweak.override.{k}.{a} value", v, (str, type(None)))

            # Override generated attributes of selected entries matching tweak.override.
            for i, entry in enumerate(dot.body):
                if isinstance(entry, str):
                    # Find a possibly quoted keyword after leading TAB(s) and followed by [ ].
                    match = re.match(
                        r'^\t*(")?((?(1)[^"]|[^ "])+)(?(1)") \[.*\]$', entry, re.S
                    )
                    keyword = match and match[2]
                    if keyword in self.tweak.override.keys():
                        for attr, value in self.tweak.override[keyword].items():
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

        if self.tweak.append is not None:
            if isinstance(self.tweak.append, list):
                for i, element in enumerate(self.tweak.append, 1):
                    typecheck(f"tweak.append[{i}]", element, str)
                dot.body.extend(self.tweak.append)
            else:
                typecheck("tweak.append", self.tweak.append, str)
                dot.body.append(self.tweak.append)

        # TODO: All code below until "return dot" must be moved above all tweak processing!
        for mate in self.mates:
            if mate.shape[0] == "<" and mate.shape[-1] == ">":
                dir = "both"
            elif mate.shape[0] == "<":
                dir = "back"
            elif mate.shape[-1] == ">":
                dir = "forward"
            else:
                dir = "none"

            if isinstance(mate, MatePin):
                color = "#000000"
            elif isinstance(mate, MateComponent):
                color = "#000000:#000000"
            else:
                raise Exception(f"{mate} is an unknown mate")

            from_connector = self.connectors[mate.from_name]
            to_connector = self.connectors[mate.to_name]
            if isinstance(mate, MatePin) and from_connector.style != "simple":
                from_pin_index = from_connector.pins.index(mate.from_pin)
                from_port_str = f":p{from_pin_index+1}r"
            else:  # MateComponent or style == 'simple'
                from_port_str = ""
            if isinstance(mate, MatePin) and to_connector.style != "simple":
                to_pin_index = to_connector.pins.index(mate.to_pin)
                to_port_str = f":p{to_pin_index+1}l"
            else:  # MateComponent or style == 'simple'
                to_port_str = ""
            code_from = f"{mate.from_name}{from_port_str}:e"
            code_to = f"{mate.to_name}{to_port_str}:w"

            dot.attr("edge", color=color, style="dashed", dir=dir)
            dot.edge(code_from, code_to)

        return dot

    # cache for the GraphViz Graph object
    # do not access directly, use self.graph instead
    _graph = None

    @property
    def graph(self):
        if not self._graph:  # no cached graph exists, generate one
            self._graph = self.create_graph()
        return self._graph  # return cached graph

    @property
    def png(self):
        from io import BytesIO

        graph = self.graph
        data = BytesIO()
        data.write(graph.pipe(format="png"))
        data.seek(0)
        return data.read()

    @property
    def svg(self):
        graph = self.graph
        return embed_svg_images(graph.pipe(format="svg").decode("utf-8"), Path.cwd())

    def output(
        self,
        filename: (str, Path),
        view: bool = False,
        cleanup: bool = True,
        fmt: tuple = ("html", "png", "svg", "tsv"),
    ) -> None:
        # graphical output
        graph = self.graph
        svg_already_exists = Path(
            f"{filename}.svg"
        ).exists()  # if SVG already exists, do not delete later
        # graphical output
        for f in fmt:
            if f in ("png", "svg", "html"):
                if f == "html":  # if HTML format is specified,
                    f = "svg"  # generate SVG for embedding into HTML
                # SVG file will be renamed/deleted later
                _filename = f"{filename}.tmp" if f == "svg" else filename
                # TODO: prevent rendering SVG twice when both SVG and HTML are specified
                graph.format = f
                graph.render(filename=_filename, view=view, cleanup=cleanup)
        # embed images into SVG output
        if "svg" in fmt or "html" in fmt:
            embed_svg_images_file(f"{filename}.tmp.svg")
        # GraphViz output
        if "gv" in fmt:
            graph.save(filename=f"{filename}.gv")
        # BOM output
        bomlist = bom_list(self.bom())
        if "tsv" in fmt:
            open_file_write(f"{filename}.bom.tsv").write(tuplelist2tsv(bomlist))
        if "csv" in fmt:
            # TODO: implement CSV output (preferrably using CSV library)
            print("CSV output is not yet supported")
        # HTML output
        if "html" in fmt:
            generate_html_output(filename, bomlist, self.metadata, self.options)
        # PDF output
        if "pdf" in fmt:
            # TODO: implement PDF output
            print("PDF output is not yet supported")
        # delete SVG if not needed
        if "html" in fmt and not "svg" in fmt:
            # SVG file was just needed to generate HTML
            Path(f"{filename}.tmp.svg").unlink()
        elif "svg" in fmt:
            Path(f"{filename}.tmp.svg").replace(f"{filename}.svg")

    def bom(self):
        if not self._bom:
            self._bom = generate_bom(self)
        return self._bom
