# WireViz Syntax

## Main sections

```yaml
connectors:   # dictionary of all used connectors
  X1:         # unique connector designator/name
    ...       # connector attributes (see below)
  X2:
    ...
  ...

cables:       # dictionary of all used cables and wires
  W1:         # unique cable designator/name
    ...       # cable attributes (see below)
  W2:
    ...
  ...

connections:  # list of all connections to be made
              # between cables and connectors
  -
    ...       # connection set (see below)
  -
    ...
```

## Connector attributes

```yaml
<string>:  # unique connector designator/name
  # general information about a connector (all optional)
  type: <string>
  subtype: <string>
  color: <color>  # see below
  notes: <string>

  # product information (all optional)
  manufacturer: <string>
  manufacturer_part_number: <string>
  internal_part_number: <string>

  # pinout information
  # at least one of the following must be specified
  # if more than one is specified, list lenghts must match pincount, and each other
  pincount: <int>    # if omitted, is set to length of specified list(s)
  pins: <List>       # if omitted, is autofilled with [1, 2, ..., pincount]
  pinlabels: <List>  # if omitted, is autofilled with blanks

  # rendering information (all optional)
  style: <style>         # may be set to simple for single pin connectors
  show_name: <bool>      # defaults to true for regular connectors,
                         # false for simple connectors
  show_pincount: <bool>  # defaults to true for regular connectors
                         # false for simple connectors
  hide_disconnected_pins: <bool>  # defaults to false

  # loops and shorts (#48)
  loops: <List>  # TODO

  # auto-generation
  autogenerate: <bool>  # optional; defaults to false; see below

```

### Auto-generation of connectors

<!-- TODO -->

## Cable attributes

```yaml
<string>:  # unique cable designator/name
  # general information about a connector (all optional)
  category: <category>       # may be set to bundle;
                             # generates one BOM item for every wire in the bundle
                             # instead of a single item for the entire cable;
                             # renders with a dashed outline
  type: <string>
  gauge: <int/float/string>  # allowed formats:
                             # <int/float>      is assumed to be mm2
                             # <int/float> mm2  is understood
                             # <int> AWG        is understood
                             # <string>         custom units and formats are allowed
                             #                  but unavailable for auto-conversion
  show_equiv: <bool>         # defaults to false; can auto-convert between mm2 and AWG
                             # and display the result when set to true
  length: <int/float>        # is assumed to be in meters
  shield: <bool>             # defaults to false
                             # the shield can be accessed in connections
                             # using 's' as the wire number
  notes: <string>

  # product information (all optional)
  manufacturer: <string>
  manufacturer_part_number: <string>
  internal_part_number: <string>

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

  # rendering information (all optional)
  show_name: <bool>       # defaults to true
  show_wirecount: <bool>  # defaults to true

```

## Connection sets

<!-- TODO -->

## Colors

Colors are defined via uppercase, two character strings.
Striped/banded wires can be specified by simply concatenating multiple colors, with no space inbetween, eg. `GNYE` for green-yellow.

```
TODO: list valid colors
```

## Cable color codes

Supported color codes:

- `DIN` for [DIN 47100](https://en.wikipedia.org/wiki/DIN_47100)
- `IEC` for [IEC 62](https://en.wikipedia.org/wiki/Electronic_color_code#Color_band_system) ("ROY G BIV")
- `TEL` and `TELALT`  for [25-pair color code](https://en.wikipedia.org/wiki/Electronic_color_code#Color_band_system)
- `T568A` and `T568B` for [TIA/EIA-568](https://en.wikipedia.org/wiki/TIA/EIA-568#Wiring)
- `BW` for alternating black and white

## Multiline strings

Connectors accept multiline strings in the `type`, `subtype` and `notes` attributes.
Cables accept multiline strings in the `type` and `notes` attributes.

### Method 1

By using `|`, every following indented line is treated as a new line

```yaml
attribute: |
  This is line 1.
  This is line 2.
```

## Method 2

By using double quoted strings, `\n` within the string is converted to a new line.
Plain (no quotes) or single quoted strings do not convert `\n`.

```yaml
attribute: "This is line 1.\nThis is line 2."
```

See [yaml-multiline.info](https://yaml-multiline.info/) for more information.
