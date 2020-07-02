# WireViz Tutorial
## 1 - Bare-bones example

* Minimum working example
* Only 1-to-1 sequential wiring

[Source](tutorial01.yml):

```yaml
connectors:
  X1:
    pincount: 4
  X2:
    pincount: 4

cables:
  W1:
    wirecount: 4
    length: 1

connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    - X2: [1-4]
```


Output:

![](tutorial01.png)

[Bill of Materials](tutorial01.bom.tsv)


## 2 - Adding parameters and colors

* Parameters for connectors and cables
* Auto-calculate equivalent AWG from mm2
* Non-sequential wiring

[Source](tutorial02.yml):

```yaml
connectors:
  X1:
    pincount: 4
    # More connector parameters:
    type: Molex KK 254
    subtype: female
  X2:
    pincount: 4
    type: Molex KK 254
    subtype: female

cables:
  W1:
    wirecount: 4
    # more cable parameters:
    length: 1
    gauge: 0.25 mm2
    show_equiv: true # auto-calculate AWG equivalent
    colors: [WH, BN, GN, YE]

connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    # non-sequential wiring:
    - X2: [1,2,4,3]
```


Output:

![](tutorial02.png)

[Bill of Materials](tutorial02.bom.tsv)


## 3 - Pinouts, shielding, templates (I)

* Connector pinouts
  * Pincount implicit in pinout
* Cable color codes
* Cable shielding, shield wiring
* Templates

[Source](tutorial03.yml):

```yaml
connectors:
  X1: &template1 # define a template for later use
    pinout: [GND, VCC, RX, TX] # pincount implicit in pinout
    type: Molex KK 254
    subtype: female
  X2:
    <<: *template1 # reuse template

cables:
  W1:
    wirecount: 4
    length: 1
    gauge: 0.25 mm2
    show_equiv: true
    color_code: DIN # auto-assign colors based on DIN 47100
    shield: true # add cable shielding

connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    - X2: [1,2,4,3]
  - # connect the shielding to a pin
    - X1: 1
    - W1: s
```


Output:

![](tutorial03.png)

[Bill of Materials](tutorial03.bom.tsv)


## 4 - Templates (II), notes, American standards, daisy chaining (I)

* Overriding template parameters
* Add nodes to connectors and cables
* American standards: AWG gauge and IEC colors
* Linear daisy-chain
  * Convenient for shorter chains

[Source](tutorial04.yml):

```yaml
connectors:
  X1: &template_con
    pinout: [GND, VCC, SCL, SDA]
    type: Molex KK 254
    subtype: male
    notes: to microcontroller # add notes
  X2:
    <<: *template_con # use template
    subtype: female   # but override certain parameters
    notes: to accelerometer
  X3:
    <<: *template_con
    subtype: female
    notes: to temperature sensor

cables:
  W1: &template_cbl
    wirecount: 4
    length: 0.3
    gauge: 24 AWG # specify gauge in AWG directly
    color_code: IEC # IEC 62 colors also supported
    notes: This cable is a bit longer
  W2:
    <<: *template_cbl
    length: 0.1
    notes: This cable is a bit shorter

connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    - X2: [1-4]
  - # daisy chain connectors (in line)
    - X2: [1-4]
    - W2: [1-4]
    - X3: [1-4]
```


Output:

![](tutorial04.png)

[Bill of Materials](tutorial04.bom.tsv)


## 5 - Ferrules, wire bundles, custom wire colors

* Ferrules
  * Simpler than connectors
  * Compact graphical representation
  * Only one pin, only one connection, no designator
  * Define once, auto-generate where needed
* Wire bundles
  * Internally treated as cables
  * Different treatment in BOM: Each wire is listed individually
  * Represented with dashed outline
* Custom wire colors
  * Wirecount can be implicit in color list

[Source](tutorial05.yml):

```yaml
connectors:
  X1:
    pinout: [+12V, GND, GND, +5V]
    type: Molex 8981
    subtype: female

ferrules: # ferrules
  F1:
    type: Ferrule, crimp
    subtype: 0.5 mm²
    color: OG # optional color

cables:
  W1:
    category: bundle # bundle
    length: 0.3
    gauge: 0.5 mm2
    colors: [YE, BK, BK, RD] # custom colors, wirecount is implicit

connections:
  - # attach ferrules
    - F1 # no need for list of connections; one ferrule per wire is auto-generated and attached
    - W1: [1-4] # a new ferrule is auto-generated for each wire
  - # attach connectors (separately from ferrules)
    - W1: [1-4]
    - X1: [1-4]
```


