#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import sys
from typing import Any, Tuple

import click
import yaml

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


from wireviz.Harness import Harness
from wireviz.wv_helper import expand, open_file_read


def parse(yaml_input: str, file_out: (str, Path) = None, return_types: (None, str, Tuple[str]) = None) -> Any:
    """
    Parses yaml input string and does the high-level harness conversion

    :param yaml_input: a string containing the yaml input data
    :param file_out:
    :param return_types: if None, then returns None; if the value is a string, then a
        corresponding data format will be returned; if the value is a tuple of strings,
        then for every valid format in the `return_types` tuple, another return type
        will be generated and returned in the same order; currently supports:
         - "png" - will return the PNG data
         - "svg" - will return the SVG data
         - "harness" - will return the `Harness` instance
    """

    yaml_data = yaml.safe_load(yaml_input)

    harness = Harness()

    # add items
    sections = ['connectors', 'cables', 'connections']
    types = [dict, dict, list]
    for sec, ty in zip(sections, types):
        if sec in yaml_data and type(yaml_data[sec]) == ty:
            if len(yaml_data[sec]) > 0:
                if ty == dict:
                    for key, attribs in yaml_data[sec].items():
                        if sec == 'connectors':
                            if not attribs.get('autogenerate', False):
                                harness.add_connector(name=key, **attribs)
                        elif sec == 'cables':
                            harness.add_cable(name=key, **attribs)
            else:
                pass  # section exists but is empty
        else:  # section does not exist, create empty section
            if ty == dict:
                yaml_data[sec] = {}
            elif ty == list:
                yaml_data[sec] = []

    # add connections
    def check_designators(what, where): # helper function
        for i, x in enumerate(what):
            if x not in yaml_data[where[i]]:
                return False
        return True

    autogenerated_ids = {}
    for connection in yaml_data['connections']:
        # find first component (potentially nested inside list or dict)
        first_item = connection[0]
        if isinstance(first_item, list):
            first_item = first_item[0]
        elif isinstance(first_item, dict):
            first_item = list(first_item.keys())[0]
        elif isinstance(first_item, str):
            pass

        # check which section the first item belongs to
        alternating_sections = ['connectors','cables']
        for index, section in enumerate(alternating_sections):
            if first_item in yaml_data[section]:
                expected_index = index
                break
        else:
            raise Exception('First item not found anywhere.')
        expected_index = 1 - expected_index  # flip once since it is flipped back at the *beginning* of every loop

        # check that all iterable items (lists and dicts) are the same length
        # and that they are alternating between connectors and cables/bundles, starting with either
        itemcount = None
        for item in connection:
            expected_index = 1 - expected_index  # make sure items alternate between connectors and cables
            expected_section = alternating_sections[expected_index]
            if isinstance(item, list):
                itemcount_new = len(item)
                for subitem in item:
                    if not subitem in yaml_data[expected_section]:
                        raise Exception(f'{subitem} is not in {expected_section}')
            elif isinstance(item, dict):
                if len(item.keys()) != 1:
                    raise Exception('Dicts may contain only one key here!')
                itemcount_new = len(expand(list(item.values())[0]))
                subitem = list(item.keys())[0]
                if not subitem in yaml_data[expected_section]:
                    raise Exception(f'{subitem} is not in {expected_section}')
            elif isinstance(item, str):
                if not item in yaml_data[expected_section]:
                    raise Exception(f'{item} is not in {expected_section}')
                continue
            if itemcount is not None and itemcount_new != itemcount:
                raise Exception('All lists and dict lists must be the same length!')
            itemcount = itemcount_new
        if itemcount is None:
            raise Exception('No item revealed the number of connections to make!')

        # populate connection list
        connection_list = []
        for i, item in enumerate(connection):
            if isinstance(item, str):  # one single-pin component was specified
                sublist = []
                for i in range(1, itemcount + 1):
                    if yaml_data['connectors'][item].get('autogenerate'):
                        autogenerated_ids[item] = autogenerated_ids.get(item, 0) + 1
                        new_id = f'_{item}_{autogenerated_ids[item]}'
                        harness.add_connector(new_id, **yaml_data['connectors'][item])
                        sublist.append([new_id, 1])
                    else:
                        sublist.append([item, 1])
                connection_list.append(sublist)
            elif isinstance(item, list):  # a list of single-pin components were specified
                sublist = []
                for subitem in item:
                    if yaml_data['connectors'][subitem].get('autogenerate'):
                        autogenerated_ids[subitem] = autogenerated_ids.get(subitem, 0) + 1
                        new_id = f'_{subitem}_{autogenerated_ids[subitem]}'
                        harness.add_connector(new_id, **yaml_data['connectors'][subitem])
                        sublist.append([new_id, 1])
                    else:
                        sublist.append([subitem, 1])
                connection_list.append(sublist)
            elif isinstance(item, dict):  # a component with multiple pins was specified
                sublist = []
                id = list(item.keys())[0]
                pins = expand(list(item.values())[0])
                for pin in pins:
                    sublist.append([id, pin])
                connection_list.append(sublist)
            else:
                raise Exception('Unexpected item in connection list')

        # actually connect components using connection list
        for i, item in enumerate(connection_list):
            id = item[0][0]  # TODO: make more elegant/robust/pythonic
            if id in harness.cables:
                for j, con in enumerate(item):
                    if i == 0:  # list started with a cable, no connector to join on left side
                        from_name = None
                        from_pin  = None
                    else:
                        from_name = connection_list[i-1][j][0]
                        from_pin  = connection_list[i-1][j][1]
                    via_name  = item[j][0]
                    via_pin   = item[j][1]
                    if i == len(connection_list) - 1:  # list ends with a cable, no connector to join on right side
                        to_name   = None
                        to_pin    = None
                    else:
                        to_name   = connection_list[i+1][j][0]
                        to_pin    = connection_list[i+1][j][1]
                    harness.connect(from_name, from_pin, via_name, via_pin, to_name, to_pin)

    if "additional_bom_items" in yaml_data:
        for line in yaml_data["additional_bom_items"]:
            harness.add_bom_item(line)

    if file_out is not None:
        harness.output(filename=file_out, fmt=('png', 'svg'), view=False)

    if return_types is not None:
        returns = []
        if isinstance(return_types, str): # only one return type speficied
            return_types = [return_types]

        return_types = [t.lower() for t in return_types]

        for rt in return_types:
            if rt == 'png':
                returns.append(harness.png)
            if rt == 'svg':
                returns.append(harness.svg)
            if rt == 'harness':
                returns.append(harness)

        return tuple(returns) if len(returns) != 1 else returns[0]


