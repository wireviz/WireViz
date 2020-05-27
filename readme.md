# WireViz

## Summary

WireViz is a simple yet flexible, YAML-based markup language for documenting cables, wiring harnesses and connector pinouts with beautiful graphical output (SVG, PNG, ...) thanks to [GraphViz](https://www.graphviz.org/).

## Features

* WireViz input files are fully text based
  * No special editor required
  * Human readable
  * Easy version control
  * YAML syntax
* Understands and uses color abbreviations as per [IEC 60757](https://en.wikipedia.org/wiki/Electronic_color_code#Color_band_system) (black=BK, red=RD, ...)
  * Optionally outputs colors as abbreviation (e.g. 'YE'), full name (e.g. 'yellow') or hex value (e.g. '#ffff00'), with choice of UPPER or lower case
* Auto-generates standard wire color schemes and allows custom ones if needed
  * [DIN 47100](https://en.wikipedia.org/wiki/DIN_47100) (WT/BN/GN/YE/GY/PK/BU/RD/BK/VT/...)
  * [IEC 62](https://en.wikipedia.org/wiki/Electronic_color_code#Color_band_system)   (BN/RD/OR/YE/GN/BU/VT/GY/WT/BK/...)
* Understands wire gauge in mm² or AWG
  * Optionally auto-calculates and displays AWG equivalent when specifying mm²
* Allows more than one connector per side, as well as loopbacks
* Allows for easy-autorouting for 1-to-1 wiring

_Note_: WireViz is not designed to represent the complete wiring of a system. Its main aim is to document the construction of individual wires and harnesses.

## Example

[WireViz input file](examples/example1.yml):

    nodes:
      X1:
        type: D-Sub
        gender: female
        pinout: [DCD, RX, TX, DTR, GND, DSR, RTS, CTS, RI]
        random: yes
      X2:
        type: Molex KK 254
        gender: female
        pinout: [GND, RX, TX, N/C, OUT, IN]

    wires:
      W1:
        mm2: 0.25
        length: 0.2
        color_code: DIN
        num_wires: 3
        shield: true

    connections:
      - # format: connector->wire->connector
        - X1: [5,2,1]
        - W1: [1,2,3]
        - X2: [1,3,2]
      - # format: connector->wire or wire->connector
        - X1: 5
        - W1: s
      - # loop: connector-connector
        - X2: 5
        - X2: 6

Output file:

![Sample output diagram](examples/example1.png)

[Example 2](examples/example2.yml)

![](examples/example2.png)

## Status

This is very much a [work in progress](todo.md).


## License

GNU GPLv3
