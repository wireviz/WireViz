# -*- coding: utf-8 -*-

from dataclasses import InitVar, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from wireviz.wv_colors import COLOR_CODES, Color, ColorMode, Colors, ColorScheme
from wireviz.wv_helper import aspect_ratio, int2tuple

# Each type alias have their legal values described in comments - validation might be implemented in the future
PlainText = str  # Text not containing HTML tags nor newlines
Hypertext = str  # Text possibly including HTML hyperlinks that are removed in all outputs except HTML output
MultilineHypertext = (
    str  # Hypertext possibly also including newlines to break lines in diagram output
)

Designator = PlainText  # Case insensitive unique name of connector or cable

# Literal type aliases below are commented to avoid requiring python 3.8
ConnectorMultiplier = PlainText  # = Literal['pincount', 'populated', 'unpopulated']
CableMultiplier = (
    PlainText  # = Literal['wirecount', 'terminations', 'length', 'total_length']
)
ImageScale = PlainText  # = Literal['false', 'true', 'width', 'height', 'both']

# Type combinations
Pin = Union[int, PlainText]  # Pin identifier
PinIndex = int  # Zero-based pin index
Wire = Union[int, PlainText]  # Wire number or Literal['s'] for shield
NoneOrMorePins = Union[
    Pin, Tuple[Pin, ...], None
]  # None, one, or a tuple of pin identifiers
NoneOrMorePinIndices = Union[
    PinIndex, Tuple[PinIndex, ...], None
]  # None, one, or a tuple of zero-based pin indices
OneOrMoreWires = Union[Wire, Tuple[Wire, ...]]  # One or a tuple of wires

# Metadata can contain whatever is needed by the HTML generation/template.
MetadataKeys = PlainText  # Literal['title', 'description', 'notes', ...]


Side = Enum("Side", "LEFT RIGHT")


class Metadata(dict):
    pass


@dataclass
class Options:
    fontname: PlainText = "arial"
    bgcolor: Color = "WH"
    bgcolor_node: Optional[Color] = "WH"
    bgcolor_connector: Optional[Color] = None
    bgcolor_cable: Optional[Color] = None
    bgcolor_bundle: Optional[Color] = None
    color_mode: ColorMode = "SHORT"
    mini_bom_mode: bool = True
    template_separator: str = "."

    def __post_init__(self):
        if not self.bgcolor_node:
            self.bgcolor_node = self.bgcolor
        if not self.bgcolor_connector:
            self.bgcolor_connector = self.bgcolor_node
        if not self.bgcolor_cable:
            self.bgcolor_cable = self.bgcolor_node
        if not self.bgcolor_bundle:
            self.bgcolor_bundle = self.bgcolor_cable


@dataclass
class Tweak:
    override: Optional[Dict[Designator, Dict[str, Optional[str]]]] = None
    append: Union[str, List[str], None] = None


@dataclass
class Image:
    # Attributes of the image object <img>:
    src: str
    scale: Optional[ImageScale] = None
    # Attributes of the image cell <td> containing the image:
    width: Optional[int] = None
    height: Optional[int] = None
    fixedsize: Optional[bool] = None
    bgcolor: Optional[Color] = None
    # Contents of the text cell <td> just below the image cell:
    caption: Optional[MultilineHypertext] = None
    # See also HTML doc at https://graphviz.org/doc/info/shapes.html#html

    def __post_init__(self):
        if self.fixedsize is None:
            # Default True if any dimension specified unless self.scale also is specified.
            self.fixedsize = (self.width or self.height) and self.scale is None

        if self.scale is None:
            if not self.width and not self.height:
                self.scale = "false"
            elif self.width and self.height:
                self.scale = "both"
            else:
                self.scale = "true"  # When only one dimension is specified.

        if self.fixedsize:
            # If only one dimension is specified, compute the other
            # because Graphviz requires both when fixedsize=True.
            if self.height:
                if not self.width:
                    self.width = self.height * aspect_ratio(self.src)
            else:
                if self.width:
                    self.height = self.width / aspect_ratio(self.src)

    @classmethod
    def create(cls, input: Union[None, dict, str, List[Union[dict, str]]]):
        """Create class instance(s) from alternative YAML input types"""
        if input in (None, "", []):
            return None
        if isinstance(input, list):
            return [cls.create(entry) for entry in input]
        if isinstance(input, str):
            input = {"src": input}
        if isinstance(input, dict):
            return cls(**input)
        raise TypeError(
            f"Expected None, dict, str, or list as Image input, but got {type(input)}"
        )


@dataclass
class AdditionalComponent:
    type: MultilineHypertext
    subtype: Optional[MultilineHypertext] = None
    manufacturer: Optional[MultilineHypertext] = None
    mpn: Optional[MultilineHypertext] = None
    supplier: Optional[MultilineHypertext] = None
    spn: Optional[MultilineHypertext] = None
    pn: Optional[Hypertext] = None
    qty: float = 1
    unit: Optional[str] = None
    qty_multiplier: Union[ConnectorMultiplier, CableMultiplier, None] = None
    bgcolor: Optional[Color] = None

    @property
    def description(self) -> str:
        t = self.type.rstrip()
        st = f", {self.subtype.rstrip()}" if self.subtype else ""
        t = t + st
        return t


