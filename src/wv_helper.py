from typing import Any, List

def awg_equiv(mm2):
    awg_equiv_table = {
                        '0.09': 28,
                        '0.14': 26,
                        '0.25': 24,
                        '0.34': 22,
                        '0.5': 21,
                        '0.75': 20,
                        '1': 18,
                        '1.5': 16,
                        '2.5': 14,
                        '4': 12,
                        '6': 10,
                        '10': 8,
                        '16': 6,
                        '25': 4,
                        '35': 2,
                        '50': 1,
                        }
    k = str(mm2)
    if k in awg_equiv_table:
        return awg_equiv_table[k]
    else:
        return 'unknown'

def nested(input):
    l = []
    for x in input:
        if isinstance(x, list):
            if len(x) > 0:
                n = nested(x)
                if n != '':
                    l.append('{' + n + '}')
        else:
            if x is not None:
                if x != '':
                    l.append(str(x))
    s = '|'.join(l)
    return s

def int2tuple(input):
    if isinstance(input, tuple):
        output = input
    else:
        output = (input,)
    return output

def flatten2d(input):
    output = [[str(item) if not isinstance(item, List) else ', '.join(item) for item in row] for row in input]
    return output

def tuplelist2tsv(input, header=None):
    output = ''
    if header is not None:
        input.insert(0, header)
    input = flatten2d(input)
    for row in input:
        output = output + '\t'.join(str(item) for item in row) + '\n'
    return output
