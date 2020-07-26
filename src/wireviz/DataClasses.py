#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Any, Union
from dataclasses import dataclass, field
from wireviz.wv_helper import int2tuple
from wireviz import wv_colors


@dataclass
class Connector:
    name: str
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None
    pn: Optional[str] = None
    style: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    pincount: Optional[int] = None
    notes: Optional[str] = None
    pinlabels: List[Any] = field(default_factory=list)
    pins: List[Any] = field(default_factory=list)
    color: Optional[str] = None
    show_name: bool = None
    show_pincount: bool = None
    hide_disconnected_pins: bool = False
    autogenerate: bool = False
    loops: List[Any] = field(default_factory=list)

    def __post_init__(self):
        self.ports_left = False
        self.ports_right = False
        self.visible_pins = {}

        if self.style == 'simple':
            if self.pincount and self.pincount > 1:
                raise Exception('Connectors with style set to simple may only have one pin')
            self.pincount = 1

        if self.pincount is None:
            if self.pinlabels:
                self.pincount = len(self.pinlabels)
            elif self.pins:
                self.pincount = len(self.pins)
            else:
                raise Exception('You need to specify at least one, pincount, pins or pinlabels')

        if self.pinlabels and self.pins:
            if len(self.pinlabels) != len(self.pins):
                raise Exception('Given pins and pinlabels size mismatch')

        # create default lists for pins (sequential) and pinlabels (blank) if not specified
        if not self.pins:
            self.pins = list(range(1, self.pincount + 1))
        if not self.pinlabels:
            self.pinlabels = [''] * self.pincount

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

    def activate_pin(self, pin):
        self.visible_pins[pin] = True


@dataclass
class Cable:
    name: str
    manufacturer: Optional[Union[str, List[str]]] = None
    mpn: Optional[Union[str, List[str]]] = None
    pn: Optional[Union[str, List[str]]] = None
    category: Optional[str] = None
    type: Optional[str] = None
    gauge: Optional[float] = None
    gauge_unit: Optional[str] = None
    show_equiv: bool = False
    length: float = 0
    wirecount: Optional[int] = None
    shield: bool = False
    notes: Optional[str] = None
    colors: List[Any] = field(default_factory=list)
    color_code: Optional[str] = None
    show_name: bool = True
    show_wirecount: bool = True

    def __post_init__(self):

        if isinstance(self.gauge, str):  # gauge and unit specified
            try:
                g, u = self.gauge.split(' ')
            except Exception:
                raise Exception('Gauge must be a number, or number and unit separated by a space')
            self.gauge = g

            if u.upper() == 'AWG':
                self.gauge_unit = u.upper()
            else:
                self.gauge_unit = u.replace('mm2', 'mm\u00B2')

        elif self.gauge is not None:  # gauge specified, assume mm2
            if self.gauge_unit is None:
                self.gauge_unit = 'mm\u00B2'
        else:
            pass  # gauge not specified

        self.connections = []

        if self.wirecount:  # number of wires explicitly defined
            if self.colors:  # use custom color palette (partly or looped if needed)
                pass
            elif self.color_code:  # use standard color palette (partly or looped if needed)
                if self.color_code not in wv_colors.COLOR_CODES:
                    raise Exception('Unknown color code')
                self.colors = wv_colors.COLOR_CODES[self.color_code]
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

        # if lists of part numbers are provided check this is a bundle and that it matches the wirecount.
        for idfield in [self.manufacturer, self.mpn, self.pn]:
            if isinstance(idfield, list):
                if self.category == "bundle":
                    # check the length
                    if len(idfield) != self.wirecount:
                        raise Exception('lists of part data must match wirecount')
                else:
                    raise Exception('lists of part data are only supported for bundles')

        # for BOM generation
        self.wirecount_and_shield = (self.wirecount, self.shield)

    def connect(self, from_name, from_pin, via_pin, to_name, to_pin):
        from_pin = int2tuple(from_pin)
        via_pin = int2tuple(via_pin)
        to_pin = int2tuple(to_pin)
        if len(from_pin) != len(to_pin):
            raise Exception('from_pin must have the same number of elements as to_pin')
        for i, _ in enumerate(from_pin):
            # self.connections.append((from_name, from_pin[i], via_pin[i], to_name, to_pin[i]))
            self.connections.append(Connection(from_name, from_pin[i], via_pin[i], to_name, to_pin[i]))


@dataclass
class Connection:
    from_name: Any
    from_port: Any
    via_port: Any
    to_name: Any
    to_port: Any
