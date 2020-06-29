#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
from collections import Counter
from dataclasses import dataclass, field
from graphviz import Graph
import os
import sys
from typing import Any, List, Optional
import yaml

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wireviz import wv_colors
from wireviz.wv_helper import nested, int2tuple, awg_equiv, flatten2d, tuplelist2tsv


class Harness:

    def __init__(self):
        self.color_mode = 'SHORT'
        self.connectors = {}
        self.cables = {}

    def add_connector(self, name, *args, **kwargs):
        self.connectors[name] = Connector(name, *args, **kwargs)

    def add_cable(self, name, *args, **kwargs):
        self.cables[name] = Cable(name, *args, **kwargs)

    def loop(self, connector_name, from_pin, to_pin):
        self.connectors[connector_name].loop(from_pin, to_pin)

    def connect(self, from_name, from_pin, via_name, via_pin, to_name, to_pin):
        self.cables[via_name].connect(from_name, from_pin, via_pin, to_name, to_pin)
        if from_name in self.connectors:
            self.connectors[from_name].activate_pin(from_pin)
        if to_name in self.connectors:
            self.connectors[to_name].activate_pin(to_pin)

    def create_graph(self):
        dot = Graph()
        dot.body.append('// Graph generated by WireViz')
        dot.body.append('// https://github.com/formatc1702/WireViz')
        font = 'arial'
        dot.attr('graph', rankdir='LR',
                 ranksep='2',
                 bgcolor='white',
                 nodesep='0.33',
                 fontname=font)
        dot.attr('node', shape='record',
                 style='filled',
                 fillcolor='white',
                 fontname=font)
        dot.attr('edge', style='bold',
                 fontname=font)

        # prepare ports on connectors depending on which side they will connect
        for k, c in self.cables.items():
            for x in c.connections:
                if x.from_port is not None:  # connect to left
                    self.connectors[x.from_name].ports_right = True
                if x.to_port is not None:  # connect to right
                    self.connectors[x.to_name].ports_left = True

        for k, n in self.connectors.items():
            if n.category == 'ferrule':
                subtype = f', {n.subtype}' if n.subtype else ''
                color = wv_colors.translate_color(n.color, self.color_mode) if n.color else ''
                infostring = f'{n.maintype}{subtype} {color}'
                infostring_l = infostring if n.ports_right else ''
                infostring_r = infostring if n.ports_left else ''

                # INFO: Leaving this one as a string.format form because f-strings do not work well with triple quotes
                colorbar = f'<TD BGCOLOR="{wv_colors.translate_color(n.color, "HEX")}" BORDER="1" SIDES="LR" WIDTH="4"></TD>' if n.color else ''
                dot.node(k, shape='none',
                         style='filled',
                         margin='0',
                         orientation='0' if n.ports_left else '180',
                         label='''<

                <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2"><TR>
                <TD PORT="p1l"> {infostring_l} </TD>
                {colorbar}
                <TD PORT="p1r"> {infostring_r} </TD>
                </TR></TABLE>


                >'''.format(infostring_l=infostring_l, infostring_r=infostring_r, colorbar=colorbar))

            else:  # not a ferrule
                attributes = [n.maintype,
                              n.subtype,
                              f'{n.pincount}-pin' if n.show_pincount else'']
                pinouts = [[], [], []]
                for pinnumber, pinname in zip(n.pinnumbers, n.pinout):
                    if n.hide_disconnected_pins and not n.visible_pins.get(pinnumber, False):
                        continue
                    pinouts[1].append(pinname)
                    if n.ports_left:
                        pinouts[0].append(f'<p{pinnumber}l>{pinnumber}')
                    if n.ports_right:
                        pinouts[2].append(f'<p{pinnumber}r>{pinnumber}')
                label = [n.name if n.show_name else '', attributes, pinouts, n.notes]
                dot.node(k, label=nested(label))

                if len(n.loops) > 0:
                    dot.attr('edge', color='#000000:#ffffff:#000000')
                    if n.ports_left:
                        loop_side = 'l'
                        loop_dir = 'w'
                    elif n.ports_right:
                        loop_side = 'r'
                        loop_dir = 'e'
                    else:
                        raise Exception('No side for loops')
                    for loop in n.loops:

                        # FIXME: Original string.format style had some unused arguments (port_to for 1st arg,
                        # port_from for 2nd arg). De we need them back?

                        dot.edge(f'{n.name}:p{loop[0]}{loop_side}:{loop_dir}',
                                 f'{n.name}:p{loop[1]}{loop_side}:{loop_dir}')

        for _, c in self.cables.items():
            awg_fmt = f' ({awg_equiv(c.gauge)} AWG)' if c.gauge_unit == 'mm\u00B2' and c.show_equiv else ''
            attributes = [f'{len(c.colors)}x' if c.show_wirecount else '',
                          f'{c.gauge} {c.gauge_unit}{awg_fmt}' if c.gauge else '',  # TODO: show equiv
                          '+ S' if c.shield else '',
                          f'{c.length} m' if c.length > 0 else '']
            attributes = list(filter(None, attributes))

            html = '<table border="0" cellspacing="0" cellpadding="0"><tr><td>'  # main table

            html = f'{html}<table border="0" cellspacing="0" cellpadding="3" cellborder="1">'  # name+attributes table
            if c.show_name:
                html = f'{html}<tr><td colspan="{len(attributes)}">{c.name}</td></tr>'
            html = f'{html}<tr>'  # attribute row
            for attrib in attributes:
                html = f'{html}<td>{attrib}</td>'
            html = f'{html}</tr>'  # attribute row
            html = f'{html}</table></td></tr>'  # name+attributes table

            html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer between attributes and wires

            html = f'{html}<tr><td><table border="0" cellspacing="0" cellborder="0">'  # conductor table

            for i, x in enumerate(c.colors, 1):
                p = []
                p.append(f'<!-- {i}_in -->')
                p.append(wv_colors.translate_color(x, self.color_mode))
                p.append(f'<!-- {i}_out -->')
                html = f'{html}<tr>'
                for bla in p:
                    html = f'{html}<td>{bla}</td>'
                html = f'{html}</tr>'
                bgcolor = wv_colors.translate_color(x, 'hex')
                bgcolor = bgcolor if bgcolor != '' else '#ffffff'
                html = f'{html}<tr><td colspan="{len(p)}" cellpadding="0" height="6" bgcolor="{bgcolor}" border="2" sides="tb" port="w{i}"></td></tr>'

            if c.shield:
                p = ['<!-- s_in -->', 'Shield', '<!-- s_out -->']
                html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer
                html = f'{html}<tr>'
                for bla in p:
                    html = html + f'<td>{bla}</td>'
                html = f'{html}</tr>'

                # FIXME, original string.format had a unused bgcolor argument. Do we need it back
                html = f'{html}<tr><td colspan="{len(p)}" cellpadding="0" height="6" border="2" sides="b" port="ws"></td></tr>'

            html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer at the end

            html = f'{html}</table>'  # conductor table

            html = f'{html}</td></tr>'  # main table
            if c.notes:
                html = f'{html}<tr><td cellpadding="3">{c.notes}</td></tr>'  # notes table
                html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer at the end

            html = f'{html}</table>'  # main table

            # connections
            for x in c.connections:
                if isinstance(x.via_port, int):  # check if it's an actual wire and not a shield
                    search_color = c.colors[x.via_port - 1]
                    if search_color in wv_colors.color_hex:
                        dot.attr('edge', color=f'#000000:{wv_colors.color_hex[search_color]}:#000000')
                    else:  # color name not found
                        dot.attr('edge', color='#000000:#ffffff:#000000')
                else:  # it's a shield connection
                    dot.attr('edge', color='#000000')

                if x.from_port is not None:  # connect to left
                    from_ferrule = self.connectors[x.from_name].category == 'ferrule'
                    port = f':p{x.from_port}r' if not from_ferrule else ''
                    code_left_1 = f'{x.from_name}{port}:e'
                    # FIXME: Uncomment, then add to end of f-string if needed
                    # via_subport = 'i' if c.show_pinout else ''
                    code_left_2 = f'{c.name}:w{x.via_port}:w'
                    dot.edge(code_left_1, code_left_2)
                    from_string = f'{x.from_name}:{x.from_port}' if not from_ferrule else ''
                    html = html.replace(f'<!-- {x.via_port}_in -->', from_string)
                if x.to_port is not None:  # connect to right
                    to_ferrule = self.connectors[x.to_name].category == 'ferrule'

                    # FIXME: Add in if it was supposed to be here. the add to fstring two lines down
                    # via_subport = 'o' if c.show_pinout else ''
                    code_right_1 = f'{c.name}:w{x.via_port}:e'
                    to_port = f':p{x.to_port}l' if not to_ferrule else ''
                    code_right_2 = f'{x.to_name}{to_port}:w'
                    dot.edge(code_right_1, code_right_2)
                    to_string = f'{x.to_name}:{x.to_port}' if not to_ferrule else ''
                    html = html.replace(f'<!-- {x.via_port}_out -->', to_string)

            dot.node(c.name, label=f'<{html}>', shape='box',
                     style='filled,dashed' if c.category == 'bundle' else '', margin='0', fillcolor='white')

        return dot

    def output(self, filename, directory='_output', view=False, cleanup=True, format='pdf', gen_bom=False):
        # graphical output
        digraph = self.create_graph()
        for f in format:
            digraph.format = f
            digraph.render(filename=filename, directory=directory, view=view, cleanup=cleanup)
        digraph.save(filename=f'{filename}.gv', directory=directory)
        # bom output
        bom_list = self.bom_list()
        with open(f'{filename}.bom.tsv', 'w') as file:
            file.write(tuplelist2tsv(bom_list))
        # HTML output
        with open(f'{filename}.html', 'w') as file:
            file.write('<html><body style="font-family:Arial">')

            file.write('<h1>Diagram</h1>')
            with open(f'{filename}.svg') as svg:
                for svgLine in svg:
                    file.write(svgLine)

            file.write('<h1>Bill of Materials</h1>')
            listy = flatten2d(bom_list)
            file.write('<table style="border:1px solid #000000; font-size: 14pt; border-spacing: 0px">')
            file.write('<tr>')
            for item in listy[0]:
                file.write(f'<th align="left" style="border:1px solid #000000; padding: 8px">{item}</th>')
            file.write('</tr>')
            for row in listy[1:]:
                file.write('<tr>')
                for i, item in enumerate(row):
                    align = 'align="right"' if listy[0][i] == 'Qty' else ''
                    file.write(f'<td {align} style="border:1px solid #000000; padding: 4px"><{item}</td>')
                file.write('</tr>')
            file.write('</table>')

            file.write('</body></html>')

    def bom(self):
        bom = []
        bom_connectors = []
        bom_cables = []
        # connectors
        types = Counter([(v.maintype, v.subtype, v.pincount) for v in self.connectors.values()])
        for maintype in types:
            items = {k: v for k, v in self.connectors.items() if (v.maintype, v.subtype, v.pincount) == maintype}
            shared = next(iter(items.values()))
            designators = list(items.keys())
            designators.sort()
            conn_type = f', {shared.maintype}' if shared.maintype else ''
            conn_subtype = f', {shared.subtype}' if shared.subtype else ''
            conn_pincount = f', {shared.pincount} pins' if shared.category != 'ferrule' else ''
            conn_color = f', {shared.color}' if shared.color else ''
            name = f'Connector{conn_type}{conn_subtype}{conn_pincount}{conn_color}'
            item = {'item': name, 'qty': len(designators), 'unit': '',
                    'designators': designators if shared.category != 'ferrule' else ''}
            bom_connectors.append(item)
            bom_connectors = sorted(bom_connectors, key=lambda k: k['item'])  # https://stackoverflow.com/a/73050
        bom.extend(bom_connectors)
        # cables
        types = Counter([(v.category, v.gauge, v.gauge_unit, v.wirecount, v.shield) for v in self.cables.values()])
        for maintype in types:
            items = {k: v for k, v in self.cables.items() if (
                v.category, v.gauge, v.gauge_unit, v.wirecount, v.shield) == maintype}
            shared = next(iter(items.values()))
            if shared.category != 'bundle':
                designators = list(items.keys())
                designators.sort()
                total_length = sum(i.length for i in items.values())
                gauge_name = f' x {shared.gauge} {shared.gauge_unit}'if shared.gauge else ' wires'
                shield_name = ' shielded' if shared.shield else ''
                name = f'Cable, {shared.wirecount}{gauge_name}{shield_name}'
                item = {'item': name, 'qty': round(total_length, 3), 'unit': 'm', 'designators': designators}
                bom_cables.append(item)
        # bundles (ignores wirecount)
        wirelist = []
        # list all cables again, since bundles are represented as wires internally, with the category='bundle' set
        types = Counter([(v.category, v.gauge, v.gauge_unit, v.length) for v in self.cables.values()])
        for maintype in types:
            items = {k: v for k, v in self.cables.items() if (v.category, v.gauge, v.gauge_unit, v.length) == maintype}
            shared = next(iter(items.values()))
            # filter out cables that are not bundles
            if shared.category == 'bundle':
                for bundle in items.values():
                    # add each wire from each bundle to the wirelist
                    for color in bundle.colors:
                        wirelist.append({'gauge': shared.gauge, 'gauge_unit': shared.gauge_unit,
                                         'length': shared.length, 'color': color, 'designator': bundle.name})
        # join similar wires from all the bundles to a single BOM item
        types = Counter([(v['gauge'], v['gauge_unit'], v['color']) for v in wirelist])
        for maintype in types:
            items = [v for v in wirelist if (v['gauge'], v['gauge_unit'], v['color']) == maintype]
            shared = items[0]
            designators = [i['designator'] for i in items]
            # remove duplicates
            designators = list(dict.fromkeys(designators))
            designators.sort()
            total_length = sum(i['length'] for i in items)
            gauge_name = f', {shared["gauge"]} {shared["gauge_unit"]}' if shared['gauge'] else ''
            gauge_color = f', {shared["color"]}' if shared['color'] != '' else ''
            name = f'Wire{gauge_name}{gauge_color}'
            item = {'item': name, 'qty': round(total_length, 3), 'unit': 'm', 'designators': designators}
            bom_cables.append(item)
            bom_cables = sorted(bom_cables, key=lambda k: k['item'])  # https://stackoverflow.com/a/73050
        bom.extend(bom_cables)
        return bom

    def bom_list(self):
        bom = self.bom()
        keys = ['item', 'qty', 'unit', 'designators']
        bom_list = []
        bom_list.append([k.capitalize() for k in keys])  # create header row with keys
        for item in bom:
            item_list = [item.get(key, '') for key in keys]  # fill missing values with blanks
            for i, subitem in enumerate(item_list):
                if isinstance(subitem, List):  # convert any lists into comma separated strings
                    item_list[i] = ', '.join(subitem)
            bom_list.append(item_list)
        return bom_list


