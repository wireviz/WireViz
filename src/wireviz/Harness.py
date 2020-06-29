#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wireviz.Components import Connector, Cable
from graphviz import Graph
from wireviz import wv_colors
from wireviz.wv_helper import awg_equiv, tuplelist2tsv, nested, flatten2d
from collections import Counter
from typing import List


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
        for _, cable in self.cables.items():
            for connection in cable.connections:
                if connection.from_port is not None:  # connect to left
                    self.connectors[connection.from_name].ports_right = True
                if connection.to_port is not None:  # connect to right
                    self.connectors[connection.to_name].ports_left = True

        for key, connector in self.connectors.items():
            if connector.category == 'ferrule':
                subtype = f', {connector.subtype}' if connector.subtype else ''
                color = wv_colors.translate_color(connector.color, self.color_mode) if connector.color else ''
                infostring = f'{connector.maintype}{subtype} {color}'
                infostring_l = infostring if connector.ports_right else ''
                infostring_r = infostring if connector.ports_left else ''

                # INFO: Leaving this one as a string.format form because f-strings do not work well with triple quotes
                colorbar = f'<TD BGCOLOR="{wv_colors.translate_color(connector.color, "HEX")}" BORDER="1" SIDES="LR" WIDTH="4"></TD>' if connector.color else ''
                dot.node(key, shape='none',
                         style='filled',
                         margin='0',
                         orientation='0' if connector.ports_left else '180',
                         label='''<

                <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2"><TR>
                <TD PORT="p1l"> {infostring_l} </TD>
                {colorbar}
                <TD PORT="p1r"> {infostring_r} </TD>
                </TR></TABLE>


                >'''.format(infostring_l=infostring_l, infostring_r=infostring_r, colorbar=colorbar))

            else:  # not a ferrule
                attributes = [connector.maintype,
                              connector.subtype,
                              f'{connector.pincount}-pin' if connector.show_pincount else'']
                pinouts = [[], [], []]
                for pinnumber, pinname in zip(connector.pinnumbers, connector.pinout):
                    if connector.hide_disconnected_pins and not connector.visible_pins.get(pinnumber, False):
                        continue
                    pinouts[1].append(pinname)
                    if connector.ports_left:
                        pinouts[0].append(f'<p{pinnumber}l>{pinnumber}')
                    if connector.ports_right:
                        pinouts[2].append(f'<p{pinnumber}r>{pinnumber}')
                label = [connector.name if connector.show_name else '', attributes, pinouts, connector.notes]
                dot.node(key, label=nested(label))

                if len(connector.loops) > 0:
                    dot.attr('edge', color='#000000:#ffffff:#000000')
                    if connector.ports_left:
                        loop_side = 'l'
                        loop_dir = 'w'
                    elif connector.ports_right:
                        loop_side = 'r'
                        loop_dir = 'e'
                    else:
                        raise Exception('No side for loops')
                    for loop in connector.loops:

                        # FIXME: Original string.format style had some unused arguments (port_to for 1st arg,
                        # port_from for 2nd arg). De we need them back?

                        dot.edge(f'{connector.name}:p{loop[0]}{loop_side}:{loop_dir}',
                                 f'{connector.name}:p{loop[1]}{loop_side}:{loop_dir}')

        for _, cable in self.cables.items():
            awg_fmt = f' ({awg_equiv(cable.gauge)} AWG)' if cable.gauge_unit == 'mm\u00B2' and cable.show_equiv else ''
            attributes = [f'{len(cable.colors)}x' if cable.show_wirecount else '',
                          f'{cable.gauge} {cable.gauge_unit}{awg_fmt}' if cable.gauge else '',  # TODO: show equiv
                          '+ S' if cable.shield else '',
                          f'{cable.length} m' if cable.length > 0 else '']
            attributes = list(filter(None, attributes))

            html = '<table border="0" cellspacing="0" cellpadding="0"><tr><td>'  # main table

            html = f'{html}<table border="0" cellspacing="0" cellpadding="3" cellborder="1">'  # name+attributes table
            if cable.show_name:
                html = f'{html}<tr><td colspan="{len(attributes)}">{cable.name}</td></tr>'
            html = f'{html}<tr>'  # attribute row
            for attrib in attributes:
                html = f'{html}<td>{attrib}</td>'
            html = f'{html}</tr>'  # attribute row
            html = f'{html}</table></td></tr>'  # name+attributes table

            html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer between attributes and wires

            html = f'{html}<tr><td><table border="0" cellspacing="0" cellborder="0">'  # conductor table

            for i, connection in enumerate(cable.colors, 1):
                p = []
                p.append(f'<!-- {i}_in -->')
                p.append(wv_colors.translate_color(connection, self.color_mode))
                p.append(f'<!-- {i}_out -->')
                html = f'{html}<tr>'
                for bla in p:
                    html = f'{html}<td>{bla}</td>'
                html = f'{html}</tr>'
                bgcolor = wv_colors.translate_color(connection, 'hex')
                bgcolor = bgcolor if bgcolor != '' else '#ffffff'
                html = f'{html}<tr><td colspan="{len(p)}" cellpadding="0" height="6" bgcolor="{bgcolor}" border="2" sides="tb" port="w{i}"></td></tr>'

            if cable.shield:
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
            if cable.notes:
                html = f'{html}<tr><td cellpadding="3">{cable.notes}</td></tr>'  # notes table
                html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer at the end

            html = f'{html}</table>'  # main table

            # connections
            for connection in cable.connections:
                if isinstance(connection.via_port, int):  # check if it's an actual wire and not a shield
                    search_color = cable.colors[connection.via_port - 1]
                    if search_color in wv_colors.color_hex:
                        dot.attr('edge', color=f'#000000:{wv_colors.color_hex[search_color]}:#000000')
                    else:  # color name not found
                        dot.attr('edge', color='#000000:#ffffff:#000000')
                else:  # it's a shield connection
                    dot.attr('edge', color='#000000')

                if connection.from_port is not None:  # connect to left
                    from_ferrule = self.connectors[connection.from_name].category == 'ferrule'
                    port = f':p{connection.from_port}r' if not from_ferrule else ''
                    code_left_1 = f'{connection.from_name}{port}:e'
                    # FIXME: Uncomment, then add to end of f-string if needed
                    # via_subport = 'i' if c.show_pinout else ''
                    code_left_2 = f'{cable.name}:w{connection.via_port}:w'
                    dot.edge(code_left_1, code_left_2)
                    from_string = f'{connection.from_name}:{connection.from_port}' if not from_ferrule else ''
                    html = html.replace(f'<!-- {connection.via_port}_in -->', from_string)
                if connection.to_port is not None:  # connect to right
                    to_ferrule = self.connectors[connection.to_name].category == 'ferrule'

                    # FIXME: Add in if it was supposed to be here. the add to fstring two lines down
                    # via_subport = 'o' if c.show_pinout else ''
                    code_right_1 = f'{cable.name}:w{connection.via_port}:e'
                    to_port = f':p{connection.to_port}l' if not to_ferrule else ''
                    code_right_2 = f'{connection.to_name}{to_port}:w'
                    dot.edge(code_right_1, code_right_2)
                    to_string = f'{connection.to_name}:{connection.to_port}' if not to_ferrule else ''
                    html = html.replace(f'<!-- {connection.via_port}_out -->', to_string)

            dot.node(cable.name, label=f'<{html}>', shape='box',
                     style='filled,dashed' if cable.category == 'bundle' else '', margin='0', fillcolor='white')

        return dot

    def output(self, filename, directory='_output', view=False, cleanup=True, fmt='pdf', gen_bom=False):
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
                for svgdata in svg:
                    file.write(svgdata)

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
