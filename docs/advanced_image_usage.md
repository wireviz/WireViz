# Advanced Image Usage

In rare cases when the [ordinary image scaling functionality](syntax.md#images) is insufficient, a couple of extra optional image attributes can be set to offer extra image cell space and scaling functionality when combined with the image dimension attributes `width` and `height`, but in most cases their default values below are sufficient:
- `scale: <str>` (how an image will use the available cell space) is default `false` if no dimension is set, or `true` if only one dimension is set, or `both` if both dimensions are set.
- `fixedsize: <bool>` (scale to fixed size or expand to minimum size) is default `false` when no dimension is set or if a `scale` value is set, and `true` otherwise.
- When `fixedsize` is true and only one dimension is set, then the other dimension is calculated using the image aspect ratio. If reading the aspect ratio fails, then 1:1 ratio is assumed.

See explanations of all supported values for these attributes in subsections below.

## The effect of `fixedsize` boolean values

- When `false`, any `width` or `height` values are _minimum_ values used to expand the image cell size for more available space, but cell contents or other size demands in the table might expand this cell even more than specified by `width` or `height`.
- When `true`, both `width` and `height` values are required by Graphwiz and specify the fixed size of the image cell, distorting any image inside if it don't fit. Any borders are normally drawn around the fixed size, and therefore, WireViz enclose the image cell in an extra table without borders when `fixedsize` is true to keep the borders around the outer non-fixed cell.

## The effect of `scale` string values:

- When `false`, the image is not scaled.
- When `true`, the image is scaled proportionally to fit within the available image cell space.
- When `width`, the image width is expanded (height is normally unchanged) to fill the available image cell space width.
- When `height`, the image height is expanded (width is normally unchanged) to fill the available image cell space height.
- When `both`, both image width and height are expanded independently to fill the available image cell space.

In all cases (except `true`) the image might get distorted when a specified fixed image cell size limits the available space to less than what an unscaled image needs.

In the WireViz diagrams there are no other space demanding cells in the same row, and hence, there are never extra available image cell space height unless a greater image cell `height` also is set.

## Usage examples

All examples of `image` attribute combinations below also require the mandatory `src` attribute to be set.

- Expand the image proportionally to fit within a minimum height and the node width:
```yaml
  height: 100      # Expand image cell to this minimum height
  fixedsize: false # Avoid scaling to a fixed size
  # scale default value is true in this case
```

- Increase the space around the image by expanding the image cell space (width and/or height) to a larger value without scaling the image:
```yaml
  width:  200  # Expand image cell to this minimum width
  height: 100  # Expand image cell to this minimum height
  scale: false # Avoid scaling the image
  # fixedsize default value is false in this case
```

- Stretch the image width to fill the available space in the node:
```yaml
  scale: width # Expand image width to fill the available image cell space
  # fixedsize default value is false in this case
```

- Stretch the image height to a minimum value:
```yaml
  height: 100   # Expand image cell to this minimum height
  scale: height # Expand image height to fill the available image cell space
  # fixedsize default value is false in this case
```

## How Graphviz support this image scaling

The connector and cable nodes are rendered using a HTML `<table>` containing an image cell `<td>` with `width`, `height`, and `fixedsize` attributes containing an image `<img>` with `src` and `scale` attributes. See also the [Graphviz doc](https://graphviz.org/doc/info/shapes.html#html), but note that WireViz uses default values as described above.