@dataclass
class Connector:
    name: str
    category: Optional[str] = None
    maintype: Optional[str] = None
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
    maintype: Optional[str] = None
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
    show_pinout: bool = False
    show_wirecount: bool = True

    def __post_init__(self):

        if isinstance(self.gauge, str):  # gauge and unit specified
            try:
                g, u = self.gauge.split(' ')
            except Exception:
                raise Exception('Gauge must be a number, or number and unit separated by a space')
            self.gauge = g
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
        for i, x in enumerate(from_pin):
            # self.connections.append((from_name, from_pin[i], via_pin[i], to_name, to_pin[i]))
            self.connections.append(Connection(from_name, from_pin[i], via_pin[i], to_name, to_pin[i]))


@dataclass
class Connection:
    from_name: Any
    from_port: Any
    via_port: Any
    to_name: Any
    to_port: Any


def parse(yaml_input, file_out=None, generate_bom=False):

    yaml_data = yaml.safe_load(yaml_input)

    def expand(yaml_data):
        # yaml_data can be:
        # - a singleton (normally str or int)
        # - a list of str or int
        # if str is of the format '#-#', it is treated as a range (inclusive) and expanded
        output = []
        if not isinstance(yaml_data, list):
            yaml_data = [yaml_data]
        for e in yaml_data:
            e = str(e)
            if '-' in e:  # list of pins
                a, b = tuple(map(int, e.split('-')))
                if a < b:
                    for x in range(a, b + 1):
                        output.append(x)
                elif a > b:
                    for x in range(a, b - 1, -1):
                        output.append(x)
                elif a == b:
                    output.append(a)
            else:
                try:
                    x = int(e)
                except Exception:
                    x = e
                output.append(x)
        return output

    def check_designators(what, where):
        for i, x in enumerate(what):
            if x not in yaml_data[where[i]]:
                return False
        return True

    harness = Harness()

    # add items
    sections = ['connectors', 'cables', 'ferrules', 'connections']
    types = [dict, dict, dict, list]
    for sec, ty in zip(sections, types):
        if sec in yaml_data and type(yaml_data[sec]) == ty:
            if len(yaml_data[sec]) > 0:
                if ty == dict:
                    for k, o in yaml_data[sec].items():
                        if sec == 'connectors':
                            harness.add_connector(name=k, **o)
                        elif sec == 'cables':
                            harness.add_cable(name=k, **o)
                        elif sec == 'ferrules':
                            pass
            else:
                pass  # section exists but is empty
        else:  # section does not exist, create empty section
            if ty == dict:
                yaml_data[sec] = {}
            elif ty == list:
                yaml_data[sec] = []

    # add connections
    ferrule_counter = 0
    for con in yaml_data['connections']:
        if len(con) == 3:  # format: connector -- cable -- connector

            for c in con:
                if len(list(c.keys())) != 1:  # check that each entry in con has only one key, which is the designator
                    raise Exception('Too many keys')

            from_name = list(con[0].keys())[0]
            via_name = list(con[1].keys())[0]
            to_name = list(con[2].keys())[0]

            if not check_designators([from_name, via_name, to_name], ('connectors', 'cables', 'connectors')):
                print([from_name, via_name, to_name])
                raise Exception('Bad connection definition (3)')

            from_pins = expand(con[0][from_name])
            via_pins = expand(con[1][via_name])
            to_pins = expand(con[2][to_name])

            if len(from_pins) != len(via_pins) or len(via_pins) != len(to_pins):
                raise Exception('List length mismatch')

            for (from_pin, via_pin, to_pin) in zip(from_pins, via_pins, to_pins):
                harness.connect(from_name, from_pin, via_name, via_pin, to_name, to_pin)

        elif len(con) == 2:

            for c in con:
                if type(c) is dict:
                    if len(list(c.keys())) != 1:  # check that each entry in con has only one key, which is the designator
                        raise Exception('Too many keys')

            # hack to make the format for ferrules compatible with the formats for connectors and cables
            if type(con[0]) == str:
                name = con[0]
                con[0] = {}
                con[0][name] = name
            if type(con[1]) == str:
                name = con[1]
                con[1] = {}
                con[1][name] = name

            from_name = list(con[0].keys())[0]
            to_name = list(con[1].keys())[0]

            con_cbl = check_designators([from_name, to_name], ('connectors', 'cables'))
            cbl_con = check_designators([from_name, to_name], ('cables', 'connectors'))
            con_con = check_designators([from_name, to_name], ('connectors', 'connectors'))

            fer_cbl = check_designators([from_name, to_name], ('ferrules', 'cables'))
            cbl_fer = check_designators([from_name, to_name], ('cables', 'ferrules'))

            if not con_cbl and not cbl_con and not con_con and not fer_cbl and not cbl_fer:
                raise Exception('Wrong designators')

            from_pins = expand(con[0][from_name])
            to_pins = expand(con[1][to_name])

            if con_cbl or cbl_con or con_con:
                if len(from_pins) != len(to_pins):
                    raise Exception('List length mismatch')

            if con_cbl or cbl_con:
                for (from_pin, to_pin) in zip(from_pins, to_pins):
                    if con_cbl:
                        harness.connect(from_name, from_pin, to_name, to_pin, None, None)
                    else:  # cbl_con
                        harness.connect(None, None, from_name, from_pin, to_name, to_pin)
            elif con_con:
                cocon_coname = list(con[0].keys())[0]
                from_pins = expand(con[0][from_name])
                to_pins = expand(con[1][to_name])

                for (from_pin, to_pin) in zip(from_pins, to_pins):
                    harness.loop(cocon_coname, from_pin, to_pin)
            if fer_cbl or cbl_fer:
                from_pins = expand(con[0][from_name])
                to_pins = expand(con[1][to_name])

                if fer_cbl:
                    ferrule_name = from_name
                    cable_name = to_name
                    cable_pins = to_pins
                else:
                    ferrule_name = to_name
                    cable_name = from_name
                    cable_pins = from_pins

                ferrule_params = yaml_data['ferrules'][ferrule_name]
                for cable_pin in cable_pins:
                    ferrule_counter = ferrule_counter + 1
                    ferrule_id = f'_F{ferrule_counter}'
                    harness.add_connector(ferrule_id, category='ferrule', **ferrule_params)

                    if fer_cbl:
                        harness.connect(ferrule_id, 1, cable_name, cable_pin, None, None)
                    else:
                        harness.connect(None, None, cable_name, cable_pin, ferrule_id, 1)

        else:
            raise Exception('Wrong number of connection parameters')

    harness.output(filename=file_out, format=('png', 'svg'), gen_bom=generate_bom, view=False)


