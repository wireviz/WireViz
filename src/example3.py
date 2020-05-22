from wireviz import Harness, Node, Cable

Harness = Harness()
Harness.color_mode = 'full'

Harness.add(Node('X1', num_pins=10, ports_right=True))
Harness.add(Node('X2', num_pins=10, ports_left=True))
Harness.add(Cable('W1', num_wires=10, color_code='IEC'))
Harness.objects['W1'].connect_all_straight('X1','X2')

Harness.add(Node('X3', num_pins=12, ports_right=True))
Harness.add(Node('X4', num_pins=12, ports_left=True))
Harness.add(Cable('W2', num_wires=12, color_code='DIN'))
Harness.objects['W2'].connect_all_straight('X3','X4')

Harness.add(Node('X5', num_pins=20, ports_right=True))
Harness.add(Node('X6', num_pins=20, ports_left=True))
Harness.add(Cable('W3', num_wires=20, colors=('RD','YE','BU')))
Harness.objects['W3'].connect_all_straight('X5','X6')

Harness.add(Node('X7', num_pins=6, ports_right=True))
Harness.add(Node('X8', num_pins=6, ports_left=True))
Harness.add(Cable('W4', num_wires=6, length=1, mm2=1))
Harness.objects['W4'].connect_all_straight('X7','X8')




Harness.graphviz()
