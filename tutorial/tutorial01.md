## Bare-bones example

his is a minimal example that shows the basic WireViz syntax. A WireViz file consists of three sections: `connectors:` and `cables:` specify the components to be used, while `connections:` creates the links between components.

### `connectors`

Each connector has a designator (a unique name) and can contain various parameters. The minimum requirement is `pincount`, specifying the number of ports to which wires can be attached.

### `cables`

A cable is a collection of wires (for bundles of individual wires, see below). Just like connectors, they have a unique designator and a `wirecount`, i.e. the number of wires inside the cable.

In this example, the cable is also given a `length`. This length must be specified in meters.

### `connections`

This section is a list of connection sets. In this example, only one set is necessary.

The set consists of three parts: A starting connector (`X1`), a cable (`W1`) and a destination connector (`X2`).

This set specifies that connectos 1 through 4 of `X1` should go straight through wires 1 through 4 of `W1` and into connectors 1 through 4 of `X2`: A straight 1-to-1 wiring.

For other ways of defining connection sets, see below.
