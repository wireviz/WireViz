from wireviz import Harness, Node, Cable

# shortcuts for use during harness creation
PINOUT_I2C = ('GND','+5V','SCL','SDA')
COLORS_I2C = ('BK', 'RD', 'YE', 'GN')
PINOUT_SPI_DATAONLY = ('MISO','MOSI','SCK')

Harness = Harness()

Harness.add(Node('X1',type='Molex KK 254', gender='female',  pinout=('GND',
                                                                     '+5V',
                                                                     'SCL',
                                                                     'SDA',
                                                                     'MISO',
                                                                     'MOSI',
                                                                     'SCK',
                                                                     'N/C'), ports_right=True))
Harness.add(Node('X2', type='Molex KK 254', gender='female', pinout=PINOUT_I2C, ports_left=True))
Harness.add(Node('X3', type='Molex KK 254', gender='female', pinout=PINOUT_I2C, ports_left=True))
Harness.add(Node('X4', type='Molex KK 254', gender='female', pinout=('GND','+12V')+PINOUT_SPI_DATAONLY, ports_left=True))
Harness.add(Node('X5', type='Molex Micro-Fit', gender='male', pinout=('GND','+12V'), ports_right=True))
Harness.add(Cable('W1', mm2=0.14, length=0.2, colors=COLORS_I2C))
Harness.add(Cable('W2', mm2=0.14, length=0.2, colors=COLORS_I2C))
Harness.add(Cable('W3', mm2=0.14, length=0.2, colors=('BK','BU','OG','VT')))
Harness.add(Cable('W4', mm2=0.5, length=0.35, colors=('BK','RD')))
Harness.objects['W1'].connect('X1',(1,2,3,4),'auto','X2','auto')
Harness.objects['W2'].connect('X1',(1,2,3,4),'auto','X3','auto')
Harness.objects['W3'].connect('X1',(1,5,6,7),'auto','X4',(1,3,4,5))
Harness.objects['W4'].connect_all_straight('X5','X4')

Harness.graphviz()
