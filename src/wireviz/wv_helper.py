#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

awg_equiv_table = {
    '0.09': '28',
    '0.14': '26',
    '0.25': '24',
    '0.34': '22',
    '0.5': '21',
    '0.75': '20',
    '1': '18',
    '1.5': '16',
    '2.5': '14',
    '4': '12',
    '6': '10',
    '10': '8',
    '16': '6',
    '25': '4',
    '35': '2',
    '50': '1',
}

mm2_equiv_table = {v:k for k,v in awg_equiv_table.items()}

def awg_equiv(mm2):
    return awg_equiv_table.get(str(mm2), 'Unknown')

def mm2_equiv(awg):
    return mm2_equiv_table.get(str(awg), 'Unknown')

def nested(inp):
    l = []
    for x in inp:
        if isinstance(x, list):
            if len(x) > 0:
                n = nested(x)
                if n != '':
                    l.append('{' + n + '}')
        else:
            if x is not None:
                if x != '':
                    l.append(str(x))
    return '|'.join(l)


def int2tuple(inp):
    if isinstance(inp, tuple):
        output = inp
    else:
        output = (inp,)
    return output


def flatten2d(inp):
    return [[str(item) if not isinstance(item, List) else ', '.join(item) for item in row] for row in inp]


def tuplelist2tsv(inp, header=None):
    output = ''
    if header is not None:
        inp.insert(0, header)
    inp = flatten2d(inp)
    for row in inp:
        output = output + '\t'.join(str(item) for item in row) + '\n'
    return output
