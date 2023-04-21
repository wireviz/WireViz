# -*- coding: utf-8 -*-

import base64
import re
from pathlib import Path
from typing import Dict, List, Union
import logging

from weasyprint import HTML

import wireviz  # for doing wireviz.__file__
from wireviz.wv_bom import bom_list
from wireviz.wv_utils import bom2tsv
from wireviz.wv_dataclasses import Metadata, Options
from wireviz.wv_harness_quantity import HarnessQuantity
from wireviz.wv_templates import get_template

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


def generate_pdf_output(
    filename_list: List[Path],
    options: Dict = None,
):
    """Generate a pdf output, options are ignored for now, expect the formatting
    to be done within the html files
    """
    if isinstance(filename_list, Path):
        filename_list = [filename_list]
        output_path = filename_list[0].with_suffix(".pdf")
    else:
        output_dir = filename_list[0].parent
        output_path = (output_dir / output_dir.name).with_suffix(".pdf")

    filepath_list = [f.with_suffix(".html") for f in filename_list]

    print(f"Generating pdf output: {output_path}")
    files_html = [HTML(path) for path in filepath_list]
    documents = [f.render() for f in files_html]
    all_pages = [p for doc in documents for p in doc.pages]
    documents[0].copy(all_pages).write_pdf(output_path)


def generate_shared_bom(
    output_dir,
    shared_bom,
    use_qty_multipliers=False,
    files=None,
    multiplier_file_name=None,
):
    shared_bom_base = output_dir / "shared_bom"
    shared_bom_file = shared_bom_base.with_suffix(".tsv")
    print(f"Generating shared bom at {shared_bom_base}")

    if use_qty_multipliers:
        harnesses = HarnessQuantity(files, multiplier_file_name, output_dir=output_dir)
        harnesses.fetch_qty_multipliers_from_file()
        qty_multipliers = harnesses.multipliers
        print(f"Using quantity multipliers: {qty_multipliers}")
        for bom_item in shared_bom.values():
            bom_item.scale_per_harness(qty_multipliers)

    shared_bomlist = bom_list(shared_bom, restrict_printed_lengths=False, filter_entries=True)

    shared_bom_tsv = bom2tsv(shared_bomlist)
    shared_bom_file.open("w").write(shared_bom_tsv)

    return shared_bom_base, shared_bomlist


def generate_html_output(
    filename: Path,
    bom: List[List[str]],
    metadata: Metadata,
    options: Options,
):
    print("Generating html output")
    template_name = metadata.get("template", {}).get("name", "simple")

    svgdata = None
    if template_name != "titlepage":
        # embed SVG diagram for all but the titlepage
        with filename.with_suffix(".svg").open("r") as f:
            svgdata = re.sub(
                "^<[?]xml [^?>]*[?]>[^<]*<!DOCTYPE [^>]*>",
                "<!-- XML and DOCTYPE declarations from SVG file removed -->",
                f.read(),
                1,
            )

    # generate BOM table
    # generate BOM header (may be at the top or bottom of the table)
    bom_reversed = (
        False if template_name == "simple" or template_name == "titlepage" else True
    )
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
        "show_bom": options.show_bom,
        "show_notes": options.show_notes,
        "show_index_table": options.show_index_table,
        "notes_on_right": options.notes_on_right,
        "notes_width": options.notes_width,
        "diagram": svgdata,
        "sheet_current": sheet_current,
        "sheet_total": sheet_total,
        "bom_reversed": bom_reversed,
        "bom_header": bom_header,
        "bom_content": bom_content,
        "bom_columns": bom_columns,
        "bom_rows": len(bom_content),
        "titleblock_rows": 9,
    }

    # prepare metadata replacements
    added_metadata = {
        "revisions": [],
        "authors": [],
        "sheetsize": "A4",
        "orientation": "portrait",
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
                added_metadata["sheetsize"] = contents.get("sheetsize", "A4")
                if added_metadata["sheetsize"] in ["A2", "A3"]:
                    added_metadata["orientation"] = "landscape"
            else:
                added_metadata[item] = contents

    replacements = {**replacements, **added_metadata}

    # prepare BOM
    replacements["bom"] = get_template("bom.html").render(replacements)

    # prepare titleblock
    replacements["titleblock"] = get_template("titleblock.html").render(replacements)

    # preparate Notes
    if "notes" in replacements:
        replacements["notes"] = get_template("notes.html").render(replacements)

    # prepare index_table
    replacements["index_table"] = get_template("index_table.html").render(replacements)

    # generate page template
    page_rendered = get_template(template_name, ".html").render(replacements)

    # save generated file
    filename.with_suffix(".html").open("w").write(page_rendered)


def generate_titlepage(yaml_data, extra_metadata, shared_bom, for_pdf=False):
    print("Generating titlepage")

    index_table_content = []
    index_table_content.append((1, extra_metadata["titlepage"], ""))

    for index, page_name in enumerate(extra_metadata["output_names"]):
        index_table_content.append((index + 2, page_name, ""))

    if not for_pdf:
        index_table_content = [
            (
                p[0],
                f"<a href={Path(p[1]).with_suffix('.html')}>{p[1]}</a>",
                p[2],
            )
            for p in index_table_content
        ]

    # if create_titlepage:
    #    extra_metadata["index_table_content"].append([
    #        sheet_current,
    #        f"<a href={Path(_output_name).with_suffix('.html')}>{extra_metadata['sheet_name']}</a>",
    #        "",
    #    ])
    # index_table_content.insert(0, [
    #    1,
    #    f"<a href={Path('titlepage').with_suffix('.html')}>Title Page</a>",
    #    ''
    # ])

    titlepage_metadata = {
        **yaml_data.get("metadata", {}),
        **extra_metadata,
        "sheet_current": 1,
        "sheet_name": "titlepage",
        "output_name": "titlepage",
        "index_table_header": ["Sheet", "Harness", "Notes"],
        "index_table_content": index_table_content,
        "bom_updated_position": "top: 20mm; left: 10mm",
        "notes_width": "200mm",
    }
    titlepage_metadata["template"]["name"] = "titlepage"
    titlepage_options = {
        "show_bom": True,
        "show_index_table": True,
        "show_notes": True,
        **yaml_data.get("options", {}),
    }
    generate_html_output(
        extra_metadata["output_dir"] / extra_metadata["titlepage"],
        bom=bom_list(shared_bom, restrict_printed_lengths=False, filter_entries=True),
        metadata=Metadata(**titlepage_metadata),  # TBD what we need to add here
        options=Options(**titlepage_options),
    )
