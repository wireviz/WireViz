#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path

script_path = Path(__file__).absolute()
sys.path.insert(0, str(script_path.parent.parent.parent))  # to find wireviz module

from wireviz import APP_NAME, __version__, wireviz
from wireviz.wv_utils import open_file_append, open_file_read, open_file_write

dir = script_path.parent.parent.parent.parent
readme = "readme.md"
groups = {
    "examples": {
        "path": dir / "examples",
        "prefix": "ex",
        readme: [],  # Include no files
        "title": "Example Gallery",
    },
    "tutorial": {
        "path": dir / "tutorial",
        "prefix": "tutorial",
        readme: ["md", "yml"],  # Include .md and .yml files
        "title": f"{APP_NAME} Tutorial",
    },
    "demos": {
        "path": dir / "examples",
        "prefix": "demo",
    },
}

input_extensions = [".yml"]
extensions_not_containing_graphviz_output = [".gv", ".bom.tsv"]
extensions_containing_graphviz_output = [".png", ".svg", ".html"]
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
            with open_file_write(path / readme) as out:
                out.write(f'# {groups[key]["title"]}\n\n')
        # collect and iterate input YAML files
        for yaml_file in collect_filenames("Building", key, input_extensions):
            print(f'  "{yaml_file}"')
            wireviz.parse(yaml_file, output_formats=("gv", "html", "png", "svg", "tsv"))

            if build_readme:
                i = "".join(filter(str.isdigit, yaml_file.stem))

                with open_file_append(path / readme) as out:
                    if include_readme:
                        with open_file_read(yaml_file.with_suffix(".md")) as info:
                            for line in info:
                                out.write(line.replace("## ", f"## {i} - "))
                            out.write("\n\n")
                    else:
                        out.write(f"## Example {i}\n")

                    if include_source:
                        with open_file_read(yaml_file) as src:
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


def compare_generated(groupkeys, branch="", include_graphviz_output=False):
    if branch:
        branch = f" {branch.strip()}"
    compare_extensions = (
        generated_extensions
        if include_graphviz_output
        else extensions_not_containing_graphviz_output
    )
    for key in groupkeys:
        # collect and compare files
        for filename in collect_filenames("Comparing", key, compare_extensions):
            cmd = f'git --no-pager diff{branch} -- "{filename}"'
            print(f"  {cmd}")
            os.system(cmd)


def restore_generated(groupkeys, branch=""):
    if branch:
        branch = f" {branch.strip()}"
    for key in groupkeys:
        # collect input YAML files
        filename_list = collect_filenames("Restoring", key, input_extensions)
        # collect files to restore
        filename_list = [
            fn.with_suffix(ext) for fn in filename_list for ext in generated_extensions
        ]
        if readme in groups[key]:
            filename_list.append(groups[key]["path"] / readme)
        # restore files
        for filename in filename_list:
            cmd = f'git checkout{branch} -- "{filename}"'
            print(f"  {cmd}")
            os.system(cmd)


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
        "-c",
        "--compare-graphviz-output",
        action="store_true",
        help="the Graphviz output is also compared (default: False)",
    )
    parser.add_argument(
        "-b",
        "--branch",
        action="store",
        default="",
        help="branch or commit to compare with or restore from",
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
    elif args.action == "compare" or args.action == "diff":
        compare_generated(args.groups, args.branch, args.compare_graphviz_output)
    elif args.action == "restore":
        restore_generated(args.groups, args.branch)


if __name__ == "__main__":
    main()
