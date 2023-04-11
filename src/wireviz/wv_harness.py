# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from graphviz import Graph

from wireviz import APP_NAME, APP_URL, __version__
import wireviz.wv_colors
from wireviz.wv_bom import bom_list
from wireviz.wv_dataclasses import (
    Arrow,
    ArrowWeight,
    BomCategory,
    Cable,
    Component,
    Connector,
    MateComponent,
    MatePin,
    Metadata,
    Options,
    Side,
)
from wireviz.wv_graphviz import (
    calculate_node_bgcolor,
    gv_connector_loops,
    gv_edge_mate,
    gv_edge_wire,
    gv_node_connector,
    gv_node_component,
    parse_arrow_str,
    set_dot_basics,
)
from wireviz.wv_output import (
    embed_svg_images_file,
    generate_html_output,
    generate_pdf_output,
)
from wireviz.wv_utils import bom2tsv
from wireviz.wv_templates import get_template


@dataclass
class Harness:
    metadata: Metadata
    options: Options
    additional_bom_items: List[Component] = field(default_factory=list)
    shared_bom: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.connectors = {}
        self.cables = {}
        self.mates = []
        self.bom = {}
        self.additional_bom_items = []

    @property
    def name(self) -> str:
        pn = self.metadata.get("pn", "")
        output_name = self.metadata["output_name"]
        if pn and pn not in output_name:
            return f"{pn}-{output_name}"
        else:
            return output_name

    def add_connector(self, designator: str, *args, **kwargs) -> None:
        conn = Connector(designator=designator, *args, **kwargs)
        self.connectors[designator] = conn

    def add_cable(self, designator: str, *args, **kwargs) -> None:
        cbl = Cable(designator=designator, *args, **kwargs)
        self.cables[designator] = cbl

    def add_additional_bom_item(self, item: dict) -> None:
        new_item = Component(**item, category=BomCategory.ADDITIONAL)
        self.additional_bom_items.append(new_item)

    def add_mate_pin(self, from_name, from_pin, to_name, to_pin, arrow_str) -> None:
        from_con = self.connectors[from_name]
        from_pin_obj = from_con.pin_objects[from_pin]
        to_con = self.connectors[to_name]
        to_pin_obj = to_con.pin_objects[to_pin]
        arrow = Arrow(direction=parse_arrow_str(arrow_str), weight=ArrowWeight.SINGLE)

        self.mates.append(MatePin(from_pin_obj, to_pin_obj, arrow))
        self.connectors[from_name].activate_pin(
            from_pin, Side.RIGHT, is_connection=False
        )
        self.connectors[to_name].activate_pin(to_pin, Side.LEFT, is_connection=False)

    def add_mate_component(self, from_name, to_name, arrow_str) -> None:
        arrow = Arrow(direction=parse_arrow_str(arrow_str), weight=ArrowWeight.SINGLE)
        self.mates.append(MateComponent(from_name, to_name, arrow))

    def populate_bom(self):
        # helper lists
        all_toplevel_items = (
            list(self.connectors.values())
            + list(self.cables.values())
            + self.additional_bom_items
        )
        all_subitems = [
            subitem
            for item in all_toplevel_items
            for subitem in item.additional_components
        ]
        all_bom_relevant_items = (
            list(self.connectors.values())
            + [cable for cable in self.cables.values() if cable.category != "bundle"]
            + [
                wire
                for cable in self.cables.values()
                if cable.category == "bundle"
                for wire in cable.wire_objects.values()
            ]
            + all_subitems
        )

        def add_to_bom(entry):
            if isinstance(entry, list):
                for e in entry:
                    add_to_bom(e)
                return

            if hash(entry) in self.bom:
                self.bom[hash(entry)] += entry
            else:
                self.bom[hash(entry)] = entry

            try:
                self.bom[hash(entry)]
            except KeyError:
                raise RuntimeError(
                    f"BomEntry's hash is not persitent: h1:{hash(entry)} h2:{hash(entry)}\n\tentry: {entry}\n\titem:{item}"
                )

        # add items to BOM
        for item in all_bom_relevant_items:
            if item.ignore_in_bom:
                continue
            add_to_bom(item.bom_entry)

        # sort BOM by category first, then alphabetically by description within category
        self.bom = dict(
            sorted(
                self.bom.items(),
                key=lambda x: (
                    x[1].category,
                    x[1].description,
                ),  # x[0] = key, x[1] = value
            )
        )

        next_id = len(self.shared_bom) + 1
        # TODO: for each harness, track a (harness_name, qty) pair
        def get_per_harness(v):
            d = {
                "qty": v["qty"],
            }
            return (self.name, d)

        for key, values in self.bom.items():
            if key in self.shared_bom:
                self.shared_bom[key]["qty"] += values["qty"]
                values["id"] = self.shared_bom[key]["id"]
            else:
                self.shared_bom[key] = values
                self.shared_bom[key]["id"] = next_id
                values["id"] = next_id
                next_id += 1

            k, v = get_per_harness(values)
            self.shared_bom[key].per_harness[k] = v

        # print(f'bom length: {len(self.bom)}, shared_bom length: {len(self.shared_bom)}') # for debugging

        # set BOM IDs within components (for BOM bubbles)
        for item in all_bom_relevant_items:
            if item.ignore_in_bom:
                continue
            if hash(item) not in self.bom:
                continue
            item.id = self.bom[hash(item)].id

        self.bom = dict(
            sorted(
                self.bom.items(),
                key=lambda x: (x[1].id,),
            )
        )
        # from wireviz.wv_bom import print_bom_table ; print_bom_table(self.bom)  # for debugging

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
        for (name, pin) in zip([from_name, to_name], [from_pin, to_pin]):
            if name is not None and name in self.connectors:
                connector = self.connectors[name]
                # check if provided name is ambiguous
                if pin in connector.pins and pin in connector.pinlabels:
                    if connector.pins.index(pin) != connector.pinlabels.index(pin):
                        raise Exception(
                            f"{name}:{pin} is defined both in pinlabels and pins, "
                            "for different pins."
                        )
                    # TODO: Maybe issue a warning if present in both lists
                    # but referencing the same pin?
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
                        f"{via_name}:{via_wire} is defined both in colors and wirelabels, "
                        "for different wires."
                    )
                # TODO: Maybe issue a warning if present in both lists
                # but referencing the same wire?
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
        if from_name is not None:
            from_con = self.connectors[from_name]
            from_pin_obj = from_con.pin_objects[from_pin]
        else:
            from_pin_obj = None
        if to_name is not None:
            to_con = self.connectors[to_name]
            to_pin_obj = to_con.pin_objects[to_pin]
        else:
            to_pin_obj = None

        self.cables[via_name]._connect(from_pin_obj, via_wire, to_pin_obj)
        if from_name in self.connectors:
            self.connectors[from_name].activate_pin(from_pin, Side.RIGHT)
        if to_name in self.connectors:
            self.connectors[to_name].activate_pin(to_pin, Side.LEFT)

    def create_graph(self) -> Graph:
        dot = Graph()
        set_dot_basics(dot, self.options)

        for connector in self.connectors.values():
            # generate connector node
            gv_html = gv_node_component(connector)
            gv_html.update_attribs(
                bgcolor=calculate_node_bgcolor(connector, self.options)
            )
            template_html = gv_node_connector(connector)
            #print(gv_html)
            #import pdb; pdb.set_trace()
            dot.node(
                connector.designator,
                label=f"<\n{template_html}\n>",
                shape="box",
                style="filled",
            )
            # generate edges for connector loops
            if len(connector.loops) > 0:
                dot.attr("edge", color="#000000")
                loops = gv_connector_loops(connector)
                for head, tail in loops:
                    dot.edge(head, tail)

        # determine if there are double- or triple-colored wires in the harness;
        # if so, pad single-color wires to make all wires of equal thickness
        wire_is_multicolor = [
            len(wire.color) > 1
            for cable in self.cables.values()
            for wire in cable.wire_objects.values()
        ]
        if any(wire_is_multicolor):
            wireviz.wv_colors.padding_amount = 3
        else:
            wireviz.wv_colors.padding_amount = 1

        for cable in self.cables.values():
            # generate cable node
            # TODO: PN info for bundles (per wire)
            gv_html = gv_node_component(cable)
            gv_html.update_attribs(bgcolor=calculate_node_bgcolor(cable, self.options))
            style = "filled,dashed" if cable.category == "bundle" else "filled"
            dot.node(
                cable.designator,
                label=f"<\n{gv_html}\n>",
                shape="box",
                style=style,
            )

            # generate wire edges between component nodes and cable nodes
            for connection in cable._connections:
                color, l1, l2, r1, r2 = gv_edge_wire(self, cable, connection)
                dot.attr("edge", color=color)
                if not (l1, l2) == (None, None):
                    dot.edge(l1, l2)
                if not (r1, r2) == (None, None):
                    dot.edge(r1, r2)

        for mate in self.mates:
            color, dir, code_from, code_to = gv_edge_mate(mate)

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

        rendered = set()
        for f in fmt:
            if f in ("png", "svg", "html"):
                if f == "html":  # if HTML format is specified,
                    f = "svg"  # generate SVG for embedding into HTML
                # SVG file will be renamed/deleted later
                if f in rendered:
                    continue
                graph.format = f
                graph.render(filename=filename, view=view, cleanup=cleanup)
                rendered.add(f)
        # embed images into SVG output
        if "svg" in fmt or "html" in fmt:
            embed_svg_images_file(filename.with_suffix(".svg"))
        # GraphViz output
        if "gv" in fmt:
            graph.save(filename=filename.with_suffix(".gv"))
        # BOM output
        if "tsv" in fmt:
            bomlist = bom_list(self.bom, restrict_printed_lengths=False)
            bom_tsv = bom2tsv(bomlist)
            filename.with_suffix(".tsv").open("w").write(bom_tsv)
        if "csv" in fmt:
            # TODO: implement CSV output (preferrably using CSV library)
            print("CSV output is not yet supported")
        # HTML output
        if "html" in fmt:
            bomlist = bom_list(self.bom, filter_entries=True)
            generate_html_output(filename, bomlist, self.metadata, self.options)
        # PDF output
        if "pdf" in fmt:
            generate_pdf_output(filename)
        # delete SVG if not needed
        if "html" in fmt and not "svg" in fmt:
            # SVG file was just needed to generate HTML
            filename.with_suffix(".svg").unlink()
