import wireviz

h = wireviz.Harness()

h.add_cable('W1', show_name=False, show_num_wires=False, num_wires=4, color_code='DIN')
h.add_cable('W2', show_name=False, show_num_wires=False, num_wires=4, color_code='DIN')
h.add_node('X1', num_pins=4, show_num_pins=False)
h.add_node('X2', num_pins=4, show_num_pins=False)
h.add_node('X3', num_pins=4, show_num_pins=False)
h.connect_all_straight('W1','X1','X2')
h.connect_all_straight('W2','X2','X3')

h.output(filename='output', format=('png','svg'), view=False)
