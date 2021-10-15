# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import click

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.wv_helper import open_file_read

format_codes = {
    "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    "P": "pdf",
    "s": "svg",
    "t": "tsv",
}

epilog = "The -f or --format option accepts a string containing one or more of the "
epilog += "following characters to specify which file types to output:\n"
epilog += ", ".join([f"{key} ({value.upper()})" for key, value in format_codes.items()])


@click.command(epilog=epilog, no_args_is_help=True)
@click.argument("file", nargs=-1)
@click.option(
    "-f",
    "--format",
    default="hpst",
    type=str,
    show_default=True,
    help="Output formats (see below).",
)
@click.option(
    "-p",
    "--prepend",
    default=None,
    type=Path,
    help="YAML file to prepend to the input file (optional).",
)
@click.option(
    "-o",
    "--output-file",
    default=None,
    type=Path,
    help="File name (without extension) to use for output, if different from input file name.",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    default=False,
    help=f"Output {APP_NAME} version and exit.",
)
def wireviz(file, format, prepend, output_file, version):
    """
    Parses the provided FILE and generates the specified outputs.
    """
    print()
    print(f"{APP_NAME} {__version__}")
    if version:
        return  # print version number only and exit

    # get list of files
    try:
        _ = iter(file)
    except TypeError:
        filepaths = [file]
    else:
        filepaths = list(file)

    # determine output formats
    output_formats = []
    for code in format:
        if code in format_codes:
            output_formats.append(format_codes[code])
        else:
            raise Exception(f"Unknown output format: {code}")
    output_formats = tuple(sorted(set(output_formats)))
    output_formats_str = (
        f'[{"|".join(output_formats)}]'
        if len(output_formats) > 1
        else output_formats[0]
    )

    image_paths = []
    # check prepend file
    if prepend:
        prepend = Path(prepend)
        if not prepend.exists():
            raise Exception(f"File does not exist:\n{prepend}")
        print("Prepend file:", prepend)

        with open_file_read(prepend) as file_handle:
            prepend_input = file_handle.read() + "\n"
        prepend_dir = prepend.parent
    else:
        prepend_input = ""
        prepend_dir = None

    # run WireVIz on each input file
    for file in filepaths:
        file = Path(file)
        if not file.exists():
            raise Exception(f"File does not exist:\n{file}")

        file_out = file.with_suffix("") if not output_file else output_file

        print("Input file:  ", file)
        print("Output file: ", f"{file_out}.{output_formats_str}")

        with open_file_read(file) as file_handle:
            yaml_input = file_handle.read()
        file_dir = file.parent

        yaml_input = prepend_input + yaml_input

        wv.parse_text(
            yaml_input,
            file_out=file_out,
            output_formats=output_formats,
            image_paths=[file_dir, prepend_dir],
        )

    print()


if __name__ == "__main__":
    wireviz()
