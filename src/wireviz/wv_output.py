# -*- coding: utf-8 -*-

import base64
import re
from pathlib import Path
from typing import Dict, List, Union

import wireviz  # for doing wireviz.__file__
from wireviz import APP_NAME, APP_URL, __version__
from wireviz.wv_dataclasses import Metadata, Options
from wireviz.wv_utils import (
    html_line_breaks,
    open_file_read,
    open_file_write,
    smart_file_resolve,
)

mime_subtype_replacements = {"jpg": "jpeg", "tif": "tiff"}


def embed_svg_images(svg_in: str, base_path: Union[str, Path] = Path.cwd()) -> str:
    images_b64 = {}  # cache of base64-encoded images

    def image_tag(pre: str, url: str, post: str) -> str:
        return f'<image{pre} xlink:href="{url}"{post}>'

    def replace(match: re.Match) -> str:
        imgurl = match["URL"]
        if not imgurl in images_b64:  # only encode/cache every unique URL once
            imgurl_abs = (Path(base_path) / imgurl).resolve()
            image = imgurl_abs.read_bytes()
            images_b64[imgurl] = base64.b64encode(image).decode("utf-8")
        return image_tag(
            match["PRE"] or "",
            f"data:image/{get_mime_subtype(imgurl)};base64, {images_b64[imgurl]}",
            match["POST"] or "",
        )

    pattern = re.compile(
        image_tag(r"(?P<PRE> [^>]*?)?", r'(?P<URL>[^"]*?)', r"(?P<POST> [^>]*?)?"),
        re.IGNORECASE,
    )
    return pattern.sub(replace, svg_in)


def get_mime_subtype(filename: Union[str, Path]) -> str:
    mime_subtype = Path(filename).suffix.lstrip(".").lower()
    if mime_subtype in mime_subtype_replacements:
        mime_subtype = mime_subtype_replacements[mime_subtype]
    return mime_subtype


def embed_svg_images_file(
    filename_in: Union[str, Path], overwrite: bool = True
) -> None:
    filename_in = Path(filename_in).resolve()
    filename_out = filename_in.with_suffix(".b64.svg")
    filename_out.write_text(
        embed_svg_images(filename_in.read_text(), filename_in.parent)
    )
    if overwrite:
        filename_out.replace(filename_in)


def generate_html_output(
    filename: Union[str, Path],
    bom: List[List[str]],
    metadata: Metadata,
    options: Options,
):
    # load HTML template
    templatename = metadata.get("template", {}).get("name")
    if templatename:
        # if relative path to template was provided,
        # check directory of YAML file first, fall back to built-in template directory
        templatefile = smart_file_resolve(
            f"{templatename}.html",
            [Path(filename).parent, Path(__file__).parent / "templates"],
        )
    else:
        # fall back to built-in simple template if no template was provided
        templatefile = Path(wireviz.__file__).parent / "templates/simple.html"

    html = open_file_read(templatefile).read()

    # embed SVG diagram
    with open_file_read(f"{filename}.tmp.svg") as file:
        svgdata = re.sub(
            "^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>",
            "<!-- XML and DOCTYPE declarations from SVG file removed -->",
            file.read(),
            1,
        )

    # generate BOM table
    # generate BOM header (may be at the top or bottom of the table)
    bom_header_html = "  <tr>\n"
    for item in bom[0]:
        th_class = f"bom_col_{item.lower()}"
        bom_header_html = f'{bom_header_html}    <th class="{th_class}">{item}</th>\n'
    bom_header_html = f"{bom_header_html}  </tr>\n"

    # generate BOM contents
    bom_contents = []
    for row in bom[1:]:
        row_html = "  <tr>\n"
        for i, item in enumerate(row):
            td_class = f"bom_col_{bom[0][i].lower()}"
            row_html = f'{row_html}    <td class="{td_class}">{item if item is not None else ""}</td>\n'
        row_html = f"{row_html}  </tr>\n"
        bom_contents.append(row_html)

    bom_html = (
        '<table class="bom">\n' + bom_header_html + "".join(bom_contents) + "</table>\n"
    )
    bom_html_reversed = (
        '<table class="bom">\n'
        + "".join(list(reversed(bom_contents)))
        + bom_header_html
        + "</table>\n"
    )

    # prepare simple replacements
    replacements = {
        "<!-- %generator% -->": f"{APP_NAME} {__version__} - {APP_URL}",
        "<!-- %fontname% -->": options.fontname,
        "<!-- %bgcolor% -->": options.bgcolor.html,
        "<!-- %diagram% -->": svgdata,
        "<!-- %bom% -->": bom_html,
        "<!-- %bom_reversed% -->": bom_html_reversed,
        "<!-- %sheet_current% -->": "1",  # TODO: handle multi-page documents
        "<!-- %sheet_total% -->": "1",  # TODO: handle multi-page documents
    }

    # prepare metadata replacements
    if metadata:
        for item, contents in metadata.items():
            if isinstance(contents, (str, int, float)):
                replacements[f"<!-- %{item}% -->"] = html_line_breaks(str(contents))
            elif isinstance(contents, Dict):  # useful for authors, revisions
                for index, (category, entry) in enumerate(contents.items()):
                    if isinstance(entry, Dict):
                        replacements[f"<!-- %{item}_{index+1}% -->"] = str(category)
                        for entry_key, entry_value in entry.items():
                            replacements[
                                f"<!-- %{item}_{index+1}_{entry_key}% -->"
                            ] = html_line_breaks(str(entry_value))

        replacements['"sheetsize_default"'] = '"{}"'.format(
            metadata.get("template", {}).get("sheetsize", "")
        )
        # include quotes so no replacement happens within <style> definition

    # perform replacements
    # regex replacement adapted from:
    # https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729

    # longer replacements first, just in case
    replacements_sorted = sorted(replacements, key=len, reverse=True)
    replacements_escaped = map(re.escape, replacements_sorted)
    pattern = re.compile("|".join(replacements_escaped))
    html = pattern.sub(lambda match: replacements[match.group(0)], html)

    open_file_write(f"{filename}.html").write(html)
