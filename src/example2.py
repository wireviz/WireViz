import wireviz

PINOUT_I2C = ('GND','+5V','SCL','SDA')
COLORS_I2C = ('BK', 'RD', 'YE', 'GN')

PINOUT_SPI_DATAONLY = ('MISO','MOSI','SCK')

X1 = wireviz.Node('X1',type='Molex KK 254', gender='female',  pinout=(
'GND',
'+5V',
'SCL',
'SDA',
'MISO',
'MOSI',
'SCK',
'N/C'
), ports_right=True)
X2 = wireviz.Node('X2', type='Molex KK 254', gender='female', pinout=PINOUT_I2C, ports_left=True)
X3 = wireviz.Node('X3', type='Molex KK 254', gender='female', pinout=PINOUT_I2C, ports_left=True)
X4 = wireviz.Node('X4', type='Molex KK 254', gender='female', pinout=('GND','+12V')+PINOUT_SPI_DATAONLY, ports_left=True)
X5 = wireviz.Node('X5', type='Molex Micro-Fit', gender='male', pinout=('GND','+12V'), ports_right=True)
W1 = wireviz.Cable('W1', mm2=0.14, length=0.2, colors=COLORS_I2C)
W2 = wireviz.Cable('W2', mm2=0.14, length=0.2, colors=COLORS_I2C)
W3 = wireviz.Cable('W3', mm2=0.14, length=0.2, colors=('BK','BU','OG','VT'))
W4 = wireviz.Cable('W4', mm2=0.5, length=0.35, colors=('BK','RD'))
W1.connect(X1,(1,2,3,4),'auto',X2,'auto')
W2.connect(X1,(1,2,3,4),'auto',X3,'auto')
W3.connect(X1,(1,5,6,7),'auto',X4,(1,3,4,5))
W4.connect(X5,'auto','auto',X4,'auto')
objects = [X1, X2, X3, X4, X5, W1, W2, W3, W4]

wireviz.output(objects)
