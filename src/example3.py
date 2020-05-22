import wireviz

wireviz.color_mode = 'full' # short/SHORT/full/FULL/hex/HEX

X1 = wireviz.Node('X1', num_pins=10, ports_right=True)
X2 = wireviz.Node('X2', num_pins=10, ports_left=True)
W1 = wireviz.Cable('W1', num_wires=10, color_code='IEC')
W1.connect_all_straight(X1,X2)
X3 = wireviz.Node('X3', num_pins=10, ports_right=True)
X4 = wireviz.Node('X4', num_pins=10, ports_left=True)
W2 = wireviz.Cable('W2', num_wires=10, color_code='DIN')
W2.connect_all_straight(X3,X4)
objects = [X1, X2, W1, X3, X4, W2]

wireviz.output(objects)
