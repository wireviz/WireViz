import wireviz

PINOUT_SERIAL = ('DCD','RX','TX','DTR','GND','DSR','RTS','CTS','RI')

PINOUT_I2C = ('GND','+5V','SCL','SDA')
COLORS_I2C = ('BK', 'RD', 'YE', 'GN')

PINOUT_SPI_DATAONLY = ('MISO','MOSI','SCK')

# example 1
# X1 = wireviz.Node("X1", pinout=PINOUT_SERIAL, ports_right=True)
# X2 = wireviz.Node("X2", num_pins=6, ports_left=True)
# W1 = wireviz.Cable("W1", show_name=True, num_wires=3, color_code="DIN", shield=True)
# W1.connect(X1,(2,3,5),(1,2,3),X2,(1,3,2))
# X2.loop(5,6)
# objects = [X1, X2, W1]

# example 2
X1 = wireviz.Node("X1", pinout=(
'GND',
'+5V',
'SCL',
'SDA',
'MISO',
'MOSI',
'SCK',
'N/C'
), ports_right=True)
X2 = wireviz.Node("X2", pinout=PINOUT_I2C, ports_left=True)
X3 = wireviz.Node("X3", pinout=PINOUT_I2C, ports_left=True)
X4 = wireviz.Node("X4", pinout=('GND','+12V')+PINOUT_SPI_DATAONLY, ports_left=True)
X5 = wireviz.Node("X5", pinout=('GND','+12V'), ports_right=True)
W1 = wireviz.Cable("W1", colors=COLORS_I2C)
W2 = wireviz.Cable("W2", colors=COLORS_I2C)
W3 = wireviz.Cable("W3", colors=('BK','BU','OG','VT'))
W4 = wireviz.Cable("W4", colors=('BK','RD'))
W1.connect(X1,(1,2,3,4),(1,2,3,4),X2,(1,2,3,4))
W2.connect(X1,(1,2,3,4),(1,2,3,4),X3,(1,2,3,4))
W3.connect(X1,(1,5,6,7),(1,2,3,4),X4,(1,3,4,5))
W4.connect(X5,(1,2),(1,2),X4,(1,2))
objects = [X1, X2, X3, X4, X5, W1, W2, W3, W4]

with open('output/output.dot','w') as f:
    with open('input/header.dot','r') as infile:
        for line in infile:
            f.write(line)
    f.write('\n\n')

    for o in objects:
        f.write(o.graphviz() + '\n')

    f.write('\n\n')
    with open('input/footer.dot','r') as infile:
        for line in infile:
            f.write(line)

# print output file
# with open('output/output.dot','r') as f:
#     for line in f:
#         print(line)
