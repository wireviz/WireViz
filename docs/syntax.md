# WireViz Syntax

## Main sections

```yaml
connectors:  # dictionary of all used connectors
  <str>   :    # unique connector designator/name
    ...          # connector attributes (see below)
  <str>   :
    ...
  ...

cables:      # dictionary of all used cables and wires
  <str>   :    # unique cable designator/name
    ...          # cable attributes (see below)
  <str>   :
    ...
  ...

connections:  # list of all connections to be made
              # between cables and connectors
  -
    ...         # connection set (see below)
  -
    ...
  ...

additional_bom_items:  # custom items to add to BOM
  - <bom-item>           # BOM item (see below)
  ...

metadata:  # dictionary of meta-information describing the harness
  <key>   : <value>  # any number of key value pairs (see below)
  ...

options:  # dictionary of common attributes for the whole harness
  <str>   : <value>  # optional harness attributes (see below)
  ...

tweak:  # optional tweaking of .gv output
  ...
```
## Connector attributes

```yaml
<str>   :  # unique connector designator/name
  # general information about a connector (all optional)
  type: <str>   
  subtype: <str>   
  color: <color>  # see below
  image: <image>  # see below
  notes: <str>   

  # product information (all optional)
  ignore_in_bom: <bool>  # if set to true the connector is not added to the BOM
  pn: <str>              # [internal] part number
  manufacturer: <str>    # manufacturer name
  mpn: <str>             # manufacturer part number
  supplier: <str>        # supplier name
  spn: <str>             # supplier part number
  additional_components: # additional components
    - <additional-component> # additional component (see below)

  # pinout information
  # at least one of the following must be specified
  pincount: <int>    # if omitted, is set to length of specified list(s)
  pins: <List>       # if omitted, is autofilled with [1, 2, ..., pincount]
  pinlabels: <List>  # if omitted, is autofilled with blanks

  # pin color marks (optional)
  pincolors: <List>  # list of colors to be assigned to the respective pins;
                     # if list length is lower than connector pinout,
                     # no color marks will be added to remaining pins

  # rendering information (all optional)
  bgcolor: <color>       # Background color of diagram connector box
  bgcolor_title: <color> # Background color of title in diagram connector box
  style: <style>         # may be set to simple for single pin connectors
  show_name: <bool>      # defaults to true for regular connectors,
                         # false for simple connectors
  show_pincount: <bool>  # defaults to true for regular connectors
                         # false for simple connectors
  hide_disconnected_pins: <bool>  # defaults to false

  # loops
  loops:              # a list(dict) of loops
    - <str>: <List>   # every list item is itself a list of pins
                      # on the connector that are to be shorted with a cable loop
                      # more information about the loop can be added by additional
                      # components definition (see below)
  # Shorts
  shorts:             # a list(dict) of shorts
    - <str>: <List>   # every list item is itself a list of pins
                      # on the connector that are to be shorted represented inside
                      # the connector table
                      # more information about the loop can be added by additional
                      # components definition (see below)
```

## Cable attributes

