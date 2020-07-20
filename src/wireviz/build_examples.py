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

readme = 'readme.md'


def build(dirname, build_readme, include_source, include_readme):
    filename_list = []
    path   = paths[dirname]['path']
    prefix = paths[dirname]['prefix']
    print(f'Building {path}')
    # collect input YAML files
    file_iterator = path.iterdir()
    for entry in file_iterator:
        if entry.is_file() and entry.match(f'{prefix}*.yml'):
            filename_list.append(entry)
    filename_list = sorted(filename_list)
    # build files
    if build_readme:
        with open_file_write(path / 'readme.md') as out:
            out.write(f'# {paths[dirname]["title"]}\n\n')
    for yaml_file in filename_list:
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
    generated_extensions = ['.gv', '.png', '.svg', '.html', '.bom.tsv']
    for k, v in paths.items():
        filepath = v['path']
        print(f'Cleaning {filepath}')
        # collect files to remove
        filename_list = []
        file_iterator = filepath.iterdir()
        for entry in file_iterator:
            for ext in generated_extensions:
                if entry.is_file() and entry.match(f'*{ext}'):
                    filename_list.append(entry)
        filename_list.append(filepath / readme)

        filename_list = sorted(filename_list)
        # remove files
        for filename in filename_list:
            if filename.is_file():
                print(f'  rm {filename}')
                os.remove(filename)


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


if __name__ == '__main__':
    main()
