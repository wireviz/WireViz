# -*- coding: utf-8 -*-

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import asdict, dataclass, field, InitVar
from pathlib import Path

from wireviz.wv_helper import int2tuple, aspect_ratio
from wireviz.wv_colors import Color, Colors, ColorMode, ColorScheme, COLOR_CODES, translate_color


# Each type alias have their legal values described in comments - validation might be implemented in the future
PlainText = str # Text not containing HTML tags nor newlines
Hypertext = str # Text possibly including HTML hyperlinks that are removed in all outputs except HTML output
MultilineHypertext = str # Hypertext possibly also including newlines to break lines in diagram output
Designator = PlainText # Case insensitive unique name of connector or cable
Points = float  # Size in points = 1/72 inch

# Literal type aliases below are commented to avoid requiring python 3.8
ConnectorMultiplier = PlainText # = Literal['pincount', 'populated']
CableMultiplier = PlainText # = Literal['wirecount', 'terminations', 'length', 'total_length']
ImageScale = PlainText # = Literal['false', 'true', 'width', 'height', 'both']

# Type combinations
Pin = Union[int, PlainText] # Pin identifier
PinIndex = int # Zero-based pin index
Wire = Union[int, PlainText] # Wire number or Literal['s'] for shield
NoneOrMorePinIndices = Union[PinIndex, Tuple[PinIndex, ...], None]  # None, one, or a tuple of zero-based pin indices
OneOrMoreWires = Union[Wire, Tuple[Wire, ...]] # One or a tuple of wires

# Metadata can contain whatever is needed by the HTML generation/template.
MetadataKeys = PlainText  # Literal['title', 'description', 'notes', ...]
class Metadata(dict):
    pass


@dataclass
class Look:
    """Colors and font that defines how an element should look like."""
    bordercolor: Optional[Color] = None
    bgcolor: Optional[Color] = None
    fontcolor: Optional[Color] = None
    fontname: Optional[PlainText] = None
    fontsize: Optional[Points] = None

    def lookdict(self) -> dict:
        """Return Look attributes as dict."""
        return {k:v for k,v in asdict(self).items() if k in asdict(DEFAULT_LOOK).keys()}

    def _2dict(self) -> dict:
        """Return dict of non-None strings with color values translated to hex."""
        return {
            k:translate_color(v, "hex") if 'color' in k else str(v)
            for k,v in self.lookdict().items() if v is not None
        }

    def graph_args(self) -> dict:
        """Return dict with arguments to a dot graph."""
        return {k:v for k,v in self._2dict().items() if k != 'bordercolor'}

    def node_args(self) -> dict:
        """Return dict with arguments to a dot node with filled style."""
        return {k.replace('border', '').replace('bg', 'fill'):v for k,v in self._2dict().items()}

    def html_style(self, color_prefix: Optional[str] = None, include_all: bool = True) -> str:
        """Return HTML style value containing all non-empty option values."""
        translated = Look(**self._2dict())
        return ' '.join(value for value in (
            f'{color_prefix} {translated.bordercolor};' if self.bordercolor and color_prefix else None,
            f'background-color: {translated.bgcolor};' if self.bgcolor and include_all else None,
            f'color: {translated.fontcolor};' if self.fontcolor and include_all else None,
            f'font-family: {self.fontname};' if self.fontname and include_all else None,
            f'font-size: {self.fontsize}pt;' if self.fontsize and include_all else None,
        ) if value)

DEFAULT_LOOK = Look(
    bordercolor = 'BK',
    bgcolor = 'WH',
    fontcolor = 'BK',
    fontname = 'arial',
    fontsize = 14,
)


@dataclass
class Options(Look):
    node: Look = field(default_factory=dict)
    connector: Look = field(default_factory=dict)
    cable: Look = field(default_factory=dict)
    bundle: Look = field(default_factory=dict)
    color_mode: ColorMode = 'SHORT'
    mini_bom_mode: bool = True

    def __post_init__(self):
        # Build initialization dicts with default values followed by dict entries from YAML input.
        self.node = Look(**{**self.lookdict(), **self.node})
        self.connector = Look(**{**asdict(self.node), **self.connector})
        self.cable = Look(**{**asdict(self.node), **self.cable})
        self.bundle = Look(**{**asdict(self.cable), **self.bundle})


@dataclass
class Tweak:
    override: Optional[Dict[Designator, Dict[str, Optional[str]]]] = None
    append: Union[str, List[str], None] = None


