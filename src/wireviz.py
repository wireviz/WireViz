
COLOR_CODES = {'DIN': ['WH','BN','GN','YE','GY','PK','BU','RD','BK','VT','GYPK','RDBU','WHGN','BNGN','WHYE','YEBN','WHGY','GYBN','WHPK','PKBN'],
               'IEC': ['BN','RD','OG','YE','GN','BU','VT','GY','WH','BK'],
               'BW':  ['BK','WH']}

# TODO: parse and render double-colored cables ('RDBU' etc)
color_hex = {
             'BK': '#000000',
             'WH': '#ffffff',
             'GY': '#808080',
             'PK': '#ff80c0',
             'RD': '#ff0000',
             'OG': '#ff8000',
             'YE': '#ffff00',
             'GN': '#00ff00',
             'TQ': '#00ffff',
             'BU': '#0000ff',
             'VT': '#8000ff',
             'BN': '#666600',
              }

color_full = {
             'BK': 'black',
             'WH': 'white',
             'GY': 'grey',
             'PK': 'pink',
             'RD': 'red',
             'OG': 'orange',
             'YE': 'yellow',
             'GN': 'green',
             'TQ': 'turquoise',
             'BU': 'blue',
             'VT': 'violet',
             'BN': 'brown',
}

color_ger = {
             'BK': 'sw',
             'WH': 'ws',
             'GY': 'gr',
             'PK': 'rs',
             'RD': 'rt',
             'OG': 'or',
             'YE': 'ge',
             'GN': 'gn',
             'TQ': 'tk',
             'BU': 'bl',
             'VT': 'vi',
             'BN': 'br',
}

class Harness:

    def __init__(self):
        self.color_mode = 'SHORT'
        self.objects = {}

    def add(self, object):
        self.objects[object.name] = object
        self.objects[object.name].color_mode = self.color_mode

    def graphviz(self, print_to_screen=False):
        with open('output/output.dot','w') as f:
            with open('input/header.dot','r') as infile:
                for line in infile:
                    f.write(line)
            f.write('\n\n')

            for o in self.objects:
                f.write(self.objects[o].graphviz() + '\n')

            f.write('\n\n')
            with open('input/footer.dot','r') as infile:
                for line in infile:
                    f.write(line)

        if print_to_screen == True:
            with open('output/output.dot','r') as f:
                for line in f:
                    print(line)

class Node:

    def __init__(self, name, type=None, gender=None, show_name=True, num_pins=None, pinout=None, ports_left=False, ports_right=False):
        self.name = name
        self.type = type
        self.gender = gender
        self.show_name = show_name
        self.ports_left = ports_left
        self.ports_right = ports_right
        self.loops = []
        self.color_mode = 'SHORT'

        if pinout is None:
            self.pinout = ('',) * num_pins
        else:
            if num_pins is None:
                if pinout is None:
                    raise Exception('Must provide num_pins or pinout')
                else:
                    self.pinout = pinout

    def loop(self, from_pin, to_pin, side=None):
        if self.ports_left == True and self.ports_right == False:
            loop_side = 'w' # west = left
        elif self.ports_left == False and self.ports_right == True:
            loop_side = 'e' # east = right
        elif self.ports_left == True and self.ports_right == True:
            if side == None:
                raise Exception('Must specify side of loop')
            else:
                loop_side = side
        self.loops.append((from_pin, to_pin, loop_side))

    def graphviz(self):
        s = ''
        # print header

        s = s + '{name}[label="'.format(name=self.name)

        if self.show_name == True:
            s = s + '{name} | '.format(name=self.name)

        s = s + '{'
        l = []
        if self.type is not None:
            l.append('{}'.format(self.type))
        if self.gender is not None:
            l.append('{}'.format(self.gender))
        l.append('{}-pin'.format(len(self.pinout)))
        if len(l) > 0:
            s = s + '|'.join(l)
        s = s + '} | '

        s = s + '{'
        # print pinout
        if self.ports_left == True:
            s = s + '{'
            l = []
            for i,x in enumerate(self.pinout,1):
                l.append('<p{portno}>{portno}'.format(portno=i))
            s = s + '|'.join(l)
            s = s + '} | '

        s = s + '{'
        s = s + '|'.join(self.pinout)
        s = s + '}'

        if self.ports_right == True:
            s = s + ' | {'
            l = []
            for i,x in enumerate(self.pinout,1):
                l.append('<p{portno}>{portno}'.format(portno=i))
            s = s + '|'.join(l)
            s = s + '}'

        s = s + '}}"]'

        # print loops
        if len(self.loops) > 0:
            s = s + '\n\n{edge[style=bold]\n'
            for x in self.loops:
                s = s + '{name}:p{port_from}:{loop_side} -- {name}:p{port_to}:{loop_side}\n'.format(name=self.name, port_from=x[0], port_to=x[1], loop_side=x[2])
            s = s + '}'

        s = s + '\n'
        return s

