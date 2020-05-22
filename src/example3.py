from wireviz import Harness, Node, Cable

Harness = Harness()
Harness.color_mode = 'full'

Harness.add(Node('X1', num_pins=10, ports_right=True))
Harness.add(Node('X2', num_pins=10, ports_left=True))
Harness.add(Cable('W1', num_wires=10, color_code='IEC'))
Harness.objects['W1'].connect_all_straight('X1','X2')

Harness.add(Node('X3', num_pins=20, ports_right=True))
Harness.add(Node('X4', num_pins=20, ports_left=True))
Harness.add(Cable('W2', num_wires=20, color_code='DIN'))
Harness.objects['W2'].connect_all_straight('X3','X4')

Harness.graphviz()
