import yaml
import wireviz

filename = 'example1.yml'

def check_designators(what, where):
    for i,x in enumerate(what):
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
# add nodes
for k, o in input['nodes'].items():
    h.add_node(k, type=o.get('type'),
                  gender=o.get('gender'),
                  num_pins=o.get('num_pins'),
                  pinout=o.get('pinout'))
# add wires
for k, o in input['wires'].items():
    h.add_cable(k, mm2=o.get('mm2'),
                   awg=o.get('awg'),
                   length=o.get('length'),
                   num_wires=o.get('num_wires'),
                   colors=o.get('colors'),
                   color_code=o.get('color_code'),
                   shield=o.get('shield'))
# add connections
conlist = input['connections']
for con in conlist:
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
            if len(list(c.keys())) != 1: # check that each entry in con has only one key, which is the designator
                raise Exception('Too many keys')

        from_name = list(con[0].keys())[0]
        to_name = list(con[1].keys())[0]

        n_w = check_designators([from_name, to_name],('nodes','wires'))
        w_n = check_designators([from_name, to_name],('wires','nodes'))
        n_n = check_designators([from_name, to_name],('nodes','nodes'))

        if not n_w and not w_n and not n_n:
            raise Exception('Wrong designators')

        from_pins = expand(con[0][from_name])
        to_pins  = expand(con[1][to_name])

        if len(from_pins) != len(to_pins):
            raise Exception('List length mismatch')

        if n_w == True or w_n == True:
            for (from_pin, to_pin) in zip(from_pins, to_pins):
                if n_w:
                    h.connect(from_name, from_pin, to_name, to_pin, None, None)
                else: # w_n
                    h.connect(None, None, from_name, from_pin, to_name, to_pin)
        elif n_n == True:
            con_name  = list(con[0].keys())[0]
            from_pins = expand(con[0][from_name])
            to_pins   = expand(con[1][to_name])

            for (from_pin, to_pin) in zip(from_pins, to_pins):
                h.loop(con_name, from_pin, to_pin)
    else:
        raise Exception('Wrong number of connection parameters')

h.output(filename='output', format=('png',), view=False)
