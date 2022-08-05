# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import click

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.wv_utils import open_file_read

format_codes = {
    "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    "P": "pdf",
    "s": "svg",
    "t": "tsv",
}


epilog = (
    "The -f or --format option accepts a string containing one or more of the "
    "following characters to specify which file types to output:\n"
    + f", ".join([f"{key} ({value.upper()})" for key, value in format_codes.items()])
)


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
    default=[],
    multiple=True,
    type=Path,
    help="YAML file to prepend to the input file (optional).",
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=Path,
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
def wireviz(file, format, prepend, output_dir, output_name, version):
    """
    Parses the provided FILE and generates the specified outputs.
    """
    print()  # blank line before execution
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

    # check prepend file
    if len(prepend) > 0:
        prepend_input = ""
        for prepend_file in prepend:
            prepend_file = Path(prepend_file)
            if not prepend_file.exists():
                raise Exception(f"File does not exist:\n{prepend_file}")
            if not prepend_file.is_file():
                raise Exception(f"Path is not a file:\n{prepend_file}")
            print("Prepend file:", prepend_file)

            prepend_input += open_file_read(prepend_file).read() + "\n"
    else:
        prepend_input = ""

    # run WireVIz on each input file
    for file in filepaths:
        file = Path(file)
        if not file.exists():
            raise Exception(f"File does not exist:\n{file}")
        if not file.is_file():
            raise Exception(f"Path is not a file:\n{file}")

        # file_out = file.with_suffix("") if not output_file else output_file
        _output_dir = file.parent if not output_dir else output_dir
        _output_name = file.stem if not output_name else output_name

        print("Input file:  ", file)
        print(
            "Output file: ", f"{Path(_output_dir / _output_name)}.{output_formats_str}"
        )

        yaml_input = open_file_read(file).read()
        file_dir = file.parent

        yaml_input = prepend_input + yaml_input
        image_paths = {file_dir}
        for p in prepend:
            image_paths.add(Path(p).parent)

        wv.parse(
            yaml_input,
            output_formats=output_formats,
            output_dir=_output_dir,
            output_name=_output_name,
            image_paths=list(image_paths),
        )

    print()  # blank line after execution


if __name__ == "__main__":
    wireviz()