def parse_file(yaml_file: str, file_out: (str, Path) = None) -> None:
    with open_file_read(yaml_file) as file:
        yaml_input = file.read()

    if not file_out:
        fn, fext = os.path.splitext(yaml_file)
        file_out = fn
    file_out = os.path.abspath(file_out)

    parse(yaml_input, file_out=file_out)


@click.command()
@click.argument('input_file', required=True)
@click.option('--prepend', '-p', default=None, help='a YAML file containing a library of templates and parts that may be referenced in the `input_file`')
@click.option('--out_types', '-o', multiple=True, default=['png'], help='the output formats to be generated')
def main(input_file, prepend, out_types):
    if not os.path.exists(input_file):
        print(f'Error: input file {input_file} inaccessible or does not exist, check path')
        sys.exit(1)

    with open_file_read(input_file) as fh:
        yaml_input = fh.read()

    if prepend:
        if not os.path.exists(prepend):
            print(f'Error: prepend input file {prepend} inaccessible or does not exist, check path')
            sys.exit(1)
        with open_file_read(prepend) as fh:
            prepend = fh.read()
            yaml_input = prepend + yaml_input

    input_file = Path(input_file)
    base_file_name = input_file.name.replace(input_file.suffix, '')

    # the parse function may return a single instance or a tuple, thus, the
    # if/then determines if there is only one thing that must be saved or multiple
    filedatas = parse(yaml_input, return_types=out_types)
    if isinstance(filedatas, tuple):
        for ext, data in zip(out_types, filedatas):
            fname = f'{base_file_name}.{ext}'
            with open(fname, 'wb') as f:
                f.write(data)
    else:
        ext = out_types[0]
        data = filedatas
        fname = f'{base_file_name}.{ext}'
        with open(fname, 'wb') as f:
            f.write(data)


if __name__ == '__main__':
    main()
