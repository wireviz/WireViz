
COLOR_CODE_DIN = ['WH','BN','GN','YE','GY','PK','BU','RD','BK','VT']
COLOR_CODE_IEC = ['BN','RD','OG','YE','GN','BU','VT','GY','WH','BK']

class Node:

    def __init__(self, name, num_pins=None, pinout=None):
        self.name = name

        if pinout is None:
            self.pinout = ("",) * num_pins
        else:
            if num_pins is None:
                if pinout is None:
                    raise Exception("Must provide num_pins or pinout")
                else:
                    self.pinout = pinout

    def __repr__(self):
        return "{} = {} {}".format(self.name, len(self.pinout), self.pinout)

class Cable:

    def __init__(self, name, num_wires=None, colors=None, color_code=None):
        self.name = name
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

    def __repr__(self):
        return "{} = {} {}".format(self.name, len(self.colors), self.colors)



# class ClassName(object):
#     """docstring for ."""
#
#     def __init__(self, arg):
#         super(, self).__init__()
#         self.arg = arg
