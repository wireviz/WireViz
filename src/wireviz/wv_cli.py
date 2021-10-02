import os
from pathlib import Path
import sys

import click

from wireviz import APP_NAME, __version__
import wireviz.wireviz as wv
from wireviz.wv_helper import open_file_read


@click.command()
@click.argument('filepath', nargs=-1)
@click.option('-f', '--format', default='hpst')
@click.option('-p', '--prepend', default=None)
@click.option('-o', '--output-file', default=None)
@click.option('-V', '--version', is_flag=True, default=False)
def main(filepath, format, prepend, output_file, version):
    print()
    print(f'{APP_NAME} {__version__}')
    if version:
        return  # print version number only and exit

    # get list of files
    try:
        _ = iter(filepath)
    except TypeError:
        filepaths = [filepath]
    else:
        filepaths = list(filepath)

    # determine output formats
    format_codes = {'p': 'png', 's': 'svg', 't': 'tsv', 'c': 'csv', 'h': 'html', 'P': 'pdf'}
    return_types = []
    for code in format:
        if code in format_codes:
            return_types.append(format_codes[code])
        else:
            raise Exception(f'Unknown output format: {code}')
    return_types = tuple(sorted(set(return_types)))
    return_types_str = f'[{"|".join(return_types)}]' if len(return_types) > 1 else return_types[0]

    # check prepend file
    if prepend:
        prepend = Path(prepend)
        if not prepend.exists():
            raise Exception(f'File does not exist:\n{prepend}')
        print('Prepend file:', prepend)

        with open_file_read(prepend) as file_handle:
            prepend_input = file_handle.read() + '\n'
    else:
        prepend_input = ''

    # run WireVIz on each input file
    for file in filepaths:
        file = Path(file)
        if not file.exists():
            raise Exception(f'File does not exist:\n{file}')

        file_out = file.with_suffix('') if not output_file else output_file

        print('Input file:  ', file)
        print('Output file: ', f'{file_out}.{return_types_str}')

        with open_file_read(file) as file_handle:
            yaml_input = file_handle.read()

        yaml_input = prepend_input + yaml_input

        wv.parse(yaml_input, file_out=file_out)

    print()

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    wireviz()