```yaml
<str>   :  # unique cable designator/name
  # general information about a connector (all optional)
  category: <category>  # may be set to bundle;
                        # generates one BOM item for every wire in the bundle
                        # instead of a single item for the entire cable;
                        # renders with a dashed outline
  type: <str>   
  gauge: <int/float/str>  # allowed formats:
                          # <int/float> mm2  is understood
                          # <int> AWG        is understood
                          # <int/float>      is assumed to be mm2
                          # <str>            custom units and formats are allowed
                          #                  but unavailable for auto-conversion
  show_equiv: <bool>      # defaults to false; can auto-convert between mm2 and AWG
                          # and display the result when set to true
  length: <int/float>[ <unit>]  # <int/float> is assumed to be in meters unless <unit> is specified
                                # e.g. length: 2.5 -> assumed to be 2.5 m
                                # or   length: 2.5 ft -> "ft" is used as the unit
                                # Units are not converted during BOM generation;
                                # different units result in separate BOM entries.
  shield: <bool/color>  # defaults to false
                        # setting to true will display the shield as a thin black line
                        # using a color (see below) will render the shield in that color
                        # A shield can be accessed by using 's' as the wire ID
  color: <color>  # see below
  image: <image>  # see below
  notes: <str>   

  # product information (all optional)
  ignore_in_bom: <bool>  # if set to true the cable or wires are not added to the BOM
  pn: <str>              # [internal] part number
  manufacturer: <str>    # manufacturer name
  mpn: <str>             # manufacturer part number
  supplier: <str>        # supplier name
  spn: <str>             # supplier part number
  additional_components: # additional components
    - <additional-component> # additional component (see below)

  # conductor information
  # the following combinations are permitted:
  # wirecount only          no color information is specified
  # colors only             wirecount is inferred from list length
  # wirecount + color_code  colors are auto-generated based on the specified
  #                         color code (see below) to match the wirecount
  # wirecount + colors      colors list is trimmed or repeated to match the wirecount
  wirecount: <int>
  colors: <List>     # list of colors (see below)
  color_code: <str>  # one of the supported cable color codes (see below)

  wirelabels: <List>  # optional; one label for each wire

  # rendering information (all optional)
  bgcolor: <color>          # Background color of diagram cable box
  bgcolor_title: <color>    # Background color of title in diagram cable box
  show_name: <bool>         # defaults to true
  show_wirecount: <bool>    # defaults to true
  show_wirenumbers: <bool>  # defaults to true for cables; false for bundles

```

## Connection sets

A connection set is used to connect multiple components together. Multiple connections can be easily created in parallel within one connection set, by specifying a list of individual pins (for `connectors`) or wires (for `cables`) for every component along the way.

```yaml
connections:
  -                # Each list entry is a connection set
    - <component>    # Each connection set is itself a list of items
    - <component>    # Items must alternatingly belong to the connectors and cables sections
                     # Arrows may be used instead of cables
    -...

  - # example (single connection)
    - <connector>: <pin>   # attach one pin of the connector
    - <cable>:     <wire>  # attach one wire of the cable
    - <connector>          # for simple connectors, pin 1 is implicit
    - <cable>:     s       # for shielded wires, s attaches to the shield

  - # example (multiple parallel connections)
    - <connector>: [<pin>,  ..., <pin> ]  # attach multiple pins in parallel
    - <cable>:     [<wire>, ..., <wire>]  # attach multiple wires in parallel
    - <connector>                         # auto-generate a new connector for every parallel connection
    - <cable>:     [<wire>-<wire>]        # specify a range of wires to attach in parallel
    - [<connector>, ..., <connector>]     # specify multiple simple connectors to attach in parallel
                                          # these may be unique, auto-generated, or a mix of both

  - # example (arrows between pins)
    - <connector>: [<pin>, ..., <pin>]
    - [<arrow>, ..., <arrow>]             # draw arrow linking pins of both connectors
                                          # use single line arrows (--, <--, <-->, -->)
    - <connector>: [<pin>, ..., <pin>]

  - # example (arrows between connectors)
    - <connector>                  
    - <arrow>                               # draw arrow linking the connectors themselves
                                            # use double line arrow (==, <==, <==>, ==>)
    - <connector>

  ...    
```

- Each connection set is a list of components.
- The minimum number of items is one.
- The maximum number of items is unlimited.
- Items must alternatingly belong to the `connectors` and the `cables` sections.
- When a connection set defines multiple parallel connections, the number of specified `<pin>`s and `<wire>`s for each component in the set must match. When specifying only one designator, one is auto-generated for each connection of the set.
- `<pin>` may reference a pin's unique ID (as per the connector's `pins` attribute, auto-numbered from 1 by default) or its label (as per `pinlabels`).
- `<wire>` may reference a wire's number within a cable/bundle, its label (as per `wirelabels`) or, if unambiguous, its color.
- For `<arrow>`, see below.

