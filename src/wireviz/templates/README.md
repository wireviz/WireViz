# HTML Output Templates

This is the standard folder where WireViz looks for an HTML output template file.

## Which HTML Output Template File is Used?

A named HTML output template can optionally be specified as
`metadata.template.name` in the YAML input:
```yaml
metadata:
  template:
    name: din-6771
```
In the case above, WireViz will search for a template file named
`din-6771.html` in these folders:
1. In the same folder as the YAML input file.
2. In this standard template folder.

If no HTML output template is specified, the `simple` template is assumed
(i.e. filename `simple.html`, and in this case,
only the standard template folder is searched).

## Placeholders in HTML Output Templates

HTML output template files might contain placeholders that will be replaced by
generated text by WireViz when producing HTML output based on such a template.
A placeholder starts with `<!-- %`, followed by a keyword, and finally `% -->`.
Note that there must be one single space between `--` and `%` at both ends.

| Placeholder | Replaced by |
| --- | --- |
| `<!-- %generator% -->` | The application name, version, and URL |
| `<!-- %fontname% -->`  | The value of `options.fontname` |
| `<!-- %bgcolor% -->`   | The HEX color translation of `options.bgcolor` |
| `<!-- %filename% -->`  | The output path and filename without extension |
| `<!-- %filename_stem% -->` | The output filename without path nor extension |
| `<!-- %bom% -->`           | BOM as HTML table with headers at top |
| `<!-- %bom_reversed% -->`  | Reversed BOM as HTML table with headers at bottom |
| `<!-- %sheet_current% -->` | `1` (multi-page documents not yet supported) |
| `<!-- %sheet_total% -->`   | `1` (multi-page documents not yet supported) |
| `<!-- %diagram% -->`       | Embedded SVG diagram as valid HTML |
| `<!-- %diagram_png_base64% -->` | Embedded base64 encoded PNG diagram as URI |
| `<!-- %{item}% -->`             | String or numeric value of `metadata.{item}` |
| `<!-- %{item}_{i}% -->`         | Category number `{i}` within dict value of `metadata.{item}` |
| `<!-- %{item}_{i}_{key}% -->`   | Value of `metadata.{item}.{category}.{key}` |

Note that `{item}`, `{category}` and `{key}` in the description above can be
any valid YAML key, and `{i}` is an integer representing the 1-based index of
category entries in a dict `metadata.{item}` entry.
The `{` and `}` characters are not literally part of the syntax, just used in
this documentation to enclose the variable parts of the keywords.