@dataclass
class Image:
    gv_dir: InitVar[Path] # Directory of .gv file injected as context during parsing
    # Attributes of the image object <img>:
    src: str
    scale: Optional[ImageScale] = None
    # Attributes of the image cell <td> containing the image:
    width: Optional[Points] = None
    height: Optional[Points] = None
    fixedsize: Optional[bool] = None
    box: Optional[Look] = None
    # Contents of the text cell <td> just below the image cell:
    caption: Optional[MultilineHypertext] = None
    # See also HTML doc at https://graphviz.org/doc/info/shapes.html#html

    def __post_init__(self, gv_dir):

        if isinstance(self.box, dict):
            self.box = Look(**self.box)

        if self.fixedsize is None:
            # Default True if any dimension specified unless self.scale also is specified.
            self.fixedsize = (self.width or self.height) and self.scale is None

        if self.scale is None:
            self.scale = "false" if not self.width and not self.height \
                else     "both"  if     self.width and     self.height \
                else     "true" # When only one dimension is specified.

        if self.fixedsize:
            # If only one dimension is specified, compute the other
            # because Graphviz requires both when fixedsize=True.
            if self.height:
                if not self.width:
                    self.width = self.height * aspect_ratio(gv_dir.joinpath(self.src))
            else:
                if self.width:
                    self.height = self.width / aspect_ratio(gv_dir.joinpath(self.src))


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
    box: Optional[Look] = None

    def __post_init__(self) -> None:
        if isinstance(self.box, dict):
            self.box = Look(**self.box)

    @property
    def description(self) -> str:
        return self.type.rstrip() + (f', {self.subtype.rstrip()}' if self.subtype else '')


