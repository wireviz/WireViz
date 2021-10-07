#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import sys
from typing import Any, Tuple

import yaml

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent))  # add src/wireviz to PATH

from wireviz import __version__
from wireviz.DataClasses import Metadata, Options, Tweak
from wireviz.Harness import Harness
from wireviz.wv_helper import expand, get_single_key_and_value, is_arrow, open_file_read


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


    # define variables =========================================================
    # containers for parsed component data and connection sets
    template_connectors = {}
    template_cables     = {}
    connection_sets     = []
    # actual harness
    harness = Harness(
        metadata = Metadata(**yaml_data.get('metadata', {})),
        options = Options(**yaml_data.get('options', {})),
        tweak = Tweak(**yaml_data.get('tweak', {})),
    )
    # others
    designators_and_templates = {}  # store mapping of components to their respective template
    autogenerated_designators = {}  # keep track of auto-generated designators to avoid duplicates

    if 'title' not in harness.metadata:
        if file_out is None:
            harness.metadata['title'] = "WireViz diagram and BOM"
        else:
            harness.metadata['title'] = Path(file_out).stem

    # add items
    # parse YAML input file ====================================================

    sections = ['connectors', 'cables', 'connections']
    types = [dict, dict, list]
    for sec, ty in zip(sections, types):
        if sec in yaml_data and type(yaml_data[sec]) == ty:  # section exists
            if len(yaml_data[sec]) > 0:  # section has contents
                if ty == dict:
                    for key, attribs in yaml_data[sec].items():
                        # The Image dataclass might need to open an image file with a relative path.
                        image = attribs.get('image')
                        if isinstance(image, dict):
                            image['gv_dir'] = Path(file_out if file_out else '').parent # Inject context

                        # store component templates only; do not generate instances yet
                        if sec == 'connectors':
                            template_connectors[key] = attribs
                        elif sec == 'cables':
                            template_cables[key] = attribs
            else:  # section exists but is empty
                pass
        else:  # section does not exist, create empty section
            if ty == dict:
                yaml_data[sec] = {}
            elif ty == list:
                yaml_data[sec] = []

    connection_sets = yaml_data['connections']

    # go through connection sets, generate and connect components ==============

    template_separator_char = '.'  # TODO: make user-configurable (in case user wants to use `.` as part of their template/component names)

    def resolve_designator(inp, separator):
        if separator in inp:  # generate a new instance of an item
            if inp.count(separator) > 1:
                raise Exception(f'{inp} - Found more than one separator ({separator})')
            template, designator = inp.split(separator)
            if designator == '':
                autogenerated_designators[template] = autogenerated_designators.get(template, 0) + 1
                designator = f'__{template}_{autogenerated_designators[template]}'
            # check if redefining existing component to different template
            if designator in designators_and_templates:
                if designators_and_templates[designator] != template:
                    raise Exception(f'Trying to redefine {designator} from {designators_and_templates[designator]} to {template}')
            else:
                designators_and_templates[designator] = template
        else:
            template, designator = (inp, inp)
            if designator in designators_and_templates:
                pass  # referencing an exiting connector, no need to add again
            else:
                designators_and_templates[designator] = template
        return (template, designator)

    # utilities to check for alternating connectors and cables/arrows ==========

    alternating_types = ['connector','cable/arrow']
    expected_type = None

    def check_type(designator, template, actual_type):
        nonlocal expected_type
        if not expected_type:  # each connection set may start with either section
            expected_type = actual_type

        if actual_type != expected_type:  # did not alternate
            raise Exception(f'Expected {expected_type}, but "{designator}" ("{template}") is {actual_type}')

    def alternate_type():  # flip between connector and cable/arrow
        nonlocal expected_type
        expected_type = alternating_types[1 - alternating_types.index(expected_type)]

    for connection_set in connection_sets:

        # figure out number of parallel connections within this set
        connectioncount = []
        for entry in connection_set:
            if isinstance(entry, list):
                connectioncount.append(len(entry))
            elif isinstance(entry, dict):
                connectioncount.append(len(expand(list(entry.values())[0])))  # - X1: [1-4,6] yields 5
            else:
                pass # strings do not reveal connectioncount
        if not any(connectioncount):
            # no item in the list revealed connection count;
            # assume connection count is 1
            connectioncount = [1]
            # Example: The following is a valid connection set,
            #          even though no item reveals the connection count;
            #          the count is not needed because only a component-level mate happens.
            # -
            #   - CONNECTOR
            #   - ==>
            #   - CONNECTOR

        # check that all entries are the same length
        if len(set(connectioncount)) > 1:
            raise Exception('All items in connection set must reference the same number of connections')
        # all entries are the same length, connection count is set
        connectioncount = connectioncount[0]

        # expand string entries to list entries of correct length
        for index, entry in enumerate(connection_set):
            if isinstance(entry, str):
                connection_set[index] = [entry] * connectioncount

        # resolve all designators
        for index, entry in enumerate(connection_set):
            if isinstance(entry, list):
                for subindex, item in enumerate(entry):
                    template, designator = resolve_designator(item, template_separator_char)
                    connection_set[index][subindex] = designator
            elif isinstance(entry, dict):
                key = list(entry.keys())[0]
                template, designator = resolve_designator(key, template_separator_char)
                value = entry[key]
                connection_set[index] = {designator: value}
            else:
                pass  # string entries have been expanded in previous step

        # expand all pin lists
        for index, entry in enumerate(connection_set):
            if isinstance(entry, list):
                connection_set[index] = [{designator: 1} for designator in entry]
            elif isinstance(entry, dict):
                designator = list(entry.keys())[0]
                pinlist = expand(entry[designator])
                connection_set[index] = [{designator: pin} for pin in pinlist]
            else:
                pass  # string entries have been expanded in previous step

        # Populate wiring harness ==============================================

        expected_type = None  # reset check for alternating types
                              # at the beginning of every connection set
                              # since each set may begin with either type

        # generate components
        for entry in connection_set:
            for item in entry:
                designator = list(item.keys())[0]
                template = designators_and_templates[designator]

                if designator in harness.connectors:  # existing connector instance
                    check_type(designator, template, 'connector')
                elif template in template_connectors.keys():  # generate new connector instance from template
                    check_type(designator, template, 'connector')
                    harness.add_connector(name = designator, **template_connectors[template])

                elif designator in harness.cables:  # existing cable instance
                    check_type(designator, template, 'cable/arrow')
                elif template in template_cables.keys():  # generate new cable instance from template
                    check_type(designator, template, 'cable/arrow')
                    harness.add_cable(name = designator, **template_cables[template])

                elif is_arrow(designator):
                    check_type(designator, template, 'cable/arrow')
                    # arrows do not need to be generated here
                else:
                    raise Exception(f'{template} is an unknown template/designator/arrow.')

            alternate_type()  # entries in connection set must alternate between connectors and cables/arrows

        # transpose connection set list
        # before: one item per component, one subitem per connection in set
        # after:  one item per connection in set, one subitem per component
        connection_set = list(map(list, zip(*connection_set)))

        # connect components
        for index_entry, entry in enumerate(connection_set):
            for index_item, item in enumerate(entry):
                designator = list(item.keys())[0]

                if designator in harness.cables:
                    if index_item == 0:  # list started with a cable, no connector to join on left side
                        from_name, from_pin = (None, None)
                    else:
                        from_name, from_pin = get_single_key_and_value(entry[index_item-1])
                    via_name, via_pin = (designator, item[designator])
                    if index_item == len(entry) - 1:  # list ends with a cable, no connector to join on right side
                        to_name, to_pin = (None, None)
                    else:
                        to_name, to_pin = get_single_key_and_value(entry[index_item+1])
                    harness.connect(from_name, from_pin, via_name, via_pin, to_name, to_pin)

                elif is_arrow(designator):
                    if index_item == 0:  # list starts with an arrow
                        raise Exception('An arrow cannot be at the start of a connection set')
                    elif index_item == len(entry) - 1:  # list ends with an arrow
                        raise Exception('An arrow cannot be at the end of a connection set')

