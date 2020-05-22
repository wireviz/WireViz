import wireviz

PINOUT_I2C = ("GND","VCC","SCL","SDA")
COLORS_WEIRD = ("infrared","ultraviolet","transparent","invisible")

X1 = wireviz.Node("X1", num_pins=4)
X2 = wireviz.Node("X2", pinout=PINOUT_I2C)
X3 = wireviz.Node("X3", pinout=PINOUT_I2C)

W1 = wireviz.Cable("W1", num_wires=4)
W2 = wireviz.Cable("W2", num_wires=4, color_code="DIN")
W3 = wireviz.Cable("W3", num_wires=3, colors=COLORS_WEIRD)

print(X1)
print(X2)
print(X3)

print(W1)
print(W2)
print(W3)
