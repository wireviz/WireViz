#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wireviz.DataClasses import Connector, Cable
from graphviz import Graph
from wireviz import wv_colors, wv_helper
from wireviz.wv_colors import get_color_hex
from wireviz.wv_helper import awg_equiv, mm2_equiv, tuplelist2tsv, \
    nested_html_table, flatten2d, index_if_list, html_line_breaks, \
    graphviz_line_breaks, remove_line_breaks, open_file_read, open_file_write
from collections import Counter
from typing import List
from pathlib import Path
import re


class Harness:

    def __init__(self):
        self.color_mode = 'SHORT'
        self.connectors = {}
        self.cables = {}
        self.additional_bom_items = []

    def add_connector(self, name: str, *args, **kwargs) -> None:
        self.connectors[name] = Connector(name, *args, **kwargs)

    def add_cable(self, name: str, *args, **kwargs) -> None:
        self.cables[name] = Cable(name, *args, **kwargs)

    def add_bom_item(self, item: dict) -> None:
        self.additional_bom_items.append(item)

    def connect(self, from_name: str, from_pin: (int, str), via_name: str, via_pin: (int, str), to_name: str, to_pin: (int, str)) -> None:
        for (name, pin) in zip([from_name, to_name], [from_pin, to_pin]):  # check from and to connectors
            if name is not None and name in self.connectors:
                connector = self.connectors[name]
                if pin in connector.pinnumbers and pin in connector.pinout:
                    if connector.pinnumbers.index(pin) == connector.pinout.index(pin):
                        # TODO: Maybe issue a warning? It's not worthy of an exception if it's unambiguous, but maybe risky?
                        pass
                    else:
                        raise Exception(f'{name}:{pin} is defined both in pinout and pinnumbers, for different pins.')
                if pin in connector.pinout:
                    if connector.pinout.count(pin) > 1:
                        raise Exception(f'{name}:{pin} is defined more than once.')
                    else:
                        index = connector.pinout.index(pin)
                        pin = connector.pinnumbers[index] # map pin name to pin number
                        if name == from_name:
                            from_pin = pin
                        if name == to_name:
                            to_pin = pin
                if not pin in connector.pinnumbers:
                    raise Exception(f'{name}:{pin} not found.')

        self.cables[via_name].connect(from_name, from_pin, via_pin, to_name, to_pin)
        if from_name in self.connectors:
            self.connectors[from_name].activate_pin(from_pin)
        if to_name in self.connectors:
            self.connectors[to_name].activate_pin(to_pin)

    def create_graph(self) -> Graph:
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
            for connection_color in cable.connections:
                if connection_color.from_port is not None:  # connect to left
                    self.connectors[connection_color.from_name].ports_right = True
                if connection_color.to_port is not None:  # connect to right
                    self.connectors[connection_color.to_name].ports_left = True

        for key, connector in self.connectors.items():
            if connector.category == 'ferrule':

                rows = [[connector.manufacturer,
                        f'MPN: {connector.manufacturer_part_number}' if connector.manufacturer_part_number else None,
                        f'IPN: {connector.internal_part_number}' if connector.internal_part_number else None],
                        [html_line_breaks(connector.type), html_line_breaks(connector.subtype), connector.color, '<!-- colorbar -->' if connector.color else None],
                        [html_line_breaks(connector.notes)]]
                html = nested_html_table(rows)

                if connector.color: # add color bar next to color info, if present
                    colorbar = f' bgcolor="{wv_colors.translate_color(connector.color, "HEX")}" width="4"></td>' # leave out '<td' from string to preserve any existing attributes of the <td> tag
                    html = html.replace('><!-- colorbar --></td>', colorbar)

                dot.node(key, label=f'<{html}>', shape='none', margin='0', style='filled', fillcolor='white')

            else:  # not a ferrule

                rows = [[connector.name if connector.show_name else None],
                        [connector.manufacturer,
                         f'MPN: {connector.manufacturer_part_number}' if connector.manufacturer_part_number else None,
                         f'IPN: {connector.internal_part_number}' if connector.internal_part_number else None],
                        [html_line_breaks(connector.type),
                         html_line_breaks(connector.subtype),
                         f'{connector.pincount}-pin' if connector.show_pincount else None],
                        '<!-- connector table -->',
                        [html_line_breaks(connector.notes)]]
                html = nested_html_table(rows)

                pinouts = []
                for pinnumber, pinname in zip(connector.pinnumbers, connector.pinout):
                    if connector.hide_disconnected_pins and not connector.visible_pins.get(pinnumber, False):
                        continue
                    pinouts.append([f'<td port="p{pinnumber}l">{pinnumber}</td>' if connector.ports_left else None,
                                    f'<td>{pinname}</td>' if pinname else '',
                                    f'<td port="p{pinnumber}r">{pinnumber}</td>' if connector.ports_right else None])

                pinhtml = '<table border="0" cellspacing="0" cellpadding="3" cellborder="1">'
                for i, pin in enumerate(pinouts):
                    pinhtml = f'{pinhtml}<tr>'
                    for column in pin:
                        if column is not None:
                            pinhtml = f'{pinhtml}{column}'
                    pinhtml = f'{pinhtml}</tr>'
                pinhtml = f'{pinhtml}</table>'
                html = html.replace('<!-- connector table -->', pinhtml)

                dot.node(key, label=f'<{html}>', shape='none', margin='0', style='filled', fillcolor='white')

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
                        dot.edge(f'{connector.name}:p{loop[0]}{loop_side}:{loop_dir}',
                                 f'{connector.name}:p{loop[1]}{loop_side}:{loop_dir}')

        for _, cable in self.cables.items():

            awg_fmt = ''
            if cable.show_equiv:
                # Only convert units we actually know about, i.e. currently
                # mm2 and awg --- other units _are_ technically allowed,
                # and passed through as-is.
                if cable.gauge_unit =='mm\u00B2':
                    awg_fmt = f' ({awg_equiv(cable.gauge)} AWG)'
                elif cable.gauge_unit.upper() == 'AWG':
                    awg_fmt = f' ({mm2_equiv(cable.gauge)} mm\u00B2)'

            identification = [cable.manufacturer if not isinstance(cable.manufacturer, list) else '',
                              f'MPN: {cable.manufacturer_part_number}' if (cable.manufacturer_part_number and not isinstance(cable.manufacturer_part_number, list)) else '',
                              f'IPN: {cable.internal_part_number}' if (cable.internal_part_number and not isinstance(cable.internal_part_number, list)) else '']
            identification = list(filter(None, identification))

            attributes = [html_line_breaks(cable.type) if cable.type else '',
                          f'{len(cable.colors)}x' if cable.show_wirecount else '',
                          f'{cable.gauge} {cable.gauge_unit}{awg_fmt}' if cable.gauge else '',
                          '+ S' if cable.shield else '',
                          f'{cable.length} m' if cable.length > 0 else '']
            attributes = list(filter(None, attributes))

            html = '<table border="0" cellspacing="0" cellpadding="0">'  # main table

            if cable.show_name or len(attributes) > 0:
                html = f'{html}<tr><td><table border="0" cellspacing="0" cellpadding="3" cellborder="1">'  # name+attributes table
                if cable.show_name:
                    html = f'{html}<tr><td colspan="{max(len(attributes), 1)}">{cable.name}</td></tr>'
                if(len(identification) > 0):  # print an identification row if values specified
                    html = f'{html}<tr><td colspan="{len(attributes)}" cellpadding="0"><table border="0" cellspacing="0" cellpadding="3" cellborder="1"><tr>'
                    for attrib in identification[0:-1]:
                        html = f'{html}<td sides="R">{attrib}</td>' # all columns except last have a border on the right (sides="R")
                    if len(identification) > 0:
                        html = f'{html}<td border="0">{identification[-1]}</td>' # last column has no border on the right because the enclosing table borders it
                    html = f'{html}</tr></table></td></tr>'  # end identification row
                if(len(attributes) > 0):
                    html = f'{html}<tr>'  # attribute row
                    for attrib in attributes:
                        html = f'{html}<td balign="left">{attrib}</td>'
                    html = f'{html}</tr>'  # attribute row
                html = f'{html}</table></td></tr>'  # name+attributes table

            html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer between attributes and wires

            html = f'{html}<tr><td><table border="0" cellspacing="0" cellborder="0">'  # conductor table

            # determine if there are double- or triple-colored wires;
            # if so, pad single-color wires to make all wires of equal thickness
            colorlengths = list(map(len, cable.colors))
            pad = 4 in colorlengths or 6 in colorlengths

            for i, connection_color in enumerate(cable.colors, 1):
                p = []
                p.append(f'<!-- {i}_in -->')
                p.append(wv_colors.translate_color(connection_color, self.color_mode))
                p.append(f'<!-- {i}_out -->')
                html = f'{html}<tr>'
                for bla in p:
                    html = f'{html}<td>{bla}</td>'
                html = f'{html}</tr>'

                bgcolors = ['#000000'] + get_color_hex(connection_color, pad=pad) + ['#000000']
                html = f'{html}<tr><td colspan="{len(p)}" border="0" cellspacing="0" cellpadding="0" port="w{i}" height="{(2 * len(bgcolors))}"><table cellspacing="0" cellborder="0" border = "0">'
                for j, bgcolor in enumerate(bgcolors[::-1]):  # Reverse to match the curved wires when more than 2 colors
                    html = f'{html}<tr><td colspan="{len(p)}" cellpadding="0" height="2" bgcolor="{bgcolor if bgcolor != "" else wv_colors.default_color}" border="0"></td></tr>'
                html = html + '</table></td></tr>'
                if(cable.category == 'bundle'):  # for bundles individual wires can have part information
                    # create a list of wire parameters
                    wireidentification = []
                    if isinstance(cable.manufacturer, list):
                        wireidentification.append(cable.manufacturer[i - 1])
                    if isinstance(cable.manufacturer_part_number, list):
                        wireidentification.append(f'MPN: {cable.manufacturer_part_number[i - 1]}')
                    if isinstance(cable.internal_part_number, list):
                        wireidentification.append(f'IPN: {cable.internal_part_number[i - 1]}')
                    # print parameters into a table row under the wire
                    if(len(wireidentification) > 0):
                        html = f'{html}<tr><td colspan="{len(p)}"><table border="0" cellspacing="0" cellborder="0"><tr>'
                        for attrib in wireidentification:
                            html = f'{html}<td>{attrib}</td>'
                        html = f'{html}</tr></table></td></tr>'

            if cable.shield:
                p = ['<!-- s_in -->', 'Shield', '<!-- s_out -->']
                html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer
                html = f'{html}<tr>'
                for bla in p:
                    html = html + f'<td>{bla}</td>'
                html = f'{html}</tr>'
                html = f'{html}<tr><td colspan="{len(p)}" cellpadding="0" height="6" border="2" sides="b" port="ws"></td></tr>'

            html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer at the end

            html = f'{html}</table>'  # conductor table

            html = f'{html}</td></tr>'  # main table
            if cable.notes:
                html = f'{html}<tr><td cellpadding="3" balign="left">{html_line_breaks(cable.notes)}</td></tr>'  # notes table
                html = f'{html}<tr><td>&nbsp;</td></tr>'  # spacer at the end

            html = f'{html}</table>'  # main table

            # connections
            for connection_color in cable.connections:
                if isinstance(connection_color.via_port, int):  # check if it's an actual wire and not a shield
                    dot.attr('edge', color=':'.join(['#000000'] + wv_colors.get_color_hex(cable.colors[connection_color.via_port - 1], pad=pad) + ['#000000']))
                else:  # it's a shield connection
                    # shield is shown as a thin tinned wire
                    dot.attr('edge', color=':'.join(['#000000', wv_colors.get_color_hex('SN', pad=False)[0], '#000000']))
                if connection_color.from_port is not None:  # connect to left
                    from_ferrule = self.connectors[connection_color.from_name].category == 'ferrule'
                    port = f':p{connection_color.from_port}r' if not from_ferrule else ''
                    code_left_1 = f'{connection_color.from_name}{port}:e'
                    code_left_2 = f'{cable.name}:w{connection_color.via_port}:w'
                    dot.edge(code_left_1, code_left_2)
                    from_string = f'{connection_color.from_name}:{connection_color.from_port}' if not from_ferrule else ''
                    html = html.replace(f'<!-- {connection_color.via_port}_in -->', from_string)
                if connection_color.to_port is not None:  # connect to right
                    to_ferrule = self.connectors[connection_color.to_name].category == 'ferrule'
                    code_right_1 = f'{cable.name}:w{connection_color.via_port}:e'
                    to_port = f':p{connection_color.to_port}l' if not to_ferrule else ''
                    code_right_2 = f'{connection_color.to_name}{to_port}:w'
                    dot.edge(code_right_1, code_right_2)
                    to_string = f'{connection_color.to_name}:{connection_color.to_port}' if not to_ferrule else ''
                    html = html.replace(f'<!-- {connection_color.via_port}_out -->', to_string)

            dot.node(cable.name, label=f'<{html}>', shape='box',
                     style='filled,dashed' if cable.category == 'bundle' else '', margin='0', fillcolor='white')

        return dot

    @property
    def png(self):
        from io import BytesIO
        graph = self.create_graph()
        data = BytesIO()
        data.write(graph.pipe(format='png'))
        data.seek(0)
        return data.read()

    @property
    def svg(self):
        from io import BytesIO
        graph = self.create_graph()
        data = BytesIO()
        data.write(graph.pipe(format='svg'))
        data.seek(0)
        return data.read()

    def output(self, filename: (str, Path), view: bool = False, cleanup: bool = True, fmt: tuple = ('pdf', )) -> None:
        # graphical output
        graph = self.create_graph()
        for f in fmt:
            graph.format = f
            graph.render(filename=filename, view=view, cleanup=cleanup)
        graph.save(filename=f'{filename}.gv')
        # bom output
        bom_list = self.bom_list()
        with open_file_write(f'{filename}.bom.tsv') as file:
            file.write(tuplelist2tsv(bom_list))
        # HTML output
        with open_file_write(f'{filename}.html') as file:
            file.write('<!DOCTYPE html>\n')
            file.write('<html><head><meta charset="UTF-8"></head><body style="font-family:Arial">')

            file.write('<h1>Diagram</h1>')
            with open_file_read(f'{filename}.svg') as svg:
                file.write(re.sub(
                    '^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>',
                    '<!-- XML and DOCTYPE declarations from SVG file removed -->',
                    svg.read(1024), 1))
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
                    file.write(f'<td {align} style="border:1px solid #000000; padding: 4px">{item}</td>')
                file.write('</tr>')
            file.write('</table>')

            file.write('</body></html>')

    def bom(self):
        bom = []
        bom_connectors = []
        bom_cables = []
        bom_extra = []
        # connectors
        connector_group = lambda c: (c.type, c.subtype, c.pincount, c.manufacturer, c.manufacturer_part_number, c.internal_part_number)
        for group in Counter([connector_group(v) for v in self.connectors.values()]):
            items = {k: v for k, v in self.connectors.items() if connector_group(v) == group}
            shared = next(iter(items.values()))
            designators = list(items.keys())
            designators.sort()
            conn_type = f', {remove_line_breaks(shared.type)}' if shared.type else ''
            conn_subtype = f', {remove_line_breaks(shared.subtype)}' if shared.subtype else ''
            conn_pincount = f', {shared.pincount} pins' if shared.category != 'ferrule' else ''
            conn_color = f', {shared.color}' if shared.color else ''
            name = f'Connector{conn_type}{conn_subtype}{conn_pincount}{conn_color}'
            item = {'item': name, 'qty': len(designators), 'unit': '', 'designators': designators if shared.category != 'ferrule' else '',
                    'manufacturer': shared.manufacturer, 'manufacturer part number': shared.manufacturer_part_number, 'internal part number': shared.internal_part_number}
            bom_connectors.append(item)
            bom_connectors = sorted(bom_connectors, key=lambda k: k['item'])  # https://stackoverflow.com/a/73050
        bom.extend(bom_connectors)
        # cables
        # TODO: If category can have other non-empty values than 'bundle', maybe it should be part of item name?
        # The category needs to be included in cable_group to keep the bundles excluded.
        cable_group = lambda c: (c.category, c.type, c.gauge, c.gauge_unit, c.wirecount, c.shield, c.manufacturer, c.manufacturer_part_number, c.internal_part_number)
        for group in Counter([cable_group(v) for v in self.cables.values() if v.category != 'bundle']):
            items = {k: v for k, v in self.cables.items() if cable_group(v) == group}
            shared = next(iter(items.values()))
            designators = list(items.keys())
            designators.sort()
            total_length = sum(i.length for i in items.values())
            cable_type = f', {remove_line_breaks(shared.type)}' if shared.type else ''
            gauge_name = f' x {shared.gauge} {shared.gauge_unit}' if shared.gauge else ' wires'
            shield_name = ' shielded' if shared.shield else ''
            name = f'Cable{cable_type}, {shared.wirecount}{gauge_name}{shield_name}'
            item = {'item': name, 'qty': round(total_length, 3), 'unit': 'm', 'designators': designators,
                    'manufacturer': shared.manufacturer, 'manufacturer part number': shared.manufacturer_part_number, 'internal part number': shared.internal_part_number}
            bom_cables.append(item)
        # bundles (ignores wirecount)
        wirelist = []
        # list all cables again, since bundles are represented as wires internally, with the category='bundle' set
        for bundle in self.cables.values():
            if bundle.category == 'bundle':
                # add each wire from each bundle to the wirelist
                for index, color in enumerate(bundle.colors, 0):
                    wirelist.append({'type': bundle.type, 'gauge': bundle.gauge, 'gauge_unit': bundle.gauge_unit, 'length': bundle.length, 'color': color, 'designator': bundle.name,
                                     'manufacturer': index_if_list(bundle.manufacturer, index),
                                     'manufacturer part number': index_if_list(bundle.manufacturer_part_number, index),
                                     'internal part number': index_if_list(bundle.internal_part_number, index)})
        # join similar wires from all the bundles to a single BOM item
        wire_group = lambda w: (w.get('type', None), w['gauge'], w['gauge_unit'], w['color'], w['manufacturer'], w['manufacturer part number'], w['internal part number'])
        for group in Counter([wire_group(v) for v in wirelist]):
            items = [v for v in wirelist if wire_group(v) == group]
            shared = items[0]
            designators = [i['designator'] for i in items]
            designators = list(dict.fromkeys(designators))  # remove duplicates
            designators.sort()
            total_length = sum(i['length'] for i in items)
            wire_type = f', {remove_line_breaks(shared["type"])}' if shared.get('type', None) else ''
            gauge_name = f', {shared["gauge"]} {shared["gauge_unit"]}' if shared.get('gauge', None) else ''
            gauge_color = f', {shared["color"]}' if 'color' in shared != '' else ''
            name = f'Wire{wire_type}{gauge_name}{gauge_color}'
            item = {'item': name, 'qty': round(total_length, 3), 'unit': 'm', 'designators': designators,
                    'manufacturer': shared['manufacturer'], 'manufacturer part number': shared['manufacturer part number'], 'internal part number': shared['internal part number']}
            bom_cables.append(item)
            bom_cables = sorted(bom_cables, key=lambda k: k['item'])  # sort list of dicts by their values (https://stackoverflow.com/a/73050)
        bom.extend(bom_cables)

        for item in self.additional_bom_items:
            name = item['description'] if item.get('description', None) else ''
            if isinstance(item.get('designators', None), List):
                item['designators'].sort()  # sort designators if a list is provided
            item = {'item': name, 'qty': item.get('qty', None), 'unit': item.get('unit', None), 'designators': item.get('designators', None),
                    'manufacturer': item.get('manufacturer', None), 'manufacturer part number': item.get('manufacturer_part_number', None), 'internal part number': item.get('internal_part_number', None)}
            bom_extra.append(item)
        bom_extra = sorted(bom_extra, key=lambda k: k['item'])
        bom.extend(bom_extra)
        return bom

    def bom_list(self):
        bom = self.bom()
        keys = ['item', 'qty', 'unit', 'designators'] # these BOM columns will always be included
        for fieldname in ['manufacturer', 'manufacturer part number', 'internal part number']: # these optional BOM columns will only be included if at least one BOM item actually uses them
            if any(fieldname in x and x.get(fieldname, None) for x in bom):
                keys.append(fieldname)
        bom_list = []
        bom_list.append([k.capitalize() for k in keys])  # create header row with keys
        for item in bom:
            item_list = [item.get(key, '') for key in keys]  # fill missing values with blanks
            item_list = [', '.join(subitem) if isinstance(subitem, List) else subitem for subitem in item_list]  # convert any lists into comma separated strings
            item_list = ['' if subitem is None else subitem for subitem in item_list]  # if a field is missing for some (but not all) BOM items
            bom_list.append(item_list)
        return bom_list
