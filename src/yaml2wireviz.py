import yaml
import wireviz

filename = '../examples/example1.yml'
filename = '../examples/example2.yml'
filename = '../examples/ferrules.yml'
filename = '../examples/bundles.yml'

def check_designators(what, where):
    for i, x in enumerate(what):
        # print('Looking for {} in {}'.format(x,where[i]))
        if x not in input[where[i]]:
            return False
    return True

def expand(input):
    # input can be:
    # - a singleton (normally str or int)
    # - a list of str or int
    # if str is of the format '#-#', it is treated as a range (inclusive) and expanded
    output = []
    if not isinstance(input, list):
        input = [input,]
    for e in input:
        e = str(e)
        if '-' in e: # list of pins
            a, b = tuple(map(int, e.split('-')))
            if a < b:
                for x in range(a,b+1):
                    output.append(x)
            elif a > b:
                for x in range(a,b-1,-1):
                    output.append(x)
            elif a == b:
                output.append(a)
        else:
            try:
                x = int(e)
            except:
                x = e
            output.append(x)
    return output

with open(filename, 'r') as stream:
    try:
        input = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

h = wireviz.Harness()

# add items
sections = ['nodes','wires','ferrules','connections']
types    = [dict, dict, dict, list]
for sec, ty in zip(sections, types):
    if sec in input and type(input[sec]) == ty:
        if len(input[sec]) > 0:
            if ty == dict:
                for k, o in input[sec].items():
                    if sec == 'nodes':
                        h.add_node(name=k, **o)
                    elif sec == 'wires':
                        h.add_cable(name=k, **o)
                    elif sec == 'ferrules':
                        pass
        else:
            print('{} section empty'.format(sec))
    else:
        print('No {} section found'.format(sec))
        if ty == dict:
            input[sec] = {}
        elif ty == list:
            input[sec] = []

# add connections
ferrule_counter = 0
for con in input['connections']:
    if len(con) == 3: # format: connector -- wire -- conector

        for c in con:
            if len(list(c.keys())) != 1: # check that each entry in con has only one key, which is the designator
                raise Exception('Too many keys')

        from_name = list(con[0].keys())[0]
        via_name  = list(con[1].keys())[0]
        to_name   = list(con[2].keys())[0]

        if not check_designators([from_name,via_name,to_name],('nodes','wires','nodes')):
            raise Exception('Bad connection definition (3)')

        from_pins = expand(con[0][from_name])
        via_pins  = expand(con[1][via_name])
        to_pins   = expand(con[2][to_name])

        if len(from_pins) != len(via_pins) or len(via_pins) != len(to_pins):
            raise Exception('List length mismatch')

        for (from_pin, via_pin, to_pin) in zip(from_pins, via_pins, to_pins):
            h.connect(from_name, from_pin, via_name, via_pin, to_name, to_pin)

    elif len(con) == 2:

        for c in con:
            if type(c) is dict:
                if len(list(c.keys())) != 1: # check that each entry in con has only one key, which is the designator
                    raise Exception('Too many keys')

        # hack to make the format for ferrules compatible with the formats for connectors and wires
        if type(con[0]) == str:
            name = con[0]
            con[0] = {}
            con[0][name] = name
        if type(con[1]) == str:
            name = con[1]
            con[1] = {}
            con[1][name] = name

        from_name = list(con[0].keys())[0]
        to_name   = list(con[1].keys())[0]

        n_w = check_designators([from_name, to_name],('nodes','wires'))
        w_n = check_designators([from_name, to_name],('wires','nodes'))
        n_n = check_designators([from_name, to_name],('nodes','nodes'))


        f_w = check_designators([from_name, to_name],('ferrules','wires'))
        w_f = check_designators([from_name, to_name],('wires','ferrules'))

        if not n_w and not w_n and not n_n and not f_w and not w_f:
            raise Exception('Wrong designators')

        from_pins = expand(con[0][from_name])
        to_pins  = expand(con[1][to_name])

        if n_w or w_n or n_n:
            if len(from_pins) != len(to_pins):
                raise Exception('List length mismatch')

        if n_w or w_n:
            for (from_pin, to_pin) in zip(from_pins, to_pins):
                if n_w:
                    h.connect(from_name, from_pin, to_name, to_pin, None, None)
                else: # w_n
                    h.connect(None, None, from_name, from_pin, to_name, to_pin)
        elif n_n:
            con_name  = list(con[0].keys())[0]
            from_pins = expand(con[0][from_name])
            to_pins   = expand(con[1][to_name])

            for (from_pin, to_pin) in zip(from_pins, to_pins):
                h.loop(con_name, from_pin, to_pin)
        if f_w or w_f:
            from_pins = expand(con[0][from_name])
            to_pins   = expand(con[1][to_name])

            if f_w:
                ferrule_name = from_name
                wire_name = to_name
                wire_pins = to_pins
            else:
                ferrule_name = to_name
                wire_name = from_name
                wire_pins = from_pins

            ferrule_params = input['ferrules'][ferrule_name]
            for wire_pin in wire_pins:
                ferrule_counter = ferrule_counter + 1
                ferrule_id = 'F{}'.format(ferrule_counter)
                h.add_node(ferrule_id, **ferrule_params)

                if f_w:
                    h.connect(ferrule_id, 1, wire_name, wire_pin, None, None)
                else:
                    h.connect(None, None, wire_name, wire_pin, ferrule_id, 1)


    else:
        raise Exception('Wrong number of connection parameters')

h.output(filename='output', format=('png','svg'), view=False)