### Single connections

#### Connectors

- `- <designator>: <int/str>` attaches a pin of the connector, referring to a pin number (from the connector's `pins` attribute) or a pin label (from its `pinlabels` attribute), provided the label is unique.

- `- <designator>` is allowed for simple connectors, since they have only one pin to connect.

#### Cables

- `<designator>: <wire>` attaches a specific wire of a cable, using its number.

### Multiple parallel connections

#### Connectors

- `- <designator>: [<pin>, ..., <pin>]`

  Each `<pin>` may be:

  - `<int/str>` to refer to a specific pin, using its number (from its `pins` attribute) or its label (from its `pinlabels` attribute, provided the label is unique for this connector)

  - `<int>-<int>` auto-expands to a range, e.g. `1-4` auto-expands to `1,2,3,4`; `9-7` will auto-expand to `9,8,7`.

  - Mixing types is allowed, e.g. `[<pin>, <pinlabel>, <pin>-<pin>, <pin>]`

- `- [<designator>, ..., <designator>]`

  Attaches multiple different single pin connectors, one per connection in the set.

- `- <designator>`

  Attaches multiple instances of the same single pin connector, one per connectioin in the set.

#### Cables

- `<designator>: [<wire>, ..., <wire>]`

  Each `<wire>` may be:

  - `<int>` to refer to a specific wire, using its number.
  - `<int>-<int>` auto-expands to a range.
  - `<str>` to refer to a wire's label or color, if unambiguous.

### Arrows

Arrows may be used in place of wires to join two connectors. This can represent the mating of matching connectors.

To represent joining individual pins between two connectors, a list of single arrows is used:
```yaml
connections:
  -
    - <connector>: [<pin>,...,<pin>]
    - [<arrow>, ..., <arrow>]         # --, <--, <--> or -->
    - <connector>: [<pin>,...,<pin>]
```

To represent mating of two connectors as a whole, one double arrow is used:
```yaml
connections:
  -
    - <connector>  # using connector designator only
    - <arrow>      # ==, <==, <==> or ==>
    - <connector>
  -
    - ...
    - <connector>: [<pin>, ...]  # designator and pinlist (pinlist is ignored)
                                 # useful when combining arrows and wires
    - <arrow>                    # ==, <==, <==> or ==>
    - <connector>: [<pin>, ...]
    - ...
```

### Autogeneration of items

If multiple identical copies of a connector or cable are needed, it is possible to define them once as a template, and then generate multiple instances as needed. This is called autogeneration. Both connectors and cables can be autogenerated.

Autogenerated instances of components can be explicitly assigned a designator; this way, they can be referenced in multiple connection sets. However, it is also possible to generate unnamed instances of components. This is especially useful for components that do not need to be referenced in more than one connection set, and where naming each individual instance is an unnecessary complication.

Example (see `connections` section):

```yaml
connectors:
  X:
    # ...
  Y:
    # ...
  Z:
    style: simple
    # ...
cables:
  V:
    # ...
  W:
    # ...

connections:
  -  # no autogeneration (normal use)
    - X: [1,2,...]  # Use X as both the template and the instance designator
    - V: [1,2,...]  # Use V as both the template and the instance designator
    # ...

  -  # autogeneration of named instances
    - Y.Y1: [1,2,...]  # Use template Y, generate instance with designator Y1
    - W.W1: [1,2,...]  # Use template W, generate instance with designator W1
    - Y.Y2: [1,2,...]  # generate more instances from the same templates
    - W.W2: [1,2,...]
    - Y.Y3: [1,2,...]  

  -  # autogeneration of unnamed instances
    - Y3:   [1,2,...]  # reuse existing instance Y3
    - W.W4: [1,2,...]
    - Z.             # Use template Z, generate one unnamed instance
                     # for each connection in set
```

Since the internally assigned designator of an unnamed component is not known to the user, one instance of the connector can not be referenced again outside the point of creation (i.e. in other connection sets, or later in the same set). Autogeneration of unnamed instances is therefore only useful for terminals with only one wire attached, or splices with exactly one wire going in, and one wire going out.
If a component is to be used in other connection sets (e.g. for a three-way splice, or a crimp where multiple wires are joined), a named instance needs to be used.

The default character to trigger autogeneration of components is `.`. A different character can be specified using the `template_separator` option (see below).

Names of autogenerated components are hidden by default. While they can be shown in the graphical output using the `show_name: true` option, it is not recommended to manually use the internally assigned designator (starting with a double underscore `__`), since it might change in future WireViz versions, or when the order of items in connection sets changes.


### Unconnected components

Even if a component is not connected to any other components, it must be mentioned in a connection set for it to be displayed.

```yaml
connectors:
  X1:  # this connector will not be connected to any other components
    ... 

connections:
-
  - X1  # minimal connection set to include connector in the diagram

```

If any component is defined in the `connectors` or `cables` sections but not referenced in `connections`, a warning is printed in the console.


## Metadata entries

```yaml
  # Meta-information describing the harness

  # Each key/value pair replaces all key references in
  # the HTML output template with the belonging value.
  # Typical keys are 'title', 'description', and 'notes',
  # but any key is accepted. Unused keys are ignored.
  <key>   : <value>  # Any valid YAML syntax is accepted
  # If no value is specified for 'title', then the
  # output filename without extension is used.
```

## Options

```yaml
  # Common attributes for the whole harness.
  # All entries are optional and have default values.

  # Background color of diagram and HTML output
  bgcolor: <color>             # Default = 'WH'

  # Background color of other diagram elements
  bgcolor_node: <color>        # Default = 'WH'
  bgcolor_connector: <color>   # Default = bgcolor_node
  bgcolor_cable: <color>       # Default = bgcolor_node
  bgcolor_bundle: <color>      # Default = bgcolor_cable

  # How to display colors as text in the diagram
  # 'full' : Lowercase full color name
  # 'FULL' : Uppercase full color name
  # 'hex'  : Lowercase hexadecimal values
  # 'HEX'  : Uppercase hexadecimal values
  # 'short': Lowercase short color name
  # 'SHORT': Uppercase short color name
  # 'ger'  : Lowercase short German color name
  # 'GER'  : Uppercase short German color name
  color_mode: <str>            # Default = 'SHORT'

  # Fontname to use in diagram and HTML output
  fontname: <str>              # Default = 'arial'

  # If True, show only a BOM entry reference together with basic info
  # about additional components inside the diagram node (connector/cable box).
  # If False, show all info about additional components inside the diagram node.
  mini_bom_mode: <bool>        # Default = True

  # Character to split template and designator for autogenerated components
  template_separator: <str>    # Default = '.'
```


## BOM items and additional components

Connectors (both regular, and auto-generated), cables, and wires of a bundle are automatically added to the BOM,
unless the `ignore_in_bom` attribute is set to `true`.
Additional items can be added to the BOM as either part of a connector or cable or on their own.

Parts can be added to a connector or cable in the section `<additional-component>` which will also list them in the graph.

```yaml
-
  type: <str>  # type of additional component
  # all the following are optional:
  subtype: <str>  # additional description (only shown in bom)
  qty: <int/float>  # qty to add to the bom (defaults to 1)
  qty_multiplier: <str>  # multiplies qty by a feature of the parent component
                  # when used in a connector:
                  # pincount         number of pins of connector
                  # populated        number of populated positions in a connector
                  # unpopulated      number of unpopulated positions
                  # when used in a cable:
                  # wirecount        number of wires of cable/bundle
                  # terminations     number of terminations on a cable/bundle
                  # length           length of cable/bundle
                  # total_length     sum of lengths of each wire in the bundle
  unit: <str>
  pn: <str>            # [internal] part number
  manufacturer: <str>  # manufacturer name  
  mpn: <str>           # manufacturer part number
  supplier: <str>      # supplier name  
  spn: <str>           # supplier part number
  bgcolor: <color>     # Background color of entry in diagram component box

  references: <list>   # A list of designators that are related to this 
                       # component, for example shorts or loops
  
  # Shorts and Loops specific attributs
  color: <color>       # if a reference to a short or loop is defined than
                       # this color is used for the short or loop
```

Alternatively items can be added to just the BOM by putting them in the section `<bom-item>` above.

```yaml
-
  description: <str>              
  # all the following are optional:
  qty: <int/float>  # qty to add to the bom (defaults to 1)
  unit: <str>   
  designators: <List>
  pn: <str>            # [internal] part number
  manufacturer: <str>  # manufacturer name  
  mpn: <str>           # manufacturer part number
  supplier: <str>      # supplier name  
  spn: <str>           # supplier part number
```

## GraphViz tweaking (experimental)

```yaml
  # Optional tweaking of the .gv output.
  # This feature is experimental and might change
  # or be removed in future versions.

  override:  # dict of .gv entries to override
    # Each entry is identified by its leading string
    # in lines beginning with a TAB character.
    # The leading string might be in "quotes" in
    # the .gv output. This leading string must be
    # followed by attributes in [square brackets].
    # Entries with an attribute containing HTML are
    # not supported.
    <str>:  # leading string of .gv entry
      <str> : <str/null>  # attribute and its new value
      # Any number of attributes can be overridden
      # for each entry. Attributes not already existing
      # in the entry will be appended to the entry.
      # Use null as new value to delete an attribute.

  append: <str/list> # string or list of strings to append to the .gv output
```

## Colors

Colors are defined via uppercase, two character strings.
Striped/banded wires can be specified by simply concatenating multiple colors, with no space inbetween, eg. `GNYE` for green-yellow.

The following colors are understood:

- `BK` ![##000000](https://via.placeholder.com/15/000000/000000?text=+) (black)
- `WH` ![##ffffff](https://via.placeholder.com/15/ffffff/000000?text=+) (white)
- `GY` ![##999999](https://via.placeholder.com/15/999999/000000?text=+) (grey)
- `PK` ![##ff66cc](https://via.placeholder.com/15/ff66cc/000000?text=+) (pink)
- `RD` ![##ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) (red)
- `OG` ![##ff8000](https://via.placeholder.com/15/ff8000/000000?text=+) (orange)
- `YE` ![##ffff00](https://via.placeholder.com/15/ffff00/000000?text=+) (yellow)
- `OL` ![##708000](https://via.placeholder.com/15/708000/000000?text=+) (olive green)
- `GN` ![##00ff00](https://via.placeholder.com/15/00ff00/000000?text=+) (green)
- `TQ` ![##00ffff](https://via.placeholder.com/15/00ffff/000000?text=+) (turquoise)
- `LB` ![##a0dfff](https://via.placeholder.com/15/a0dfff/000000?text=+) (light blue)
- `BU` ![##0066ff](https://via.placeholder.com/15/0066ff/000000?text=+) (blue)
- `VT` ![##8000ff](https://via.placeholder.com/15/8000ff/000000?text=+) (violet)
- `BN` ![##895956](https://via.placeholder.com/15/895956/000000?text=+) (brown)
- `BG` ![##ceb673](https://via.placeholder.com/15/ceb673/000000?text=+) (beige)
- `IV` ![##f5f0d0](https://via.placeholder.com/15/f5f0d0/000000?text=+) (ivory)
- `SL` ![##708090](https://via.placeholder.com/15/708090/000000?text=+) (slate)
- `CU` ![##d6775e](https://via.placeholder.com/15/d6775e/000000?text=+) (copper)
- `SN` ![##aaaaaa](https://via.placeholder.com/15/aaaaaa/000000?text=+) (tin)
- `SR` ![##84878c](https://via.placeholder.com/15/84878c/000000?text=+) (silver)
- `GD` ![##ffcf80](https://via.placeholder.com/15/ffcf80/000000?text=+) (gold)

<!-- color list generated with a helper script: -->
<!-- https://gist.github.com/formatc1702/3c93fb4c5e392364899283f78672b952 -->

It is also possible to specify colors as hexadecimal RGB values, e.g. `#112233` or `#FFFF00:#009900`.
Remember quoting strings containing a `#` in the YAML file.

## Cable color codes

Supported color codes:

- `DIN` for [DIN 47100](https://en.wikipedia.org/wiki/DIN_47100)

  ![##ffffff](https://via.placeholder.com/15/ffffff/000000?text=+) ![##895956](https://via.placeholder.com/15/895956/000000?text=+) ![##00ff00](https://via.placeholder.com/15/00ff00/000000?text=+) ![##ffff00](https://via.placeholder.com/15/ffff00/000000?text=+) ![##999999](https://via.placeholder.com/15/999999/000000?text=+) ![##ff66cc](https://via.placeholder.com/15/ff66cc/000000?text=+) ![##0066ff](https://via.placeholder.com/15/0066ff/000000?text=+) ![##ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) ![##000000](https://via.placeholder.com/15/000000/000000?text=+) ![##8000ff](https://via.placeholder.com/15/8000ff/000000?text=+) ...

- `IEC` for [IEC 60757](https://en.wikipedia.org/wiki/Electronic_color_code#Color_band_system) ("ROY G BIV")

  ![##895956](https://via.placeholder.com/15/895956/000000?text=+) ![##ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) ![##ff8000](https://via.placeholder.com/15/ff8000/000000?text=+) ![##ffff00](https://via.placeholder.com/15/ffff00/000000?text=+) ![##00ff00](https://via.placeholder.com/15/00ff00/000000?text=+) ![##0066ff](https://via.placeholder.com/15/0066ff/000000?text=+) ![##8000ff](https://via.placeholder.com/15/8000ff/000000?text=+) ![##999999](https://via.placeholder.com/15/999999/000000?text=+) ![##ffffff](https://via.placeholder.com/15/ffffff/000000?text=+) ![##000000](https://via.placeholder.com/15/000000/000000?text=+) ...

- `TEL` and `TELALT`  for [25-pair color code](https://en.wikipedia.org/wiki/25-pair_color_code)
- `T568A` and `T568B` for [TIA/EIA-568](https://en.wikipedia.org/wiki/TIA/EIA-568#Wiring) (e.g. Ethernet)
- `BW` for alternating black and white


## Images

Both connectors and cables accept including an image with a caption within their respective nodes.

```yaml
image:
  src: <path>        # path to the image file
  # optional parameters:
  caption: <str>     # text to display below the image
  bgcolor: <color>   # Background color of entry in diagram component box
  width: <int>       # range: 1~65535; unit: points
  height: <int>      # range: 1~65535; unit: points
  # if only one dimension (width/height) is specified, the image is scaled proportionally.
  # if both width and height are specified, the image is stretched to fit.
```

For more fine grained control over the image parameters, please see [`advanced_image_usage.md`](advanced_image_usage.md).


## Multiline strings

The following attributes accept multiline strings:
- `type`
- `subtype` (connectors only)
- `notes`
- `manufacturer`
- `mpn`
- `supplier`
- `spn`
- `image.caption`
- `tweak.append`

### Method 1

By using `|`, every following indented line is treated as a new line.

```yaml
attribute: |
  This is line 1.
  This is line 2.
```

### Method 2

By using double quoted strings, `\n` within the string is converted to a new line.

```yaml
attribute: "This is line 1.\nThis is line 2."
```

Plain (no quotes) or single quoted strings do not convert `\n`.

See [yaml-multiline.info](https://yaml-multiline.info/) for more information.

## Inheritance

[YAML anchors and references](https://blog.daemonl.com/2016/02/yaml.html) are useful for defining and referencing information that is used more than once in a file, e.g. when using defining multiple connectors of the same type or family. See [Demo 02](../examples/demo02.yml) for an example.
