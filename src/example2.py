import wireviz

h = wireviz.Harness()

# shortcuts for use during harness creation
PINOUT_I2C = ('GND','+5V','SCL','SDA')
COLORS_I2C = ('BK', 'RD', 'YE', 'GN')
PINOUT_SPI_DATAONLY = ('MISO','MOSI','SCK')

h.add_node('X1', type='Molex KK 254', gender='female', pinout=('GND',
                                                              '+5V',
                                                              'SCL',
                                                              'SDA',
                                                              'MISO',
                                                              'MOSI',
                                                              'SCK',
                                                              'N/C'))
h.add_node('X2', type='Molex KK 254', gender='female', pinout=PINOUT_I2C)
h.add_node('X3', type='Molex KK 254', gender='female', pinout=PINOUT_I2C)
h.add_node('X4', type='Molex KK 254', gender='female', pinout=('GND','+12V')+PINOUT_SPI_DATAONLY)
h.add_node('X5', type='Molex Micro-Fit', gender='male', pinout=('GND','+12V'))
h.add_cable('W1', mm2=0.14, show_equiv=True, length=0.2, colors=COLORS_I2C, show_name=False)
h.add_cable('W2', mm2=0.14, show_equiv=True, length=0.2, colors=COLORS_I2C, show_name=False)
h.add_cable('W3', mm2=0.14, show_equiv=True, length=0.2, colors=('BK','BU','OG','VT'), show_name=False)
h.add_cable('W4', mm2=0.5, show_equiv=True, length=0.35, colors=('BK','RD'), show_name=False)
h.connect('W1','X1',(1,2,3,4),'auto','X2','auto')
h.connect('W2','X1',(1,2,3,4),'auto','X3','auto')
h.connect('W3','X1',(1,5,6,7),'auto','X4',(1,3,4,5))
h.connect_all_straight('W4','X5','X4')

h.output(filename='output', format=('png','svg'), view=False)
