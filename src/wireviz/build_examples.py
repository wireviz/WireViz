#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
import sys
from fnmatch import fnmatch

# noinspection PyUnresolvedReferences
from wv_helper import open_file_write, open_file_read

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from wireviz import wireviz

examples_path = os.path.join('..','..','examples')
tutorials_path = os.path.join('..','..','tutorial')
demos_path = examples_path

readme = 'readme.md'


def build_demos():
    for fn in sorted(os.listdir(demos_path)):
        if fnmatch(fn, "demo*.yml"):
            abspath = os.path.join(demos_path, fn)

            print(abspath)
            wireviz.parse_file(abspath)

def build_examples():
    with open_file_write(os.path.join(examples_path, readme)) as file:
        file.write('# Example gallery\n')
        for fn in sorted(os.listdir(examples_path)):
            if fnmatch(fn, "ex*.yml"):
                i = ''.join(filter(str.isdigit, fn))

                abspath = os.path.join(examples_path, fn)
                outfile_name = abspath.split(".yml")[0]


                print(abspath)
                wireviz.parse_file(abspath)

                file.write(f'## Example {i}\n')
                file.write(f'![]({outfile_name}.png)\n\n')
                file.write(f'[Source]({fn}) - [Bill of Materials]({outfile_name}.bom.tsv)\n\n\n')

def build_tutorials():
    with open_file_write(os.path.join(tutorials_path, readme)) as file:
        file.write('# WireViz Tutorial\n')
        for fn in sorted(os.listdir(tutorials_path)):
            if fnmatch(fn, "tutorial*.yml"):
                i = ''.join(filter(str.isdigit, fn))
                abspath = os.path.join(tutorials_path, fn)
                print(abspath)

                wireviz.parse_file(abspath)

                outfile_name = abspath.split(".yml")[0]

                with open_file_read(outfile_name + '.md') as info:
                    for line in info:
                        file.write(line.replace('## ', '## {} - '.format(i)))
                file.write(f'\n[Source]({fn}):\n\n')

                with open_file_read(abspath) as src:
                    file.write('```yaml\n')
                    for line in src:
                        file.write(line)
                    file.write('```\n')
                file.write('\n')

                file.write('\nOutput:\n\n'.format(i))

                file.write(f'![](tutorial{outfile_name}.png)\n\n')

                file.write(f'[Bill of Materials](tutorial{outfile_name}.bom.tsv)\n\n\n')

def clean_examples():
    generated_extensions = ['.gv', '.png', '.svg', '.html', '.bom.tsv']

    for filepath in [examples_path, demos_path, tutorials_path]:
        print(filepath)
        for file in sorted(os.listdir(filepath)):
            if os.path.exists(os.path.join(filepath, file)):
                if list(filter(file.endswith, generated_extensions)) or file == 'readme.md':
                    print('rm ' + os.path.join(filepath, file))
                    os.remove(os.path.join(filepath, file))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Wireviz Example Manager',
    )
    parser.add_argument('action', nargs='?', action='store', default='build')
    parser.add_argument('-generate', nargs='*', choices=['examples', 'demos', 'tutorials'], default=['examples', 'demos', 'tutorials'])
    return parser.parse_args()
def main():
    args = parse_args()
    if args.action == 'build':
        generate_types = {
            'examples': build_examples,
            'demos': build_demos,
            'tutorials': build_tutorials
        }
        for gentype in args.generate:
            if gentype in generate_types:
                generate_types.get(gentype) ()
    elif args.action == 'clean':
        clean_examples()

if __name__ == '__main__':
    main()