@dataclass
class Connector:
    name: Designator
    box: Optional[Look] = None
    title: Optional[Look] = None
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
    autogenerate: bool = False
    loops: List[List[Pin]] = field(default_factory=list)
    ignore_in_bom: bool = False
    additional_components: List[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:

        if isinstance(self.box, dict):
            self.box = Look(**self.box)
        if isinstance(self.title, dict):
            self.title = Look(**self.title)
        if isinstance(self.image, dict):
            self.image = Image(**self.image)

        self.ports_left = False
        self.ports_right = False
        self.visible_pins = {}

        if self.style == 'simple':
            if self.pincount and self.pincount > 1:
                raise Exception('Connectors with style set to simple may only have one pin')
            self.pincount = 1

        if not self.pincount:
            self.pincount = max(len(self.pins), len(self.pinlabels), len(self.pincolors))
            if not self.pincount:
                raise Exception('You need to specify at least one, pincount, pins, pinlabels, or pincolors')

        # create default list for pins (sequential) if not specified
        if not self.pins:
            self.pins = list(range(1, self.pincount + 1))

        if len(self.pins) != len(set(self.pins)):
            raise Exception('Pins are not unique')

        if self.show_name is None:
            self.show_name = not self.autogenerate # hide auto-generated designators by default

        if self.show_pincount is None:
            self.show_pincount = self.style != 'simple' # hide pincount for simple (1 pin) connectors by default

        for loop in self.loops:
            # TODO: check that pins to connect actually exist
            # TODO: allow using pin labels in addition to pin numbers, just like when defining regular connections
            # TODO: include properties of wire used to create the loop
            if len(loop) != 2:
                raise Exception('Loops must be between exactly two pins!')

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    def activate_pin(self, pin: Pin) -> None:
        self.visible_pins[pin] = True

    def get_qty_multiplier(self, qty_multiplier: Optional[ConnectorMultiplier]) -> int:
        if not qty_multiplier:
            return 1
        elif qty_multiplier == 'pincount':
            return self.pincount
        elif qty_multiplier == 'populated':
            return sum(self.visible_pins.values())
        else:
            raise ValueError(f'invalid qty multiplier parameter for connector {qty_multiplier}')


@dataclass
class Cable:
    name: Designator
    box: Optional[Look] = None
    title: Optional[Look] = None
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
    show_name: bool = True
    show_wirecount: bool = True
    show_wirenumbers: Optional[bool] = None
    ignore_in_bom: bool = False
    additional_components: List[AdditionalComponent] = field(default_factory=list)

    def __post_init__(self) -> None:

        if isinstance(self.box, dict):
            self.box = Look(**self.box)
        if isinstance(self.title, dict):
            self.title = Look(**self.title)
        if isinstance(self.image, dict):
            self.image = Image(**self.image)

        if isinstance(self.gauge, str):  # gauge and unit specified
            try:
                g, u = self.gauge.split(' ')
            except Exception:
                raise Exception(f'Cable {self.name} gauge={self.gauge} - Gauge must be a number, or number and unit separated by a space')
            self.gauge = g

            if self.gauge_unit is not None:
                print(f'Warning: Cable {self.name} gauge_unit={self.gauge_unit} is ignored because its gauge contains {u}')
            if u.upper() == 'AWG':
                self.gauge_unit = u.upper()
            else:
                self.gauge_unit = u.replace('mm2', 'mm\u00B2')

        elif self.gauge is not None:  # gauge specified, assume mm2
            if self.gauge_unit is None:
                self.gauge_unit = 'mm\u00B2'
        else:
            pass  # gauge not specified

        if isinstance(self.length, str):  # length and unit specified
            try:
                L, u = self.length.split(' ')
                L = float(L)
            except Exception:
                raise Exception(f'Cable {self.name} length={self.length} - Length must be a number, or number and unit separated by a space')
            self.length = L
            if self.length_unit is not None:
                print(f'Warning: Cable {self.name} length_unit={self.length_unit} is ignored because its length contains {u}')
            self.length_unit = u
        elif not any(isinstance(self.length, t) for t in [int, float]):
            raise Exception(f'Cable {self.name} length has a non-numeric value')
        elif self.length_unit is None:
            self.length_unit = 'm'

        self.connections = []

        if self.wirecount:  # number of wires explicitly defined
            if self.colors:  # use custom color palette (partly or looped if needed)
                pass
            elif self.color_code:  # use standard color palette (partly or looped if needed)
                if self.color_code not in COLOR_CODES:
                    raise Exception('Unknown color code')
                self.colors = COLOR_CODES[self.color_code]
            else:  # no colors defined, add dummy colors
                self.colors = [''] * self.wirecount

            # make color code loop around if more wires than colors
            if self.wirecount > len(self.colors):
                m = self.wirecount // len(self.colors) + 1
                self.colors = self.colors * int(m)
            # cut off excess after looping
            self.colors = self.colors[:self.wirecount]
        else:  # wirecount implicit in length of color list
            if not self.colors:
                raise Exception('Unknown number of wires. Must specify wirecount or colors (implicit length)')
            self.wirecount = len(self.colors)

        if self.wirelabels:
            if self.shield and 's' in self.wirelabels:
                raise Exception('"s" may not be used as a wire label for a shielded cable.')

        # if lists of part numbers are provided check this is a bundle and that it matches the wirecount.
        for idfield in [self.manufacturer, self.mpn, self.supplier, self.spn, self.pn]:
            if isinstance(idfield, list):
                if self.category == "bundle":
                    # check the length
                    if len(idfield) != self.wirecount:
                        raise Exception('lists of part data must match wirecount')
                else:
                    raise Exception('lists of part data are only supported for bundles')

        # by default, show wire numbers for cables, hide for bundles
        if self.show_wirenumbers is None:
            self.show_wirenumbers = self.category != 'bundle'

        for i, item in enumerate(self.additional_components):
            if isinstance(item, dict):
                self.additional_components[i] = AdditionalComponent(**item)

    # The *_pin arguments accept a tuple, but it seems not in use with the current code.
    def connect(self, from_name: Optional[Designator], from_pin: NoneOrMorePinIndices, via_wire: OneOrMoreWires,
                to_name: Optional[Designator], to_pin: NoneOrMorePinIndices) -> None:
        from_pin = int2tuple(from_pin)
        via_wire = int2tuple(via_wire)
        to_pin = int2tuple(to_pin)
        if len(from_pin) != len(to_pin):
            raise Exception('from_pin must have the same number of elements as to_pin')
        for i, _ in enumerate(from_pin):
            self.connections.append(Connection(from_name, from_pin[i], via_wire[i], to_name, to_pin[i]))

    def get_qty_multiplier(self, qty_multiplier: Optional[CableMultiplier]) -> float:
        if not qty_multiplier:
            return 1
        elif qty_multiplier == 'wirecount':
            return self.wirecount
        elif qty_multiplier == 'terminations':
            return len(self.connections)
        elif qty_multiplier == 'length':
            return self.length
        elif qty_multiplier == 'total_length':
            return self.length * self.wirecount
        else:
            raise ValueError(f'invalid qty multiplier parameter for cable {qty_multiplier}')


@dataclass
class Connection:
    from_name: Optional[Designator]
    from_port: Optional[PinIndex]
    via_port: Wire
    to_name: Optional[Designator]
    to_port: Optional[PinIndex]