Output:

![](tutorial05.png)

[Bill of Materials](tutorial05.bom.tsv)


## 6 - Custom ferrules

* Custom ferrules
  * Allows attaching more than one wire to a ferrule
  * Requires defining them as regular connectors with unique designators, adding `category: ferrule` parameter

[Source](tutorial06.yml):

```yaml
connectors:
  X1:
    pinout: [+12V, GND, GND, +5V]
    type: Molex 8981
    subtype: female
  F_10_1: # manually define a ferrule (with unique designator)
    category: ferrule
    type: Ferrule, crimp
    subtype: 1.0 mm²
    color: YE

ferrules: # ferrules
  F_05:
    type: Ferrule, crimp
    subtype: 0.5 mm²
    color: OG # optional color

cables:
  W1:
    category: bundle # bundle
    length: 0.3
    gauge: 0.5 mm2
    colors: [YE, BK, BK, RD] # custom colors, wirecount is implicit

connections:
  - # attach ferrules
    - F_05
    - W1: [1,4] # a new ferrule is auto-generated for each wire
  - # attach connectors (separately from ferrules)
    - W1: [1-4]
    - X1: [1-4]
  -
    - F_10_1: 1 # manually defined ferrules are treated like regular connectors,
                # thus requiring a pin number
    - W1: 2
  -
    - F_10_1: 1
    - W1: 3
```


Output:

![](tutorial06.png)

[Bill of Materials](tutorial06.bom.tsv)


## 7 - Daisy chaining (II)

* Zig-zag daisy chain
  * Convenient for longer chains

[Source](tutorial07.yml):

```yaml
connectors:
  X1: &template_con
    type: Molex KK 254
    subtype: female
    pinout: [GND, VCC, SCL, SDA]
  X2:
    <<: *template_con
  X3:
    <<: *template_con
  X4:
    <<: *template_con
  X5:
    <<: *template_con
  X6:
    <<: *template_con

cables:
  W1: &template_wire
    gauge: 0.25 mm2
    length: 0.2
    colors: [TQ, PK, YE, VT]
    category: bundle
  W2:
    <<: *template_wire
  W3:
    <<: *template_wire
  W4:
    <<: *template_wire
  W5:
    <<: *template_wire

connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    - X2: [1-4]
  -
    - X3: [1-4]
    - W2: [1-4]
    - X2: [1-4]
  -
    - X3: [1-4]
    - W3: [1-4]
    - X4: [1-4]
  -
    - X5: [1-4]
    - W4: [1-4]
    - X4: [1-4]
  -
    - X5: [1-4]
    - W5: [1-4]
    - X6: [1-4]
```


Output:

![](tutorial07.png)

[Bill of Materials](tutorial07.bom.tsv)


## 8 - Part numbers

* Part number information can be added to parts
  * Only provided fields will be added to the diagram and bom
* Bundles can have part information specified by wire

[Source](tutorial08.yml):

```yaml
connectors:
  X1: &template1 # define a template for later use
    type: Molex KK 254
    pincount: 4
    subtype: female
    manufacturer: Molex
    manufacturer_part_number: 22013047
  X2:
    <<: *template1 # reuse template
    internal_part_number: CON4
  X3:
    <<: *template1 # reuse template

cables:
  W1:
    wirecount: 4
    length: 1
    gauge: 0.25 mm2
    color_code: IEC
    manufacturer: CablesCo
    manufacturer_part_number: ABC123
    internal_part_number: CAB1
  W2:
    category: bundle
    length: 1
    gauge: 0.25 mm2
    colors: [YE, BK, BK, RD]
    manufacturer: [WiresCo,WiresCo,WiresCo,WiresCo]
    manufacturer_part_number: [W1-YE,W1-BK,W1-BK,W1-RD]
    internal_part_number: [WIRE1,WIRE2,WIRE2,WIRE3]


connections:
  -
    - X1: [1-4]
    - W1: [1-4]
    - X2: [1-4]
  -
    - X1: [1-4]
    - W2: [1-4]
    - X3: [1-4]
```


Output:

![](tutorial08.png)

[Bill of Materials](tutorial08.bom.tsv)


