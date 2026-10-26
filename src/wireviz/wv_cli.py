# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

import click

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import wireviz.wireviz as wv
from wireviz import APP_NAME, __version__
from wireviz.wv_helper import file_read_text

format_codes = {
    # "c": "csv",
    "g": "gv",
    "h": "html",
    "p": "png",
    # "P": "pdf",
    "s": "svg",
    "t": "tsv",
}

# output formats that can be written to stdout
stdout_formats = ("png", "svg")

epilog = "The -f or --format option accepts a string containing one or more of the "
epilog += "following characters to specify which file types to output:\n"
epilog += ", ".join([f"{key} ({value.upper()})" for key, value in format_codes.items()])


@click.command(
    epilog=epilog,
    no_args_is_help=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
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
    help="File name (without extension) to use for output files, if different from input file name.",
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

    Use - as FILE to read from stdin, and -o - to write to stdout.
    When reading from stdin, output is written to stdout unless -o is specified.
    """
    if version:
        print(f"{APP_NAME} {__version__}")
        return  # print version number only and exit
    print(file=sys.stderr)
    print(f"{APP_NAME} {__version__}", file=sys.stderr)

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
            print("Prepend file:", prepend_file, file=sys.stderr)

            prepend_input += file_read_text(prepend_file) + "\n"
    else:
        prepend_input = ""

    # run WireVIz on each input file
    for file in filepaths:
        if file == "-":
            # read from stdin
            yaml_input = sys.stdin.read()
            image_paths = {Path.cwd()}
            write_stdout = output_dir is None or str(output_dir) == "-"
        else:
            file = Path(file)
            if not file.exists():
                raise Exception(f"File does not exist:\n{file}")
            yaml_input = file_read_text(file)
            image_paths = {file.parent}
            write_stdout = output_dir is not None and str(output_dir) == "-"

        print("Input file:  ", file, file=sys.stderr)

        yaml_input = prepend_input + yaml_input
        for p in prepend:
            image_paths.add(Path(p).parent)

        if write_stdout:
            if len(output_formats) > 1 or output_formats[0] not in stdout_formats:
                raise Exception(
                    f"Only one of the following output formats can be written to stdout: {', '.join(stdout_formats)}"
                )
            print("Output file:  <stdout>", file=sys.stderr)
            output = wv.parse(
                yaml_input,
                return_types=output_formats[0],
                image_paths=list(image_paths),
            )
            if isinstance(output, (bytes, bytearray)):
                sys.stdout.buffer.write(output)
            else:
                sys.stdout.write(output)
            sys.stdout.flush()
            continue

        if file == "-":
            if not output_name:
                raise Exception("Output name (-O) is required to write files when reading from stdin")
            _output_dir = output_dir
            _output_name = output_name
        else:
            # file_out = file.with_suffix("") if not output_file else output_file
            _output_dir = file.parent if not output_dir else output_dir
            _output_name = file.stem if not output_name else output_name

        print(
            "Output file: ",
            f"{Path(_output_dir / _output_name)}.{output_formats_str}",
            file=sys.stderr,
        )

        wv.parse(
            yaml_input,
            output_formats=output_formats,
            output_dir=_output_dir,
            output_name=_output_name,
            image_paths=list(image_paths),
        )

    print(file=sys.stderr)


if __name__ == "__main__":
    wireviz()
