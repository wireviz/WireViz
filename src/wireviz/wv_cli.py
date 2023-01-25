# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import click

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.wv_bom import bom_list
from wireviz.wv_utils import bom2tsv

format_codes = {
    "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    "P": "pdf",
    "s": "svg",
    "t": "tsv",
    "b": "shared_bom",
}

epilog = (
    "The -f or --formats option accepts a string containing one or more of the "
    "following characters to specify which file types to output:\n"
    + f", ".join([f"{key} ({value.upper()})" for key, value in format_codes.items()])
)


@click.command(epilog=epilog, no_args_is_help=True)
@click.argument(
    "files",
    type=click.Path(
        exists=True,
        readable=True,
        dir_okay=False,
        path_type=Path,
    ),
    nargs=-1,
    required=True,
)
@click.option(
    "-f",
    "--formats",
    default="hpst",
    type=str,
    show_default=True,
    help="Output formats (see below).",
)
@click.option(
    "-p",
    "--prepend",
    default=[],
    multiple=True,
    type=click.Path(
        exists=True,
        readable=True,
        file_okay=True,
        path_type=Path,
    ),
    help="YAML file to prepend to the input file (optional).",
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(
        exists=True,
        readable=True,
        file_okay=False,
        dir_okay=True,
        path_type=Path,
    ),
    help="Directory to use for output files, if different from input file directory.",
)
@click.option(
    "-O",
    "--output-name",
    default=None,
    type=str,
    help=(
        "File name (without extension) to use for output files, "
        "if different from input file name."
    ),
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    default=False,
    help=f"Output {APP_NAME} version and exit.",
)
def cli(files, formats, prepend, output_dir, output_name, version):
    """
    Parses the provided FILE and generates the specified outputs.
    """
    if version:
        print(f"{APP_NAME} {__version__}")
        return  # print version number only and exit

    _output_dir = files[0].parent if not output_dir else output_dir

    # determine output formats
    output_formats = {format_codes[f] for f in formats if f in format_codes}

    harness = None
    shared_bom = {}
    sheet_current = 1
    # run WireVIz on each input file
    for _file in files:
        _output_name = _file.stem if not output_name else output_name

        print("Input file:  ", _file)
        print(
            "Output file: ",
            f"{_output_dir / _output_name}.[{'|'.join(output_formats)}]",
        )

        extra_metadata = {}
        extra_metadata["sheet_name"] = _output_name.upper()
        extra_metadata["sheet_total"] = len(files)
        extra_metadata["sheet_current"] = sheet_current
        sheet_current += 1

        file_dir = _file.parent

        ret = wv.parse(
            prepend + (_file,),
            return_types=("shared_bom"),
            output_formats=output_formats,
            output_dir=_output_dir,
            output_name=_output_name,
            extra_metadata=extra_metadata,
            shared_bom=shared_bom,
        )
        shared_bom = ret["shared_bom"]

    if "shared_bom" in output_formats:
        shared_bomlist = bom_list(shared_bom)
        shared_bom_tsv = bom2tsv(shared_bomlist)
        (_output_dir / "shared_bom").with_suffix(".tsv").open("w").write(shared_bom_tsv)

    print()  # blank line after execution


if __name__ == "__main__":
    cli()
