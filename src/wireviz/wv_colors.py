#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

COLOR_CODES = {
    'DIN': ['WH', 'BN', 'GN', 'YE', 'GY', 'PK', 'BU', 'RD', 'BK', 'VT', 'GYPK', 'RDBU', 'WHGN', 'BNGN', 'WHYE', 'YEBN',
            'WHGY', 'GYBN', 'WHPK', 'PKBN', 'WHBU', 'BNBU', 'WHRD', 'BNRD', 'WHBK', 'BNBK', 'GYGN', 'YEGY', 'PKGN',
            'YEPK', 'GNBU', 'YEBU', 'GNRD', 'YERD', 'GNBK', 'YEBK', 'GYBU', 'PKBU', 'GYRD', 'PKRD', 'GYBK', 'PKBK',
            'BUBK', 'RDBK', 'WHBNBK', 'YEGNBK', 'GYPKBK', 'RDBUBK', 'WHGNBK', 'BNGNBK', 'WHYEBK', 'YEBNBK', 'WHGYBK',
            'GYBNBK', 'WHPKBK', 'PKBNBK', 'WHBUBK', 'BNBUBK', 'WHRDBK', 'BNRDBK'],
    'IEC': ['BN', 'RD', 'OG', 'YE', 'GN', 'BU', 'VT', 'GY', 'WH', 'BK'],
    'BW': ['BK', 'WH'],
    'TEL': ['BUWH', 'WHBU', 'OGWH', 'WHOG', 'GNWH', 'WHGN', 'BNWH', 'WHBN', 'SLWH', 'WHSL', 'BURD', 'RDBU', 'OGRD',
            'RDOG', 'GNRD', 'RDGN', 'BNRD', 'RDBN', 'SLRD', 'RDSL', 'BUBK', 'BKBU', 'OGBK', 'BKOG', 'GNBK', 'BKGN',
            'BNBK', 'BKBN', 'SLBK', 'BKSL', 'BUYW', 'YWBU', 'OGYW', 'YWOG', 'GNYW', 'YWGN', 'BNYW', 'YWBN', 'SLYW',
            'YWSL', 'BUVT', 'VTBU', 'OGVT', 'VTOG', 'GNVT', 'VTGN', 'BNVT', 'VTBN', 'SLVT', 'VTSL'],
    'TELALT': ['WHBU', 'BU', 'WHOG', 'OG', 'WHGN', 'GN', 'WHBN', 'BN', 'WHSL', 'SL', 'RDBU', 'BURD', 'RDOG', 'OGRD',
               'RDGN', 'GNRD', 'RDBN', 'BNRD', 'RDSL', 'SLRD', 'BKBU', 'BUBK', 'BKOG', 'OGBK', 'BKGN', 'GNBK', 'BKBN',
               'BNBK', 'BKSL', 'SLBK', 'YWBU', 'BUYW', 'YWOG', 'OGYW', 'YWGN', 'GNYW', 'YWBN', 'BNYW', 'YWSL', 'SLYW',
               'VTBU', 'BUVT', 'VTOG', 'OGVT', 'VTGN', 'GNVT', 'VTBN', 'BNVT', 'VTSL', 'SLVT'],
    'T568A': ['WHGN', 'GN', 'WHOG', 'BU', 'WHBU', 'OG', 'WHBN', 'BN'],
    'T568B': ['WHOG', 'OG', 'WHGN', 'BU', 'WHBU', 'GN', 'WHBN', 'BN'],
}

# Convention: Color names should be 2 letters long, to allow for multicolored wires

_color_hex = {
    'BK': '#000000',
    'WH': '#ffffff',
    'GY': '#999999',
    'PK': '#ff66cc',
    'RD': '#ff0000',
    'OG': '#ff8000',
    'YE': '#ffff00',
    'OL': '#708000',  # olive green
    'GN': '#00ff00',
    'TQ': '#00ffff',
    'LB': '#a0dfff',  # light blue
    'BU': '#0066ff',
    'VT': '#8000ff',
    'BN': '#895956',
    'BG': '#ceb673',  # beige
    'IV': '#f5f0d0',  # ivory
    'SL': '#708090',
    'CU': '#d6775e',  # Faux-copper look, for bare CU wire
    'SN': '#aaaaaa',  # Silvery look for tinned bare wire
    'SR': '#84878c',  # Darker silver for silvered wire
    'GD': '#ffcf80',  # Golden color for gold
}

_color_full = {
    'BK': 'black',
    'WH': 'white',
    'GY': 'grey',
    'PK': 'pink',
    'RD': 'red',
    'OG': 'orange',
    'YE': 'yellow',
    'OL': 'olive green',
    'GN': 'green',
    'TQ': 'turquoise',
    'LB': 'light blue',
    'BU': 'blue',
    'VT': 'violet',
    'BN': 'brown',
    'BG': 'beige',
    'IV': 'ivory',
    'SL': 'slate',
    'CU': 'copper',
    'SN': 'tin',
    'SR': 'silver',
    'GD': 'gold',
}

_color_ger = {
    'BK': 'sw',
    'WH': 'ws',
    'GY': 'gr',
    'PK': 'rs',
    'RD': 'rt',
    'OG': 'or',
    'YE': 'ge',
    'OL': 'ol',  # olivgrün
    'GN': 'gn',
    'TQ': 'tk',
    'LB': 'hb',  # hellblau
    'BU': 'bl',
    'VT': 'vi',
    'BN': 'br',
    'BG': 'bg',  # beige
    'IV': 'eb',  # elfenbeinfarben
    'SL': 'si',  # Schiefer
    'CU': 'ku',  # Kupfer
    'SN': 'vz',  # verzinkt
    'SR': 'ag',  # Silber
    'GD': 'au',  # Gold
}


color_default = '#ffffff'


def get_color_hex(input, pad=False):
    if input is None or input == '':
        return [color_default]
    if len(input) == 4:  # give wires with EXACTLY 2 colors that striped/banded look
        input = input + input[:2]
    # hacky style fix: give single color wires a triple-up so that wires are the same size
    if pad and len(input) == 2:
        input = input + input + input
    try:
        output = [_color_hex[input[i:i + 2]] for i in range(0, len(input), 2)]
    except KeyError:
        print("Unknown color specified")
        output = [color_default]
    return output


def translate_color(input, color_mode):
    if input == '' or input is None:
        return ''
    upper = color_mode.isupper()
    if not (color_mode.isupper() or color_mode.islower()):
        raise Exception('Unknown color mode capitalization')

    color_mode = color_mode.lower()
    if color_mode == 'full':
        output = "/".join([_color_full[input[i:i+2]] for i in range(0,len(input),2)])
    elif color_mode == 'hex':
        output = ':'.join(get_color_hex(input, pad=False))
    elif color_mode == 'ger':
        output = "".join([_color_ger[input[i:i+2]] for i in range(0,len(input),2)])
    elif color_mode == 'short':
        output = input
    else:
        raise Exception('Unknown color mode')
    if upper:
        return output.upper()
    else:
        return output.lower()
