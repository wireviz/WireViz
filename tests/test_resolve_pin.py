# -*- coding: utf-8 -*-

"""Tests for Connector.resolve_pin() and loop pin resolution.

Covers the fix for https://github.com/wireviz/WireViz/issues/432
and related safety-critical pin resolution correctness.
"""

import pytest

from wireviz.DataClasses import Connector


def make_connector(pins=None, pinlabels=None, loops=None, **kwargs):
    """Helper to build a Connector with minimal required fields."""
    args = {"name": "X1"}
    if pins is not None:
        args["pins"] = pins
    if pinlabels is not None:
        args["pinlabels"] = pinlabels
    if loops is not None:
        args["loops"] = loops
    args.update(kwargs)
    return Connector(**args)


# --- resolve_pin() happy paths ---


class TestResolvePinHappyPaths:
    def test_pin_number_passthrough(self):
        """Pin number that exists in self.pins returns unchanged."""
        c = make_connector(pins=[1, 2, 3])
        assert c.resolve_pin(2) == 2

    def test_label_resolves_to_pin_number(self):
        """Pin label resolves to the corresponding pin number."""
        c = make_connector(pins=[1, 2, 3], pinlabels=["VCC", "GND", "SIG"])
        assert c.resolve_pin("GND") == 2

    def test_label_with_non_sequential_pins(self):
        """Labels work correctly even when pin numbers are non-sequential."""
        c = make_connector(pins=[10, 20, 30], pinlabels=["A", "B", "C"])
        assert c.resolve_pin("B") == 20

    def test_value_in_both_lists_same_position(self):
        """Value that exists in both pins and pinlabels at the same index."""
        c = make_connector(pins=["A", "B", "C"], pinlabels=["A", "X", "Y"])
        assert c.resolve_pin("A") == "A"

    def test_empty_pinlabels_falls_through(self):
        """When pinlabels is empty, pin numbers still resolve."""
        c = make_connector(pins=[1, 2, 3], pinlabels=[])
        assert c.resolve_pin(3) == 3


# --- resolve_pin() error paths ---


class TestResolvePinErrors:
    def test_unknown_pin_raises(self):
        """Resolving a pin that doesn't exist in either list raises."""
        c = make_connector(pins=[1, 2, 3], pinlabels=["A", "B", "C"])
        with pytest.raises(Exception, match="Unknown pin"):
            c.resolve_pin("NONEXISTENT")

    def test_unknown_number_raises(self):
        """Resolving a pin number not in self.pins raises."""
        c = make_connector(pins=[1, 2, 3])
        with pytest.raises(Exception, match="Unknown pin"):
            c.resolve_pin(99)

    def test_ambiguous_pin_different_positions(self):
        """Value in both pins and pinlabels at different positions raises."""
        c = make_connector(pins=["A", "B", "C"], pinlabels=["X", "A", "Y"])
        with pytest.raises(Exception, match="exists in both"):
            c.resolve_pin("A")

    def test_duplicate_label_only_in_labels(self):
        """Duplicate label in pinlabels (label-only path) raises."""
        c = make_connector(pins=[1, 2, 3], pinlabels=["A", "B", "A"])
        with pytest.raises(Exception, match="defined more than once"):
            c.resolve_pin("A")

    def test_duplicate_label_in_both_lists(self):
        """Duplicate label detected even when value also exists in pins (C-2 fix)."""
        c = make_connector(pins=["A", "B", "C"], pinlabels=["A", "X", "A"])
        with pytest.raises(Exception, match="defined more than once"):
            c.resolve_pin("A")


# --- Loop resolution ---


