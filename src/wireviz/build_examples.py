#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from pathlib import Path

script_path = Path(__file__).absolute()

sys.path.insert(0, str(script_path.parent.parent))  # to find wireviz module
from wireviz import wireviz
from wv_helper import open_file_write, open_file_read, open_file_append


paths = {}
paths['examples'] = {'path': Path(script_path).parent.parent.parent / 'examples',
                     'prefix': 'ex',
                     'title': 'Example Gallery'}
paths['tutorial'] = {'path': Path(script_path).parent.parent.parent / 'tutorial',
                     'prefix': 'tutorial',
                     'title': 'WireViz Tutorial'}
paths['demos']    = {'path': Path(script_path).parent.parent.parent / 'examples',
                     'prefix': 'demo'}

input_extensions = ['.yml']
generated_extensions = ['.gv', '.png', '.svg', '.html', '.bom.tsv']
extensions_not_from_graphviz = [ext for ext in generated_extensions if ext[-1] == 'v']
readme = 'readme.md'


def collect_filenames(description, pathkey, ext_list, extrafile = None):
    path = paths[pathkey]['path']
    patterns = [f"{paths[pathkey]['prefix']}*{ext}" for ext in ext_list]
    if extrafile is not None:
        patterns.append(extrafile)
    print(f"{description} {path}")
    return sorted([filename for pattern in patterns for filename in path.glob(pattern)])


def build(dirname, build_readme, include_source, include_readme):
    # build files
    path = paths[dirname]['path']
    if build_readme:
        with open_file_write(path / 'readme.md') as out:
            out.write(f'# {paths[dirname]["title"]}\n\n')
    # collect and iterate input YAML files
    for yaml_file in collect_filenames('Building', dirname, input_extensions):
        print(f'  {yaml_file}')
        wireviz.parse_file(yaml_file)

        if build_readme:
            i = ''.join(filter(str.isdigit, yaml_file.stem))

            if include_readme:
                with open_file_append(path / readme) as out:
                    with open_file_read(path / f'{yaml_file.stem}.md') as info:
                        for line in info:
                            out.write(line.replace('## ', '## {} - '.format(i)))
                        out.write('\n\n')
            else:
                with open_file_append(path / readme) as out:
                    out.write(f'## Example {i}\n')

            with open_file_append(path / readme) as out:
                if include_source:
                    with open_file_read(yaml_file) as src:
                        out.write('```yaml\n')
                        for line in src:
                            out.write(line)
                        out.write('```\n')
                    out.write('\n')

                out.write(f'![]({yaml_file.stem}.png)\n\n')
                out.write(f'[Source]({yaml_file.name}) - [Bill of Materials]({yaml_file.stem}.bom.tsv)\n\n\n')


def clean_examples():
    for key in paths.keys():
        # collect and remove files
        for filename in collect_filenames('Cleaning', key, generated_extensions, readme):
            if filename.is_file():
                print(f'  rm {filename}')
                os.remove(filename)


def compare_generated(include_from_graphviz = False):
    compare_extensions = generated_extensions if include_from_graphviz else extensions_not_from_graphviz
    for key in paths.keys():
        # collect and compare files
        for filename in collect_filenames('Comparing', key, compare_extensions, readme):
            cmd = f'git --no-pager diff {filename}'
            print(f'  {cmd}')
            os.system(cmd)


def restore_generated():
    for key, value in paths.items():
        # collect input YAML files
        filename_list = collect_filenames('Restoring', key, input_extensions)
        # collect files to restore
        filename_list = [fn.with_suffix(ext) for fn in filename_list for ext in generated_extensions]
        filename_list.append(value['path'] / readme)
        # restore files
        for filename in filename_list:
            cmd = f'git checkout -- {filename}'
            print(f'  {cmd}')
            os.system(cmd)


def parse_args():
    parser = argparse.ArgumentParser(description='Wireviz Example Manager',)
    parser.add_argument('action', nargs='?', action='store', default='build')
    parser.add_argument('-generate', nargs='*', choices=['examples', 'demos', 'tutorial'], default=['examples', 'demos', 'tutorial'])
    return parser.parse_args()


def main():
    args = parse_args()
    if args.action == 'build':
        for gentype in args.generate:
            if gentype == 'demos':
                build('demos', build_readme = False, include_source = False, include_readme = False)
            if gentype == 'examples':
                build('examples', build_readme = True, include_source = False, include_readme = False)
            if gentype == 'tutorial':
                build('tutorial', build_readme = True, include_source = True, include_readme = True)
    elif args.action == 'clean':
        clean_examples()
    elif args.action == 'compare':
        compare_generated()
    elif args.action == 'restore':
        restore_generated()


if __name__ == '__main__':
    main()
