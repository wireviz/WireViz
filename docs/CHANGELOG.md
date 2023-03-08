# Change Log

## [0.3.2](https://github.com/formatc1702/WireViz/tree/v0.3.2) (2021-11-27)

### Hotfix

- Adjust GraphViz generation code for compatibility with v0.18 of the `graphviz` Python package ([#258](https://github.com/formatc1702/WireViz/issues/258), [#262](https://github.com/formatc1702/WireViz/pull/261))

## [0.3.1](https://github.com/formatc1702/WireViz/tree/v0.3.1) (2021-10-25)

### Hotfix

- Assign generic harness title when using WireViz as a module and not specifying an output file name ([#253](https://github.com/formatc1702/WireViz/issues/253), [#254](https://github.com/formatc1702/WireViz/pull/254))

## [0.3](https://github.com/formatc1702/WireViz/tree/v0.3) (2021-10-11)

### New features

- Allow referencing a cable's/bundle's wires by color or by label ([#70](https://github.com/formatc1702/WireViz/issues/70), [#169](https://github.com/formatc1702/WireViz/issues/169), [#193](https://github.com/formatc1702/WireViz/issues/193), [#194](https://github.com/formatc1702/WireViz/pull/194))
- Allow additional BOM items within components ([#50](https://github.com/formatc1702/WireViz/issues/50), [#115](https://github.com/formatc1702/WireViz/pull/115))
- Add support for length units in cables and wires ([#7](https://github.com/formatc1702/WireViz/issues/7), [#196](https://github.com/formatc1702/WireViz/pull/196) (with work from [#161](https://github.com/formatc1702/WireViz/pull/161), [#162](https://github.com/formatc1702/WireViz/pull/162), [#171](https://github.com/formatc1702/WireViz/pull/171)), [#198](https://github.com/formatc1702/WireViz/pull/198), [#205](https://github.com/formatc1702/WireViz/issues/205). [#206](https://github.com/formatc1702/WireViz/pull/206))
- Add option to define connector pin colors ([#53](https://github.com/formatc1702/WireViz/issues/53), [#141](https://github.com/formatc1702/WireViz/pull/141))
- Remove HTML links from the input attributes ([#164](https://github.com/formatc1702/WireViz/pull/164))
- Add harness metadata section ([#158](https://github.com/formatc1702/WireViz/issues/158), [#214](https://github.com/formatc1702/WireViz/pull/214))
- Add support for supplier and supplier part number information ([#240](https://github.com/formatc1702/WireViz/issues/240), [#241](https://github.com/formatc1702/WireViz/pull/241/))
- Add graph rendering options (colors, font, color name display style, ...) ([#158](https://github.com/formatc1702/WireViz/issues/158), [#214](https://github.com/formatc1702/WireViz/pull/214))
- Add support for background colors for cables and connectors, as well as for some individual cells ([#210](https://github.com/formatc1702/WireViz/issues/210), [#219](https://github.com/formatc1702/WireViz/pull/219))
- Add optional tweaking of the .gv output ([#215](https://github.com/formatc1702/WireViz/pull/215)) (experimental)


## Misc. fixes

- Remove case-sensitivity issues with pin names and labels ([#160](https://github.com/formatc1702/WireViz/issues/160), [#229](https://github.com/formatc1702/WireViz/pull/229))
- Improve type hinting ([#156](https://github.com/formatc1702/WireViz/issues/156), [#163](https://github.com/formatc1702/WireViz/pull/163))
- Move BOM management and HTML functions to separate modules ([#151](https://github.com/formatc1702/WireViz/issues/151), [#192](https://github.com/formatc1702/WireViz/pull/192))
- Simplify BOM code ([#197](https://github.com/formatc1702/WireViz/pull/197))
- Bug fixes ([#218](https://github.com/formatc1702/WireViz/pull/218), [#221](https://github.com/formatc1702/WireViz/pull/221))

## Known issues

- Including images in the harness may lead to issues in the following cases: ([#189](https://github.com/formatc1702/WireViz/pull/189), [#220](https://github.com/formatc1702/WireViz/issues/220))
  - When using the `-o`/`--output_file` CLI option, specifying an output path in a different directory from the input file
  - When using the `--prepend-file` CLI option, specifying a prepend file in a different directory from the mail input file

## [0.2](https://github.com/formatc1702/WireViz/tree/v0.2) (2020-10-17)

### Backward incompatible changes

- Change names of connector attributes ([#77](https://github.com/formatc1702/WireViz/issues/77), [#105](https://github.com/formatc1702/WireViz/pull/105))
  - `pinnumbers` is now `pins`
  - `pinout` is now `pinlabels`
- Remove ferrules as a separate connector type ([#78](https://github.com/formatc1702/WireViz/issues/78), [#102](https://github.com/formatc1702/WireViz/pull/102))
  - Simple connectors like ferrules are now defined using the `style: simple` attribute
- Change the way loops are defined ([#79](https://github.com/formatc1702/WireViz/issues/79), [#75](https://github.com/formatc1702/WireViz/pull/75))
  - Wires looping between two pins of the same connector are now handled via the connector's `loops` attribute.

See the [syntax description](syntax.md) for details.


### New features

- Add bidirectional AWG/mm2 conversion ([#40](https://github.com/formatc1702/WireViz/issues/40), [#41](https://github.com/formatc1702/WireViz/pull/41))
- Add support for part numbers ([#11](https://github.com/formatc1702/WireViz/pull/11), [#114](https://github.com/formatc1702/WireViz/issues/114), [#121](https://github.com/formatc1702/WireViz/pull/121))
- Add support for multicolored wires ([#12](https://github.com/formatc1702/WireViz/issues/12), [#17](https://github.com/formatc1702/WireViz/pull/17), [#96](https://github.com/formatc1702/WireViz/pull/96), [#131](https://github.com/formatc1702/WireViz/issues/131), [#132](https://github.com/formatc1702/WireViz/pull/132))
- Add support for images ([#27](https://github.com/formatc1702/WireViz/issues/27), [#153](https://github.com/formatc1702/WireViz/pull/153))
- Add ability to export data directly to other programs ([#55](https://github.com/formatc1702/WireViz/pull/55))
- Add support for line breaks in various fields ([#49](https://github.com/formatc1702/WireViz/issues/49), [#64](https://github.com/formatc1702/WireViz/pull/64))
- Allow using connector pin names to define connections ([#72](https://github.com/formatc1702/WireViz/issues/72), [#139](https://github.com/formatc1702/WireViz/issues/139), [#140](https://github.com/formatc1702/WireViz/pull/140))
- Make defining connection sets easier and more flexible ([#67](https://github.com/formatc1702/WireViz/issues/67), [#75](https://github.com/formatc1702/WireViz/pull/75))
- Add new command line options ([#167](https://github.com/formatc1702/WireViz/issues/167), [#173](https://github.com/formatc1702/WireViz/pull/173))
- Add new features to `build_examples.py` ([#118](https://github.com/formatc1702/WireViz/pull/118))
- Add new colors ([#103](https://github.com/formatc1702/WireViz/pull/103), [#113](https://github.com/formatc1702/WireViz/pull/113), [#144](https://github.com/formatc1702/WireViz/issues/144), [#145](https://github.com/formatc1702/WireViz/pull/145))
- Improve documentation ([#107](https://github.com/formatc1702/WireViz/issues/107), [#111](https://github.com/formatc1702/WireViz/pull/111))


### Misc. fixes

- Improve BOM generation
- Add various input sanity checks
- Improve HTML output ([#66](https://github.com/formatc1702/WireViz/issues/66), [#136](https://github.com/formatc1702/WireViz/pull/136), [#95](https://github.com/formatc1702/WireViz/pull/95), [#177](https://github.com/formatc1702/WireViz/pull/177))
- Fix node rendering bug ([#69](https://github.com/formatc1702/WireViz/issues/69), [#104](https://github.com/formatc1702/WireViz/pull/104))
- Improve shield rendering ([#125](https://github.com/formatc1702/WireViz/issues/125), [#126](https://github.com/formatc1702/WireViz/pull/126))
- Add GitHub Linguist overrides ([#146](https://github.com/formatc1702/WireViz/issues/146), [#154](https://github.com/formatc1702/WireViz/pull/154))


## [0.1](https://github.com/formatc1702/WireViz/tree/v0.1) (2020-06-29)

- Initial release
