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
from wireviz.wv_harness_quantity import HarnessQuantity

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
@click.option(
    "-u",
    "--use-qty-multipliers",
    is_flag=True,
    type=bool,
    help="if set, the shared bom counts will be scaled with the qty-multipliers",
)
@click.option(
    "-m",
    "--multiplier-file-name",
    default='quantity_multipliers.txt',
    type=str,
    help="name of file used to fetch the qty_multipliers",
)
def cli(files, formats, prepend, output_dir, output_name, version, use_qty_multipliers, multiplier_file_name):
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

    # TODO: move shared bom generation to a method?
    if "shared_bom" in output_formats:
        shared_bom_file = (_output_dir / "shared_bom").with_suffix(".tsv")
        print(f'Generating shared bom at {shared_bom_file}')
        if use_qty_multipliers:
            harnesses = HarnessQuantity(files, multiplier_file_name, output_dir=_output_dir)
            harnesses.fetch_qty_multipliers_from_file()
            qty_multipliers = harnesses.multipliers
            print(f'Using quantity multipliers: {qty_multipliers}')
            for bom_item in shared_bom.values():
                bom_item.scale_per_harness(qty_multipliers)

        shared_bomlist = bom_list(shared_bom, False)

        shared_bom_tsv = bom2tsv(shared_bomlist)
        shared_bom_file.open("w").write(shared_bom_tsv)

    print()  # blank line after execution


if __name__ == "__main__":
    cli()
