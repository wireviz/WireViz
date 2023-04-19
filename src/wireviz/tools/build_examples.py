#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path

import click

script_path = Path(__file__).absolute()
sys.path.insert(0, str(script_path.parent.parent.parent))  # to find wireviz module

from wireviz import APP_NAME, __version__
from wireviz.wv_cli import cli

base_dir = script_path.parent.parent.parent.parent
readme = "readme.md"
groups = {
    "examples": {
        "path": base_dir / "examples",
        "prefix": "ex",
        readme: [],  # Include no files
        "title": "Example Gallery",
    },
    "tutorial": {
        "path": base_dir / "tutorial",
        "prefix": "tutorial",
        readme: ["md", "yml"],  # Include .md and .yml files
        "title": f"{APP_NAME} Tutorial",
    },
    "demos": {
        "path": base_dir / "examples",
        "prefix": "demo",
    },
}

input_extensions = [".yml"]
extensions_not_containing_graphviz_output = [".gv", ".bom.tsv"]
extensions_containing_graphviz_output = [".png", ".svg", ".html", ".pdf"]
generated_extensions = (
    extensions_not_containing_graphviz_output + extensions_containing_graphviz_output
)


def collect_filenames(description, groupkey, ext_list):
    path = groups[groupkey]["path"]
    patterns = [f"{groups[groupkey]['prefix']}*{ext}" for ext in ext_list]
    if ext_list != input_extensions and readme in groups[groupkey]:
        patterns.append(readme)
    print(f'{description} {groupkey} in "{path}"')
    return sorted([filename for pattern in patterns for filename in path.glob(pattern)])


def build_generated(groupkeys):
    for key in groupkeys:
        # preparation
        path = groups[key]["path"]
        build_readme = readme in groups[key]
        if build_readme:
            include_readme = "md" in groups[key][readme]
            include_source = "yml" in groups[key][readme]
            with (path / readme).open("w") as out:
                out.write(f'# {groups[key]["title"]}\n\n')
        # collect and iterate input YAML files
        yaml_files = [f for f in collect_filenames("Building", key, input_extensions)]
        try:
            res = cli([
                "--formats", "ghpstb",  # no pdf for now
                "--prepend", yaml_files[0].parent / "metadata.yml",
                *[str(f) for f in yaml_files],
            ])
        except BaseException as e:
            if str(e) != "0" and not isinstance(
                e, (click.ClickException, SystemExit)
            ):
                raise

        if build_readme:
            for yaml_file in yaml_files:
                i = "".join(filter(str.isdigit, yaml_file.stem))

                with (path / readme).open("a") as out:
                    if include_readme:
                        with yaml_file.with_suffix(".md").open("r") as info:
                            for line in info:
                                out.write(line.replace("## ", f"## {i} - "))
                            out.write("\n\n")
                    else:
                        out.write(f"## Example {i}\n")

                    if include_source:
                        with yaml_file.open("r") as src:
                            out.write("```yaml\n")
                            for line in src:
                                out.write(line)
                            out.write("```\n")
                        out.write("\n")

                    out.write(f"![]({yaml_file.stem}.png)\n\n")
                    out.write(
                        f"[Source]({yaml_file.name}) - [Bill of Materials]({yaml_file.stem}.bom.tsv)\n\n\n"
                    )


def clean_generated(groupkeys):
    for key in groupkeys:
        # collect and remove files
        for filename in collect_filenames("Cleaning", key, generated_extensions):
            if filename.is_file():
                print(f'  rm "{filename}"')
                filename.unlink()

def parse_args():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} Example Manager",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s - {APP_NAME} {__version__}",
    )
    parser.add_argument(
        "action",
        nargs="?",
        action="store",
        choices=["build", "clean", "compare", "diff", "restore"],
        default="build",
        help="what to do with the generated files (default: build)",
    )
    parser.add_argument(
        "-g",
        "--groups",
        nargs="+",
        choices=groups.keys(),
        default=groups.keys(),
        help="the groups of generated files (default: all)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.action == "build":
        build_generated(args.groups)
    elif args.action == "clean":
        clean_generated(args.groups)


if __name__ == "__main__":
    main()
