# -*- coding: utf-8 -*-

import re
from pathlib import Path
from typing import Dict, List, Optional

from wireviz import APP_NAME, APP_URL, __version__, wv_colors
from wireviz.DataClasses import Metadata, Options
from wireviz.wv_gv_html import html_line_breaks
from wireviz.wv_helper import (
    flatten2d,
    open_file_read,
    smart_file_resolve,
)


def generate_html_output(
    svg_input: str,
    output_dir: Optional[Path],
    bom_list: List[List[str]],
    metadata: Metadata,
    options: Options,
) -> str:
    # load HTML template
    template_name = metadata.get("template", {}).get("name")
    builtin_template_directory = Path(__file__).parent / "templates"  # built-in template directory
    if template_name:
        possible_paths = []
        # if relative path to template was provided, check directory of YAML file first
        if output_dir is not None:
            possible_paths.append(output_dir)

        possible_paths.append(builtin_template_directory)  # fallback
        template_file = smart_file_resolve(f"{template_name}.html", possible_paths)
    else:
        # fallback to built-in simple template if no template was provided
        template_file = builtin_template_directory / "simple.html"

    html = open_file_read(template_file).read()

    # embed SVG diagram
    svg_data = re.sub(
        "^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>",
        "<!-- XML and DOCTYPE declarations from SVG file removed -->",
        svg_input,
        1,
    )

    # generate BOM table
    bom = flatten2d(bom_list)

    # generate BOM header (might be at the top or bottom of the table)
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
            row_html = f'{row_html}    <td class="{td_class}">{item}</td>\n'
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
        "<!-- %bgcolor% -->": wv_colors.translate_color(options.bgcolor, "hex"),
        "<!-- %diagram% -->": svg_data,
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
    return pattern.sub(lambda match: replacements[match.group(0)], html)
