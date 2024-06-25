# -*- coding: utf-8 -*-

import re
from pathlib import Path
from typing import Dict, List

awg_equiv_table = {
    "0.09": "28",
    "0.14": "26",
    "0.25": "24",
    "0.34": "22",
    "0.5": "21",
    "0.75": "20",
    "1": "18",
    "1.5": "16",
    "2.5": "14",
    "4": "12",
    "6": "10",
    "10": "8",
    "16": "6",
    "25": "4",
    "35": "2",
    "50": "1",
}

mm2_equiv_table = {v: k for k, v in awg_equiv_table.items()}


def awg_equiv(mm2):
    return awg_equiv_table.get(str(mm2), "Unknown")


def mm2_equiv(awg):
    return mm2_equiv_table.get(str(awg), "Unknown")


def expand(yaml_data):
    # yaml_data can be:
    # - a singleton (normally str or int)
    # - a list of str or int
    # if str is of the format '#-#', it is treated as a range (inclusive) and expanded
    output = []
    if not isinstance(yaml_data, list):
        yaml_data = [yaml_data]
    for e in yaml_data:
        e = str(e)
        if "-" in e:
            a, b = e.split("-", 1)
            try:
                a = int(a)
                b = int(b)
                if a < b:
                    for x in range(a, b + 1):
                        output.append(x)  # ascending range
                elif a > b:
                    for x in range(a, b - 1, -1):
                        output.append(x)  # descending range
                else:  # a == b
                    output.append(a)  # range of length 1
            except:
                # '-' was not a delimiter between two ints, pass e through unchanged
                output.append(e)
        else:
            try:
                x = int(e)  # single int
            except Exception:
                x = e  # string
            output.append(x)
    return output


def get_single_key_and_value(d: dict):
    k = list(d.keys())[0]
    v = d[k]
    return (k, v)


def int2tuple(inp):
    if isinstance(inp, tuple):
        output = inp
    else:
        output = (inp,)
    return output


def flatten2d(inp):
    return [
        [str(item) if not isinstance(item, List) else ", ".join(item) for item in row]
        for row in inp
    ]


def tuplelist2tsv(inp, header=None):
    output = ""
    if header is not None:
        inp.insert(0, header)
    inp = flatten2d(inp)
    for row in inp:
        output = output + "\t".join(str(remove_links(item)) for item in row) + "\n"
    return output


def remove_links(inp):
    return (
        re.sub(r"<[aA] [^>]*>([^<]*)</[aA]>", r"\1", inp)
        if isinstance(inp, str)
        else inp
    )


def clean_whitespace(inp):
    return " ".join(inp.split()).replace(" ,", ",") if isinstance(inp, str) else inp


def open_file_read(filename):
    """Open utf-8 encoded text file for reading - remember closing it when finished"""
    # TODO: Intelligently determine encoding
    return open(filename, "r", encoding="UTF-8")


def open_file_write(filename):
    """Open utf-8 encoded text file for writing - remember closing it when finished"""
    return open(filename, "w", encoding="UTF-8")


def open_file_append(filename):
    """Open utf-8 encoded text file for appending - remember closing it when finished"""
    return open(filename, "a", encoding="UTF-8")


def file_read_text(filename: str) -> str:
    """Read utf-8 encoded text file, close it, and return the text"""
    return Path(filename).read_text(encoding="utf-8")


def file_write_text(filename: str, text: str) -> int:
    """Write utf-8 encoded text file, close it, and return the number of characters written"""
    return Path(filename).write_text(text, encoding="utf-8")


def is_arrow(inp):
    """
    Matches strings of one or multiple `-` or `=` (but not mixed)
    optionally starting with `<` and/or ending with `>`.

    Examples:
      <-, --, ->, <->
      <==, ==, ==>, <=>
    """
    # regex by @shiraneyo
    return bool(
        re.match(r"^\s*(?P<leftHead><?)(?P<body>-+|=+)(?P<rightHead>>?)\s*$", inp)
    )


def aspect_ratio(image_src):
    try:
        from PIL import Image

        with Image.open(image_src) as image:
            if image.width > 0 and image.height > 0:
                return image.width / image.height
            print(f"aspect_ratio(): Invalid image size {image.width} x {image.height}")
    # ModuleNotFoundError and FileNotFoundError are the most expected, but all are handled equally.
    except Exception as error:
        print(f"aspect_ratio(): {type(error).__name__}: {error}")
    return 1  # Assume 1:1 when unable to read actual image size


def smart_file_resolve(filename: str, possible_paths: (str, List[str])) -> Path:
    if not isinstance(possible_paths, List):
        possible_paths = [possible_paths]
    filename = Path(filename)
    if filename.is_absolute():
        if filename.exists():
            return filename
        else:
            raise Exception(f"{filename} does not exist.")
    else:  # search all possible paths in decreasing order of precedence
        possible_paths = [
            Path(path).resolve() for path in possible_paths if path is not None
        ]
        for possible_path in possible_paths:
            resolved_path = (possible_path / filename).resolve()
            if resolved_path.exists():
                return resolved_path
        else:
            raise Exception(
                f"{filename} was not found in any of the following locations: \n"
                + "\n".join([str(x) for x in possible_paths])
            )