class TestLoopResolution:
    def test_loop_with_labels(self):
        """Loops specified with pin labels resolve to pin numbers."""
        c = make_connector(
            pins=[1, 2, 3, 4],
            pinlabels=["VCC", "GND", "TX", "RX"],
            loops=[["VCC", "GND"]],
        )
        assert c.loops == [[1, 2]]

    def test_loop_with_mixed_number_and_label(self):
        """Loop with one pin number and one label resolves correctly."""
        c = make_connector(
            pins=[1, 2, 3, 4],
            pinlabels=["VCC", "GND", "TX", "RX"],
            loops=[[1, "GND"]],
        )
        assert c.loops == [[1, 2]]

    def test_loop_with_non_sequential_pins(self):
        """Loops resolve correctly with non-sequential pin numbering."""
        c = make_connector(
            pins=[10, 20, 30, 40],
            pinlabels=["VCC", "GND", "TX", "RX"],
            loops=[["VCC", "GND"]],
        )
        assert c.loops == [[10, 20]]

    def test_loop_self_reference_raises(self):
        """A loop from a pin to itself raises (I-2 fix)."""
        with pytest.raises(Exception, match="to itself"):
            make_connector(
                pins=[1, 2, 3],
                pinlabels=["A", "B", "C"],
                loops=[["A", "A"]],
            )

    def test_loop_self_reference_via_label_and_number(self):
        """Self-loop detected even when specified as label + number."""
        with pytest.raises(Exception, match="to itself"):
            make_connector(
                pins=[1, 2, 3],
                pinlabels=["A", "B", "C"],
                loops=[[2, "B"]],
            )

    def test_loop_activates_pins(self):
        """Loop-connected pins are marked visible (for hide_disconnected_pins)."""
        c = make_connector(
            pins=[1, 2, 3, 4],
            pinlabels=["VCC", "GND", "TX", "RX"],
            loops=[["TX", "RX"]],
        )
        assert c.visible_pins.get(3) is True
        assert c.visible_pins.get(4) is True
        # Unconnected pins should not be in visible_pins
        assert 1 not in c.visible_pins

    def test_multiple_loops(self):
        """Multiple loops on the same connector all resolve correctly."""
        c = make_connector(
            pins=[1, 2, 3, 4, 5, 6],
            pinlabels=["A", "B", "C", "D", "E", "F"],
            loops=[["A", "B"], ["E", "F"]],
        )
        assert c.loops == [[1, 2], [5, 6]]


# --- Loop rendering: non-sequential pins (C-1 fix) ---


class TestLoopRendering:
    """Verify that the GraphViz output uses port indices, not pin numbers.

    This is the critical C-1 fix: Harness.py must convert resolved pin
    numbers to 1-based position indices for GraphViz port references.
    """

    def _render_gv(self, yaml_str):
        """Parse a YAML string through WireViz and return the GV source."""
        import yaml

        from wireviz.DataClasses import Metadata, Options, Tweak
        from wireviz.Harness import Harness

        data = yaml.safe_load(yaml_str)
        harness = Harness(
            metadata=Metadata(data.get("metadata", {})),
            options=Options(**data.get("options", {})),
            tweak=Tweak(**data.get("tweak", {})),
        )
        for name, conn_data in data.get("connectors", {}).items():
            harness.add_connector(name, **conn_data)
        for name, cable_data in data.get("cables", {}).items():
            harness.add_cable(name, **cable_data)

        graph = harness.create_graph()
        return graph.source

    def test_non_sequential_pins_use_indices(self):
        """C-1 regression test: loops must use port indices, not pin numbers.

        With pins: [10, 20, 30, 40], a loop between pins 10 and 20
        must produce port references p1 and p2 (1-based indices),
        NOT p10 and p20 (pin numbers).
        """
        yaml_str = """
connectors:
  X1:
    pins: [10, 20, 30, 40]
    pinlabels: [VCC, GND, TX, RX]
    loops:
      - [VCC, GND]
cables:
  W1:
    wirecount: 2
    colors: [BK, RD]
connections:
  -
    - X1: [TX, RX]
    - W1: [1-2]
"""
        gv = self._render_gv(yaml_str)
        # The loop should reference p1 and p2 (positions), not p10 and p20.
        # Look specifically for the loop edge pattern with port names.
        import re

        loop_edges = re.findall(r"X1:p(\d+)\w:\w -- X1:p(\d+)\w:\w", gv)
        assert len(loop_edges) == 1, f"Expected 1 loop edge, found {len(loop_edges)}"
        idx_a, idx_b = loop_edges[0]
        # Pin 10 is at index 1, pin 20 is at index 2
        assert idx_a == "1" and idx_b == "2", (
            f"Loop ports should be p1/p2 (indices), got p{idx_a}/p{idx_b}"
        )

    def test_sequential_pins_still_work(self):
        """Sequential pins (the common case) continue to work correctly."""
        yaml_str = """
connectors:
  X1:
    pinlabels: [VCC, GND, TX, RX]
    loops:
      - [VCC, GND]
cables:
  W1:
    wirecount: 2
    colors: [BK, RD]
connections:
  -
    - X1: [TX, RX]
    - W1: [1-2]
"""
        gv = self._render_gv(yaml_str)
        # With sequential pins [1,2,3,4], p1/p2 are both the index and number
        assert ":p1" in gv
        assert ":p2" in gv


# --- Harness.connect() delegation (I-1 fix) ---