def parse_file(yaml_file, file_out=None, generate_bom=False):
    with open(yaml_file, 'r') as file:
        yaml_input = file.read()

    if not file_out:
        fn, fext = os.path.splitext(yaml_file)
        file_out = fn
    file_out = os.path.abspath(file_out)

    parse(yaml_input, file_out=file_out, generate_bom=generate_bom)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        description='Generate cable and wiring harness documentation from YAML descriptions',
    )

    parser.add_argument('input_file', action='store', type=str, metavar='YAML_FILE')

    parser.add_argument('-o', '--output_file', action='store', type=str, metavar='OUTPUT')

    parser.add_argument('--generate-bom', action='store_true', default=True)

    parser.add_argument('--prepend-file', action='store', type=str, metavar='YAML_FILE')

    return parser.parse_args()


def main():

    args = parse_cmdline()

    if not os.path.exists(args.input_file):
        print(f'Error: input file {args.input_file} inaccessible or does not exist, check path')
        sys.exit(1)

    with open(args.input_file) as fh:
        yaml_input = fh.read()

    if args.prepend_file:
        if not os.path.exists(args.prepend_file):
            print(f'Error: prepend input file {args.prepend_file} inaccessible or does not exist, check path')
            sys.exit(1)
        with open(args.prepend_file) as fh:
            prepend = fh.read()
            yaml_input = prepend + yaml_input

    if not args.output_file:
        file_out = args.input_file
        pre, _ = os.path.splitext(file_out)
        file_out = pre  # extension will be added by graphviz output function
    else:
        file_out = args.output_file
    file_out = os.path.abspath(file_out)

    parse(yaml_input, file_out=file_out, generate_bom=args.generate_bom)


if __name__ == '__main__':
    main()