@dataclass
class Connector:
    name: Designator
    bgcolor: Optional[Color] = None
    bgcolor_title: Optional[Color] = None
    manufacturer: Optional[MultilineHypertext] = None
    mpn: Optional[MultilineHypertext] = None
    supplier: Optional[MultilineHypertext] = None
    spn: Optional[MultilineHypertext] = None
    pn: Optional[Hypertext] = None
    style: Optional[str] = None
    category: Optional[str] = None
    type: Optional[MultilineHypertext] = None
    subtype: Optional[MultilineHypertext] = None
    pincount: Optional[int] = None
    image: Optional[Image] = None
    notes: Optional[MultilineHypertext] = None
    pins: List[Pin] = field(default_factory=list)
    pinlabels: List[Pin] = field(default_factory=list)
    pincolors: List[Color] = field(default_factory=list)
    color: Optional[Color] = None
    show_name: Optional[bool] = None
    show_pincount: Optional[bool] = None
    hide_disconnected_pins: bool = False
    loops: List[List[Pin]] = field(default_factory=list)
    ignore_in_bom: bool = False
    additional_components: List[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.image = Image.create(self.image)

        self.ports_left = False
        self.ports_right = False
        self.visible_pins = {}

        if self.style == "simple":
            if self.pincount and self.pincount > 1:
                raise Exception(
                    "Connectors with style set to simple may only have one pin"
                )
            self.pincount = 1

        if not self.pincount:
            self.pincount = max(
                len(self.pins), len(self.pinlabels), len(self.pincolors)
            )
            if not self.pincount:
                raise Exception(
                    "You need to specify at least one, pincount, pins, pinlabels, or pincolors"
                )

        # create default list for pins (sequential) if not specified
        if not self.pins:
            self.pins = list(range(1, self.pincount + 1))

        if len(self.pins) != len(set(self.pins)):
            raise Exception("Pins are not unique")

        if self.show_name is None:
            # hide designators for simple and for auto-generated connectors by default
            self.show_name = self.style != "simple" and self.name[0:2] != "__"

        if self.show_pincount is None:
            # hide pincount for simple (1 pin) connectors by default
            self.show_pincount = self.style != "simple"

        for loop in self.loops:
            # TODO: allow using pin labels in addition to pin numbers, just like when defining regular connections
            # TODO: include properties of wire used to create the loop
            if len(loop) != 2:
                raise Exception("Loops must be between exactly two pins!")
            for pin in loop:
                if pin not in self.pins:
                    raise Exception(
                        f'Unknown loop pin "{pin}" for connector "{self.name}"!'
                    )
                # Make sure loop connected pins are not hidden.
                self.activate_pin(pin, None)

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    def activate_pin(self, pin: Pin, side: Side) -> None:
        self.visible_pins[pin] = True
        if side == Side.LEFT:
            self.ports_left = True
        elif side == Side.RIGHT:
            self.ports_right = True

    def get_qty_multiplier(self, qty_multiplier: Optional[ConnectorMultiplier]) -> int:
        if not qty_multiplier:
            return 1
        elif qty_multiplier == "pincount":
            return self.pincount
        elif qty_multiplier == "populated":
            return sum(self.visible_pins.values())
        elif qty_multiplier == "unpopulated":
            return max(0, self.pincount - sum(self.visible_pins.values()))
        else:
            raise ValueError(
                f"invalid qty multiplier parameter for connector {qty_multiplier}"
            )


@dataclass
class Cable:
    name: Designator
    bgcolor: Optional[Color] = None
    bgcolor_title: Optional[Color] = None
    manufacturer: Union[MultilineHypertext, List[MultilineHypertext], None] = None
    mpn: Union[MultilineHypertext, List[MultilineHypertext], None] = None
    supplier: Union[MultilineHypertext, List[MultilineHypertext], None] = None
    spn: Union[MultilineHypertext, List[MultilineHypertext], None] = None
    pn: Union[Hypertext, List[Hypertext], None] = None
    category: Optional[str] = None
    type: Optional[MultilineHypertext] = None
    gauge: Optional[float] = None
    gauge_unit: Optional[str] = None
    show_equiv: bool = False
    length: float = 0
    length_unit: Optional[str] = None
    color: Optional[Color] = None
    wirecount: Optional[int] = None
    shield: Union[bool, Color] = False
    image: Optional[Image] = None
    notes: Optional[MultilineHypertext] = None
    colors: List[Colors] = field(default_factory=list)
    wirelabels: List[Wire] = field(default_factory=list)
    color_code: Optional[ColorScheme] = None
    show_name: Optional[bool] = None
    show_wirecount: bool = True
    show_wirenumbers: Optional[bool] = None
    ignore_in_bom: bool = False
    additional_components: List[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.image = Image.create(self.image)

        if isinstance(self.gauge, str):  # gauge and unit specified
            try:
                g, u = self.gauge.split(" ")
            except Exception:
                raise Exception(
                    f"Cable {self.name} gauge={self.gauge} - Gauge must be a number, or number and unit separated by a space"
                )
            self.gauge = g

            if self.gauge_unit is not None:
                print(
                    f"Warning: Cable {self.name} gauge_unit={self.gauge_unit} is ignored because its gauge contains {u}"
                )
            if u.upper() == "AWG":
                self.gauge_unit = u.upper()
            else:
                self.gauge_unit = u.replace("mm2", "mm\u00B2")

        elif self.gauge is not None:  # gauge specified, assume mm2
            if self.gauge_unit is None:
                self.gauge_unit = "mm\u00B2"
        else:
            pass  # gauge not specified

        if isinstance(self.length, str):  # length and unit specified
            try:
                L, u = self.length.split(" ")
                L = float(L)
            except Exception:
                raise Exception(
                    f"Cable {self.name} length={self.length} - Length must be a number, or number and unit separated by a space"
                )
            self.length = L
            if self.length_unit is not None:
                print(
                    f"Warning: Cable {self.name} length_unit={self.length_unit} is ignored because its length contains {u}"
                )
            self.length_unit = u
        elif not isinstance(self.length, (int, float)):
            raise Exception(f"Cable {self.name} length has a non-numeric value")
        elif self.length_unit is None:
            self.length_unit = "m"

        self.connections = []

        if self.wirecount:  # number of wires explicitly defined
            if self.colors:  # use custom color palette (partly or looped if needed)
                pass
            elif self.color_code:
                # use standard color palette (partly or looped if needed)
                if self.color_code not in COLOR_CODES:
                    raise Exception("Unknown color code")
                self.colors = COLOR_CODES[self.color_code]
            else:  # no colors defined, add dummy colors
                self.colors = [""] * self.wirecount

            # make color code loop around if more wires than colors
            if self.wirecount > len(self.colors):
                m = self.wirecount // len(self.colors) + 1
                self.colors = self.colors * int(m)
            # cut off excess after looping
            self.colors = self.colors[: self.wirecount]
        else:  # wirecount implicit in length of color list
            if not self.colors:
                raise Exception(
                    "Unknown number of wires. Must specify wirecount or colors (implicit length)"
                )
            self.wirecount = len(self.colors)

        if self.wirelabels:
            if self.shield and "s" in self.wirelabels:
                raise Exception(
                    '"s" may not be used as a wire label for a shielded cable.'
                )

        # if lists of part numbers are provided check this is a bundle and that it matches the wirecount.
        for idfield in [self.manufacturer, self.mpn, self.supplier, self.spn, self.pn]:
            if isinstance(idfield, list):
                if self.category == "bundle":
                    # check the length
                    if len(idfield) != self.wirecount:
                        raise Exception("lists of part data must match wirecount")
                else:
                    raise Exception("lists of part data are only supported for bundles")

        if self.show_name is None:
            # hide designators for auto-generated cables by default
            self.show_name = self.name[0:2] != "__"

        if self.show_wirenumbers is None:
            # by default, show wire numbers for cables, hide for bundles
            self.show_wirenumbers = self.category != "bundle"

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    # The *_pin arguments accept a tuple, but it seems not in use with the current code.
    def connect(
        self,
        from_name: Optional[Designator],
        from_pin: NoneOrMorePinIndices,
        via_wire: OneOrMoreWires,
        to_name: Optional[Designator],
        to_pin: NoneOrMorePinIndices,
    ) -> None:
        from_pin = int2tuple(from_pin)
        via_wire = int2tuple(via_wire)
        to_pin = int2tuple(to_pin)
        if len(from_pin) != len(to_pin):
            raise Exception("from_pin must have the same number of elements as to_pin")
        for i, _ in enumerate(from_pin):
            self.connections.append(
                Connection(from_name, from_pin[i], via_wire[i], to_name, to_pin[i])
            )

    def get_qty_multiplier(self, qty_multiplier: Optional[CableMultiplier]) -> float:
        if not qty_multiplier:
            return 1
        elif qty_multiplier == "wirecount":
            return self.wirecount
        elif qty_multiplier == "terminations":
            return len(self.connections)
        elif qty_multiplier == "length":
            return self.length
        elif qty_multiplier == "total_length":
            return self.length * self.wirecount
        else:
            raise ValueError(
                f"invalid qty multiplier parameter for cable {qty_multiplier}"
            )


@dataclass
class Connection:
    from_name: Optional[Designator]
    from_pin: Optional[Pin]
    via_port: Wire
    to_name: Optional[Designator]
    to_pin: Optional[Pin]


@dataclass
class MatePin:
    from_name: Designator
    from_pin: Pin
    to_name: Designator
    to_pin: Pin
    shape: str


@dataclass
class MateComponent:
    from_name: Designator
    to_name: Designator
    shape: str
