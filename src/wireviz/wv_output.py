# -*- coding: utf-8 -*-

import base64
import re
from pathlib import Path
from typing import List, Union

import jinja2

import wireviz  # for doing wireviz.__file__
from wireviz.wv_dataclasses import Metadata, Options

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


def get_template_html(template_name):
    template_file_path = jinja2.FileSystemLoader(
        Path(wireviz.__file__).parent / "templates"
    )
    jinja_env = jinja2.Environment(loader=template_file_path)

    return jinja_env.get_template(template_name + ".html")


def generate_html_output(
    filename: Path,
    bom: List[List[str]],
    metadata: Metadata,
    options: Options,
):
    print("Generating html output")
    template_name = metadata.get("template", {}).get("name", "simple")

    # embed SVG diagram
    with filename.with_suffix(".svg").open("r") as f:
        svgdata = re.sub(
            "^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>",
            "<!-- XML and DOCTYPE declarations from SVG file removed -->",
            f.read(),
            1,
        )

    # generate BOM table
    # generate BOM header (may be at the top or bottom of the table)
    bom_reversed = False if template_name == "simple" else True
    bom_header = bom[0]
    bom_columns = [
        "bom_col_{}".format("id" if c == "#" else c.lower()) for c in bom_header
    ]
    bom_content = bom[1:]
    if bom_reversed:
        bom_content.reverse()


    if metadata:
        sheet_current = metadata["sheet_current"]
        sheet_total = metadata["sheet_total"]
    else:
        sheet_current = 1
        sheet_total = 1

    replacements = {
        "generator": f"{wireviz.APP_NAME} {wireviz.__version__} - {wireviz.APP_URL}",
        "fontname": options.fontname,
        "bgcolor": options.bgcolor.html,
        "diagram": svgdata,
        "sheet_current": sheet_current,
        "sheet_total": sheet_total,
        "bom_reversed": bom_reversed,
        "bom_header": bom_header,
        "bom_content": bom_content,
        "bom_columns": bom_columns,
        "bom_length": len(bom_content),
        "titleblock_rows": 9,
    }

    # prepare metadata replacements
    added_metadata = {
        "revisions": [],
        "authors": [],
        "sheetsize": "sheetsize_default",
    }
    if metadata:
        for item, contents in metadata.items():
            if item == "revisions":
                added_metadata["revisions"] = [
                    {"rev": rev, **v} for rev, v in contents.items()
                ]
            elif item == "authors":
                added_metadata["authors"] = [
                    {"row": row, **v} for row, v in contents.items()
                ]
            elif item == "pn":
                added_metadata[item] = f'{contents}-{metadata.get("sheet_name")}'
            elif item == "template":
                added_metadata["sheetsize"] = contents.get(
                    "sheetsize", "sheetsize_default"
                )
            else:
                added_metadata[item] = contents

    replacements = {**replacements, **added_metadata}

    # prepare BOM
    bom_template = get_template_html("bom")
    replacements["bom"] = bom_template.render(replacements)

    # prepare titleblock
    titleblock_template = get_template_html("titleblock")
    replacements["titleblock"] = titleblock_template.render(replacements)

    # generate page template
    page_template = get_template_html(template_name)
    page_rendered = page_template.render(replacements)

    # save generated file
    filename.with_suffix(".html").open("w").write(page_rendered)
