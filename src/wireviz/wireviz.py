#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

import yaml

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wireviz.Harness import Harness


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
                    for key, o in yaml_data[sec].items():
                        if sec == 'connectors':
                            harness.add_connector(name=key, **o)
                        elif sec == 'cables':
                            harness.add_cable(name=key, **o)
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
    for connections in yaml_data['connections']:
        if len(connections) == 3:  # format: connector -- cable -- connector

            for connection in connections:
                if len(list(connection.keys())) != 1:  # check that each entry in con has only one key, which is the designator
                    raise Exception('Too many keys')

            from_name = list(connections[0].keys())[0]
            via_name = list(connections[1].keys())[0]
            to_name = list(connections[2].keys())[0]

            if not check_designators([from_name, via_name, to_name], ('connectors', 'cables', 'connectors')):
                print([from_name, via_name, to_name])
                raise Exception('Bad connection definition (3)')

            from_pins = expand(connections[0][from_name])
            via_pins = expand(connections[1][via_name])
            to_pins = expand(connections[2][to_name])

            if len(from_pins) != len(via_pins) or len(via_pins) != len(to_pins):
                raise Exception('List length mismatch')

            for (from_pin, via_pin, to_pin) in zip(from_pins, via_pins, to_pins):
                harness.connect(from_name, from_pin, via_name, via_pin, to_name, to_pin)

        elif len(connections) == 2:

            for connection in connections:
                if type(connection) is dict:
                    if len(list(connection.keys())) != 1:  # check that each entry in con has only one key, which is the designator
                        raise Exception('Too many keys')

            # hack to make the format for ferrules compatible with the formats for connectors and cables
            if type(connections[0]) == str:
                name = connections[0]
                connections[0] = {}
                connections[0][name] = name
            if type(connections[1]) == str:
                name = connections[1]
                connections[1] = {}
                connections[1][name] = name

            from_name = list(connections[0].keys())[0]
            to_name = list(connections[1].keys())[0]

            con_cbl = check_designators([from_name, to_name], ('connectors', 'cables'))
            cbl_con = check_designators([from_name, to_name], ('cables', 'connectors'))
            con_con = check_designators([from_name, to_name], ('connectors', 'connectors'))

            fer_cbl = check_designators([from_name, to_name], ('ferrules', 'cables'))
            cbl_fer = check_designators([from_name, to_name], ('cables', 'ferrules'))

            if not con_cbl and not cbl_con and not con_con and not fer_cbl and not cbl_fer:
                raise Exception('Wrong designators')

            from_pins = expand(connections[0][from_name])
            to_pins = expand(connections[1][to_name])

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
                cocon_coname = list(connections[0].keys())[0]
                from_pins = expand(connections[0][from_name])
                to_pins = expand(connections[1][to_name])

                for (from_pin, to_pin) in zip(from_pins, to_pins):
                    harness.loop(cocon_coname, from_pin, to_pin)
            if fer_cbl or cbl_fer:
                from_pins = expand(connections[0][from_name])
                to_pins = expand(connections[1][to_name])

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

    harness.output(filename=file_out, fmt=('png', 'svg'), gen_bom=generate_bom, view=False)


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
