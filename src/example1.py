import wireviz

X1 = wireviz.Node('X1', type='D-Sub', gender='female', pinout=('DCD','RX','TX','DTR','GND','DSR','RTS','CTS','RI'), ports_right=True)
X2 = wireviz.Node('X2', type='Molex KK 254', gender='female', pinout=('GND','RX','TX','NC','OUT','IN'), ports_left=True)
W1 = wireviz.Cable('W1', mm2=0.25, length=0.2, show_name=True, show_pinout=True, num_wires=3, color_code='DIN', shield=True)
# Option 1: define wires and shield in one line
# W1.connect(X1,(5,2,3,5),(1,2,3,'s'),X2,(1,3,2,None))
# Option 2: define wires and shield separately
W1.connect(X1,(5,2,3),'auto',X2,(1,3,2)) # wires
W1.connect(X1,(5,),('s',),X2,(None,))    # shield
X2.loop(5,6)
objects = [X1, X2, W1]

wireviz.output(objects)