class Cable:

    def __init__(self, name, mm2=None, awg=None, show_equiv=False, length=0, show_name=False, show_pinout=False, num_wires=None, colors=None, color_code=None, shield=False):
        self.name = name
        if mm2 is not None and awg is not None:
            raise Exception('You cannot define both mm2 and awg!')
        self.mm2 = mm2
        self.awg = awg
        self.show_equiv = show_equiv
        self.length = length
        self.show_name = show_name
        self.show_pinout = show_pinout
        self.shield = shield
        self.connections = []
        self.color_mode = 'SHORT'
        if color_code is None and colors is None:
            self.colors = ('',) * num_wires
        else:
            if colors is None: # no custom color pallet was specified
                if num_wires is None:
                    raise Exception('Unknown number of wires')
                else:
                    if color_code is None:
                        raise Exception('No color code')
                    # choose color code
                    if color_code not in COLOR_CODES:
                        raise Exception('Unknown color code')
                    else:
                        cc = COLOR_CODES[color_code]
                n = num_wires
            else: # custom color pallet was specified
                cc = colors
                if num_wires is None: # assume number of wires = number of items in custom pallet
                    n = len(cc)
                else: # number of wires was specified
                    n = num_wires

            cc = tuple(cc)
            if n > len(cc):
                 m = num_wires // len(cc) + 1
                 cc = cc * int(m)
            self.colors = cc[:n]

    def connect(self, from_name, from_pin, via, to_name, to_pin):
        if from_pin == 'auto':
            from_pin = tuple(x+1 for x in range(len(self.colors)))
        if via == 'auto':
            via = tuple(x+1 for x in range(len(self.colors)))
        if to_pin == 'auto':
            to_pin = tuple(x+1 for x in range(len(self.colors)))
        if len(from_pin) != len(to_pin):
            raise Exception('from_pin must have the same number of elements as to_pin')
        for i, x in enumerate(from_pin):
            self.connections.append((from_name, from_pin[i], via[i], to_name, to_pin[i]))

    def connect_all_straight(self, from_name, to_name):
        self.connect(from_name, 'auto', 'auto', to_name, 'auto')

    def graphviz(self):
        s = ''
        # print header
        s = s + '{name}[label="'.format(name=self.name)

        if self.show_name == True:
            s = s + '{name} | '.format(name=self.name)

        #print parameters
        s = s + '{'
        l = []
        l.append('{}x'.format(len(self.colors)))
        if self.mm2 is not None:
            e = awg_equiv(self.mm2)
            es = ' ({} AWG)'.format(e) if e is not None else ''
            mm ='{} mm\u00B2{}'.format(self.mm2, es)
            l.append(mm)
        if self.awg is not None:
            l.append('{} AWG'.format(self.awg))
        if self.shield == True:
            l.append(' + S')
        if self.length > 0:
            l.append('{} m'.format(self.length))
        if len(l) > 0:
            s = s + '|'.join(l)
        s = s + '} | '

        s = s + '{'
        # print pinout
        if self.show_pinout:
            s = s + '{'
            l = []
            for i,x in enumerate(self.colors,1):
                l.append('<w{wireno}i>{wireno}'.format(wireno=i))
            s = s + '|'.join(l)
            if self.shield == True:
                s = s + '|<wsi>'
            s = s + '} | '

        s = s + '{'
        if self.show_pinout:
            s = s + '|'.join(self.colors)
            if self.shield == True:
                s = s + '|Shield'
        else:
            l = []
            for i,x in enumerate(self.colors,1):
                if x in color_full:
                    if self.color_mode == 'full':
                        x = color_full[x].lower()
                    elif self.color_mode == 'FULL':
                        x = color_hex[x].upper()
                    elif self.color_mode == 'hex':
                        x = color_hex[x].lower()
                    elif self.color_mode == 'HEX':
                        x = color_hex[x].upper()
                    elif self.color_mode == 'ger':
                        x = color_ger[x].lower()
                    elif self.color_mode == 'GER':
                        x = color_ger[x].upper()
                    elif self.color_mode == 'short':
                        x = x.lower()
                    elif self.color_mode == 'SHORT':
                        x = x.upper()
                    else:
                        raise Exception('Unknown color mode')
                else:
                    x = ''
                l.append('<w{wireno}>{wirecolor}'.format(wireno=i,wirecolor=x))
            s = s + '|'.join(l)
            if self.shield == True:
                s = s + '|<ws>Shield'
        s = s + '}'

        if self.show_pinout:
            s = s + ' | {'
            l = []
            for i,x in enumerate(self.colors,1):
                l.append('<w{wireno}o>{wireno}'.format(wireno=i))
            s = s + '|'.join(l)
            if self.shield == True:
                s = s + '|<wso>'
            s = s + '}'

        s = s + '}}"]'

        # print connections
        s = s + '\n\n{edge[style=bold]\n'
        for x in self.connections:
            s = s + '{'
            if isinstance(x[2], int):
                search_color = self.colors[x[2]-1]
                if search_color in color_hex:
                    s = s + 'edge[color="#000000:{wire_color}:#000000"] '.format(wire_color=color_hex[search_color])
            if x[1] is not None:
                t = '{from_name}:p{from_port} -- {via_name}:w{via_wire}{via_subport}; '.format(from_name=x[0],from_port=x[1],via_name=self.name, via_wire=x[2], via_subport='i' if self.show_pinout == True else '')
                s = s + t
            if x[4] is not None:
                t = '{via_name}:w{via_wire}{via_subport} -- {to_name}:p{to_port}'.format(via_name=self.name, via_wire=x[2],to_name=x[3],to_port=x[4], via_subport='o' if self.show_pinout == True else '')
                s = s + t
            s = s + '}\n'
        s = s + '}'

        return s

def awg_equiv(mm2):
    awg_equiv_table = {
                        '0.09': 28,
                        '0.14': 26,
                        '0.25': 24,
                        '0.34': 22,
                        '0.5': 21,
                        '0.75': 20,
                        '1': 18,
                        '1.5': 16,
                        '2.5': 14,
                        '4': 12,
                        '6': 10,
                        '10': 8,
                        '16': 6,
                        '25': 4,
                        }
    k = str(mm2)
    if k in awg_equiv_table:
        return awg_equiv_table[k]
    else:
        return None
