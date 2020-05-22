
COLOR_CODE_DIN = ['WH','BN','GN','YE','GY','PK','BU','RD','BK','VT']
COLOR_CODE_IEC = ['BN','RD','OG','YE','GN','BU','VT','GY','WH','BK']

color_dict = {'BK': '#000000',
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
              'BN': '#808000',
              }

class Node:

    def __init__(self, name, num_pins=None, pinout=None, ports_left=False, ports_right=False):
        self.name = name
        self.ports_left = ports_left
        self.ports_right = ports_right
        self.loops = []

        if pinout is None:
            self.pinout = ("",) * num_pins
        else:
            if num_pins is None:
                if pinout is None:
                    raise Exception("Must provide num_pins or pinout")
                else:
                    self.pinout = pinout

    def loop(self, from_pin, to_pin, side=None):
        if self.ports_left == True and self.ports_right == False:
            loop_side = 'w' # west = left
        elif self.ports_left == False and self.ports_right == True:
            loop_side = 'e' # east = right
        elif self.ports_left == True and self.ports_right == True:
            if side == None:
                raise Exception("Must specify side of loop")
            else:
                loop_side = side
        self.loops.append((from_pin, to_pin, loop_side))

    def __repr__(self):
        return "{} = {} {}".format(self.name, len(self.pinout), self.pinout)

    def __str__(self):
        return "{}".format(self.name)

    def graphviz(self):
        s = ''
        # print header
        s = s + '{name}[label="{name} | {{'.format(name=self.name)
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
                s = s + '{name}:p{port_from}:{loop_side} -> {name}:p{port_to}:{loop_side}\n'.format(name=self.name, port_from=x[0], port_to=x[1], loop_side=x[2])
            s = s + '}'

        s = s + '\n'
        return s

class Cable:

    def __init__(self, name, num_wires=None, colors=None, color_code=None, shield=False):
        self.name = name
        self.connections = []
        if color_code is None and colors is None:
            self.colors = ("",) * num_wires
        else:
            if colors is None:
                if num_wires is None:
                    raise Exception("Unknown number of wires")
                else:
                    # TODO: Loop through colors if num_wires > len(COLOR_CODE_XXX)
                    if color_code == "DIN":
                        self.colors = tuple(COLOR_CODE_DIN[:num_wires])
                    elif color_code == "IEC":
                        self.colors = tuple(COLOR_CODE_IEC[:num_wires])
                    else:
                        raise Exception("Unknown color code")
            else:
                if num_wires is None:
                    self.colors = colors
                else:
                    self.colors = colors[:num_wires]
        if shield == True:
            self.colors = self.colors + ('Shield',)

    def connect(self, from_name, from_pin, via, to_name, to_pin):
        if len(from_pin) != len(to_pin):
            raise Exception("from_pin must have the same number of elements as to_pin")
        for i, x in enumerate(from_pin):
            self.connections.append((from_name, from_pin[i], via[i], to_name, to_pin[i]))

    def __repr__(self):
        return "{} = {} {}\n     {}".format(self.name, len(self.colors), self.colors, self.connections)

    def debug(self):
        print(self.name)
        print(self.colors)
        if len(self.connections) > 0:
            for i, x in enumerate(self.connections):
                if i < len(self.colors):
                    s = self.colors[int(x[2]-1)]
                else:
                    s = '--'
                # print(self.colors(x[2]) if i < len(self.colors) else '-')
                print("{}:{} -- {}({}) -> {}:{}".format(x[0],x[1],x[2],s,x[3],x[4]))

    def graphviz(self):
        s = ''
        # print header
        s = s + '{name}[label="{name} | {{'.format(name=self.name)
        # print pinout
        s = s + '{'
        l = []
        for i,x in enumerate(self.colors,1):
            l.append('<w{wireno}i>{wireno}'.format(wireno=i))
        s = s + '|'.join(l)
        s = s + '} | '

        s = s + '{'
        s = s + '|'.join(self.colors)
        s = s + '}'

        s = s + ' | {'
        l = []
        for i,x in enumerate(self.colors,1):
            l.append('<w{wireno}o>{wireno}'.format(wireno=i))
        s = s + '|'.join(l)
        s = s + '}'

        s = s + '}}"]'

        s = s + '\n\n{edge[style=bold]\n'
        for x in self.connections:
            s = s + '{'
            search_color = self.colors[x[2]-1]
            if search_color in color_dict:
                s = s + 'edge[color="#000000:{wire_color}:#000000"] '.format(wire_color=color_dict[search_color])
            t = '{from_name}:p{from_port} -> {via_name}:w{via_wire}i; {via_name}:w{via_wire}o -> {to_name}:p{to_port}'.format(from_name=x[0],from_port=x[1],via_name=self.name, via_wire=x[2],to_name=x[3],to_port=x[4])
            s = s + t
            s = s + '}\n'
        s = s + '}'

        return s