class TestHarnessConnectDelegation:
    """Verify Harness.connect() now delegates to Connector.resolve_pin()."""

    def test_connect_resolves_labels(self):
        """Wire connections using pin labels resolve correctly."""
        from wireviz.DataClasses import Cable, Metadata, Options, Tweak
        from wireviz.Harness import Harness

        harness = Harness(
            metadata=Metadata({}),
            options=Options(),
            tweak=Tweak(),
        )
        harness.add_connector(
            "X1", pins=[1, 2, 3], pinlabels=["VCC", "GND", "SIG"]
        )
        harness.add_connector("X2", pins=[1, 2, 3])
        harness.add_cable("W1", wirecount=1, colors=["BK"])

        # Connect using a label on the from side
        harness.connect("X1", "SIG", "W1", 1, "X2", 1)

        # The connection should store the resolved pin number (3), not the label
        conn = harness.cables["W1"].connections[0]
        assert conn.from_pin == 3

    def test_connect_rejects_unknown_pin(self):
        """Wire connections with unknown pins raise via resolve_pin()."""
        from wireviz.DataClasses import Metadata, Options, Tweak
        from wireviz.Harness import Harness

        harness = Harness(
            metadata=Metadata({}),
            options=Options(),
            tweak=Tweak(),
        )
        harness.add_connector("X1", pins=[1, 2, 3])
        harness.add_connector("X2", pins=[1, 2, 3])
        harness.add_cable("W1", wirecount=1, colors=["BK"])

        with pytest.raises(Exception, match="Unknown pin"):
            harness.connect("X1", 99, "W1", 1, "X2", 1)


# --- Pin type coercion (C-3 fix) ---


class TestPinTypeCoercion:
    """Verify that YAML quoting differences don't break pin lookups.

    YAML safe_load() parses unquoted 1 as int(1) and quoted "1" as str("1").
    The C-3 fix normalizes all pin-like fields at the dataclass boundary
    so downstream code always sees consistent types.
    """

    def test_str_numeric_pins_normalize_to_int(self):
        """String numeric pins are coerced to int."""
        c = make_connector(pins=["1", "2", "3"])
        assert c.pins == [1, 2, 3]
        assert all(isinstance(p, int) for p in c.pins)

    def test_mixed_type_pins_normalize(self):
        """Mix of int and str numeric pins all become int."""
        c = make_connector(pins=[1, "2", 3])
        assert c.pins == [1, 2, 3]

    def test_leading_zeros_normalize(self):
        """Leading zeros normalize to plain ints."""
        c = make_connector(pins=["01", "02", "03"])
        assert c.pins == [1, 2, 3]

    def test_non_numeric_pins_stay_str(self):
        """Non-numeric pins remain as strings."""
        c = make_connector(pins=["A", "B", "C"])
        assert c.pins == ["A", "B", "C"]
        assert all(isinstance(p, str) for p in c.pins)

    def test_duplicate_after_normalization_raises(self):
        """Pins that become duplicates after normalization are caught."""
        with pytest.raises(Exception, match="Pins are not unique"):
            make_connector(pins=[1, "1"])

    def test_pinlabels_normalize(self):
        """Pinlabels are also normalized."""
        c = make_connector(pins=[1, 2], pinlabels=["10", "20"])
        assert c.pinlabels == [10, 20]

    def test_loop_pins_normalize(self):
        """Loop pin references are normalized before resolve_pin()."""
        c = make_connector(
            pins=[1, 2, 3, 4],
            loops=[["1", "2"]],
        )
        # Loops are resolved to pin numbers (which are already int)
        assert c.loops == [[1, 2]]

    def test_str_loop_pins_match_auto_generated_int_pins(self):
        """String loop pins match auto-generated sequential int pins.

        This is the core regression: without normalization,
        "1" in [1, 2, 3] is False, so resolve_pin() would fail.
        """
        c = make_connector(
            pincount=4,
            loops=[["1", "3"]],
        )
        assert c.loops == [[1, 3]]

    def test_wirelabels_normalize(self):
        """Cable wirelabels are normalized."""
        from wireviz.DataClasses import Cable

        cable = Cable(name="W1", wirecount=3, colors=["BK", "RD", "GN"],
                      wirelabels=["1", "2", "3"])
        assert cable.wirelabels == [1, 2, 3]

    def test_quoted_pin_yaml_renders(self):
        """Integration: quoted pins in YAML render without error."""
        import yaml

        from wireviz.DataClasses import Metadata, Options, Tweak
        from wireviz.Harness import Harness

        yaml_str = """
connectors:
  X1:
    pins: ["1", "2", "3"]
    pinlabels: [VCC, GND, SIG]
    loops:
      - ["1", "2"]
cables:
  W1:
    wirecount: 1
    colors: [BK]
connections:
  -
    - X1: ["3"]
    - W1: [1]
"""
        data = yaml.safe_load(yaml_str)
        harness = Harness(
            metadata=Metadata(data.get("metadata", {})),
            options=Options(**data.get("options", {})),
            tweak=Tweak(**data.get("tweak", {})),
        )
        for name, conn_data in data.get("connectors", {}).items():
            harness.add_connector(name, **conn_data)
        for name, cable_data in data.get("cables", {}).items():
            harness.add_cable(name, **cable_data)

        # Should not raise — the whole point of C-3
        graph = harness.create_graph()
        assert graph is not None
