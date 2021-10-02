import os
import sys

import click

import wireviz.wireviz

@click.command()
@click.argument('filepath', nargs=-1)
@click.option('-p', '--prepend', default=None)
@click.option('-o', '--output', default='hpst')
@click.option('-V', '--version', is_flag=True, default=False)
def main(filepath, prepend, output, version):
    print('WireViz!')
    # get list of files
    try:
        _ = iter(filepath)
    except TypeError:
        filepaths = [filepath]
    else:
        filepaths = list(filepath)

    for f in filepaths:
        print(f)
    print()

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    wireviz()
