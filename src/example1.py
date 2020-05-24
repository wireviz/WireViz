import wireviz

h = wireviz.Harness()

h.add_cable('W1', mm2=0.25, length=0.2, show_name=True, show_pinout=True, num_wires=3, color_code='DIN', shield=True)
h.add_node('X1', type='D-Sub', gender='female', pinout=('DCD','RX','TX','DTR','GND','DSR','RTS','CTS','RI'))
h.add_node('X2', type='Molex KK 254', gender='female', pinout=('GND','RX','TX','NC','OUT','IN'))
# Option 1: define wires and shield in one line
h.connect('W1','X1',(5,2,3,5),(1,2,3,'s'),'X2',(1,3,2,None))
h.loop('X2', 5, 6)
# Option 2: define wires and shield separately
# Harness.objects['W1'].connect('X1',(5,2,3),'auto','X2',(1,3,2)) # wires
# Harness.objects['W1'].connect('X1',(5,),('s',),'X2',(None,))    # shield

h.output(filename='output', format=('png','svg'), view=False)
