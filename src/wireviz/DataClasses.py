#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Any
from dataclasses import dataclass, field
from wireviz.wv_helper import int2tuple
from wireviz import wv_colors


@dataclass
class Connector:
    name: str
    category: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    pincount: Optional[int] = None
    notes: Optional[str] = None
    pinout: List[Any] = field(default_factory=list)
    pinnumbers: List[Any] = field(default_factory=list)
    color: Optional[str] = None
    show_name: bool = True
    show_pincount: bool = True
    hide_disconnected_pins: bool = False

    def __post_init__(self):
        self.ports_left = False
        self.ports_right = False
        self.loops = []
        self.visible_pins = {}

        if self.pincount is None:
            if self.pinout:
                self.pincount = len(self.pinout)
            elif self.pinnumbers:
                self.pincount = len(self.pinnumbers)
            elif self.category == 'ferrule':
                self.pincount = 1
            else:
                raise Exception('You need to specify at least one, pincount, pinout or pinnumbers')

        if self.pinout and self.pinnumbers:
            if len(self.pinout) != len(self.pinnumbers):
                raise Exception('Given pinout and pinnumbers size mismatch')

        # create default lists for pinnumbers (sequential) and pinouts (blank) if not specified
        if not self.pinnumbers:
            self.pinnumbers = list(range(1, self.pincount + 1))
        if not self.pinout:
            self.pinout = [''] * self.pincount

    def loop(self, from_pin, to_pin):
        self.loops.append((from_pin, to_pin))
        if self.hide_disconnected_pins:
            self.visible_pins[from_pin] = True
            self.visible_pins[to_pin] = True

    def activate_pin(self, pin):
        self.visible_pins[pin] = True


@dataclass
class Cable:
    name: str
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
