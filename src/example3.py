import wireviz

h = wireviz.Harness()
h.color_mode = 'full'

h.add_node('X1', num_pins=10, ports_right=True)
h.add_node('X2', num_pins=10, ports_left=True)
h.add_cable('W1', num_wires=10, color_code='IEC')
h.connect_all_straight('W1','X1','X2')

h.add_node('X3', num_pins=20, ports_right=True)
h.add_node('X4', num_pins=20, ports_left=True)
h.add_cable('W2', num_wires=20, color_code='DIN')
h.connect_all_straight('W2','X3','X4')

h.add_node('X5', num_pins=20, ports_right=True)
h.add_node('X6', num_pins=20, ports_left=True)
h.add_cable('W3', num_wires=20, colors=('RD','YE','BU'))
h.connect_all_straight('W3','X5','X6')

h.add_node('X7', num_pins=6, ports_right=True)
h.add_node('X8', num_pins=6, ports_left=True)
h.add_cable('W4', num_wires=6, length=1, mm2=1)
h.connect_all_straight('W4','X7','X8')

h.output('output/output', format='png', view=False)
