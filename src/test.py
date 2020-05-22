import wireviz

PINOUT_SERIAL = ('DCD','RX','TX','DTR','GND','DSR','RTS','CTS','RI')
COLORS_WEIRD = ("infrared","ultraviolet","transparent","invisible")

X1 = wireviz.Node("X1", pinout=PINOUT_SERIAL, ports_right=True)
X2 = wireviz.Node("X2", num_pins=6, ports_left=True)

W1 = wireviz.Cable("W1", num_wires=3, color_code="DIN", shield=True)

W1.connect(X1,(2,3,5),(1,2,3),X2,(1,3,2))

objects = [X1, X2, W1]

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
