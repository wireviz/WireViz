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
X1:
  # general information about a connector (all optional)
  type: <string>
  subtype: <string>
  color: <colorcode>  # see below
  notes: <string>

  # pinout information
  # at least one of the following must be specified
  # if more than one is specified, list lenghts must match pincount, and each other
  pincount: <int>    # if omitted, is set to length of specified list(s)
  pins: <List>       # if omitted, is autofilled with [1, 2, ..., pincount]
  pinlabels: <List>  # if omitted, is autofilled with blanks

  # product information (all optional)
  manufacturer: <string>
  manufacturer_part_number: <string>
  internel_part_number: <string>

  # rendering information
  style: <style>         # optional; may be set to simple for single pin connectors
  show_name: <bool>      # optional; defaults to true for regular connectors,
                         # false for simple connectors
  show_pincount: <bool>  # opional; defaults to true for regular connectors
                         # false for simple connectors
  hide_disconnected_pins: <bool>  # optional; defaults to false

  # loops and shorts (#48)
  loops: <List>  # TODO

  # auto-generation
  autogenerate: <bool>  # optional; defaults to false; see below

```

### Auto-generation of connectors

<!-- TODO -->

## Cable attributes

<!-- TODO -->

## Connection sets

<!-- TODO -->

## Color codes

A color code is an uppercase, two character string.
Striped/banded wires can be specified by simply concatenating multiple color codes, with no space inbetween.

```
TODO: list valid colors
```

## Multiline strings

Accepted in the following fields:
<!-- TODO -->

How to use
<!-- TODO -->

Link to [yaml-multiline.info](https://yaml-multiline.info/)