# self.connectors[from_name].pins.index(from_pin)
                    # import pudb; pu.db
                    from_name, from_pin = get_single_key_and_value(entry[index_item-1])
                    via_name,  via_pin  = (designator, None)
                    to_name,   to_pin   = get_single_key_and_value(entry[index_item+1])
                    if '-' in designator:  # mate pin by pin
                        harness.add_mate_pin(from_name, from_pin, to_name, to_pin, designator)
                    elif '=' in designator and index_entry == 0:  # mate two connectors as a whole
                        harness.add_mate_component(from_name, to_name, designator)

    # harness population completed =============================================

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
    yaml_file = Path(yaml_file)
    with open_file_read(yaml_file) as file:
        yaml_input = file.read()

    if file_out:
        file_out = Path(file_out)
    else:
        file_out = yaml_file.parent / yaml_file.stem
    file_out = file_out.resolve()

    parse(yaml_input, file_out=file_out)


def parse_cmdline():
    parser = argparse.ArgumentParser(
        description='Generate cable and wiring harness documentation from YAML descriptions',
    )
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('input_file', action='store', type=str, metavar='YAML_FILE')
    parser.add_argument('-o', '--output_file', action='store', type=str, metavar='OUTPUT')
    # Not implemented: parser.add_argument('--generate-bom', action='store_true', default=True)
    parser.add_argument('--prepend-file', action='store', type=str, metavar='YAML_FILE')
    return parser.parse_args()


def main():

    args = parse_cmdline()

    file_in = Path(args.input_file)

    if not file_in.exists():
        print(f'Error: input file {file_in} inaccessible or does not exist, check path')
        sys.exit(1)

    with open_file_read(file_in) as fh:
        yaml_input = fh.read()

    if args.prepend_file:
        if not Path(args.prepend_file).exists():
            print(f'Error: prepend input file {args.prepend_file} inaccessible or does not exist, check path')
            sys.exit(1)
        with open_file_read(args.prepend_file) as fh:
            prepend = fh.read()
            yaml_input = prepend + yaml_input

    if not args.output_file:
        file_out = file_in.parent / file_in.stem  # extension will be added by graphviz output function
    else:
        file_out = Path(args.output_file)
    file_out = file_out.resolve()

    parse(yaml_input, file_out=file_out)


if __name__ == '__main__':
    main()
