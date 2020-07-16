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

default_color = '#ffffff'

# default_bkgnd_color = '#ffffff' # white
default_bknd_color = '#fffbf8'  # off-white beige-ish

# Convention: Color names should be 2 letters long, to allow for multicolored wires

shield_color = '#aaaaaa' # Tinned wire

_color_hex = {
    'BK': '#000000',
    'WH': '#ffffff',
    'GY': '#999999',
    'PK': '#ff66cc',
    'RD': '#ff0000',
    'OG': '#ff8000',
    'YE': '#ffff00',
    'GN': '#00ff00',
    'TQ': '#00ffff',
    'BU': '#0066ff',
    'VT': '#8000ff',
    'BN': '#895956',
    'SL': '#708090',
    # Faux-copper look, for bare CU wire
    'CU': '#d6775e',
    # Silvery look for tinned bare wire
    'SN': '#aaaaaa',
    # Darker silver for silvered wire
    'AG': '#84878c',
    # Golden color for gold
    'AU': '#ffcf80',
    # Yellow-green PE wire (matching actual wire colors, should prevent confusion with a yellow-green dual color wire
    'PE': '#54aa85:#f7f854:#54aa85',
}

_color_full = {
    'BK': 'black',
    'WH': 'white',
    'GY': 'grey',
    'PK': 'pink',
    'RD': 'red',
    'OG': 'orange',
    'YE': 'yellow',
    'GN': 'green',
    'TQ': 'turquoise',
    'BU': 'blue',
    'VT': 'violet',
    'BN': 'brown',
    'SL': 'slate',
    'CU': 'bare copper',
    'SN': 'tinned copper',
    'AG': 'silver wire',
    'AU': 'gold wire',
    'PE': 'earth'
}

# TODO Help wanted: can someone check the german translation?
_color_ger = {
    'BK': 'sw',
    'WH': 'ws',
    'GY': 'gr',
    'PK': 'rs',
    'RD': 'rt',
    'OG': 'or',
    'YE': 'ge',
    'GN': 'gn',
    'TQ': 'tk',
    'BU': 'bl',
    'VT': 'vi',
    'BN': 'br',
    # To the best of my ability, likely incorrect:

    # Slate --> Schieferfarbe --> SI ??
    'SL': 'si',
    # Copper
    'CU': 'cu',
    # Tinned
    'SN': 'sn',
    # Silver
    'AG': 'ag',
    # Gold
    'AU': 'au',
    # Earth
    'PE': 'pe'
}



def get_color_hex(input, pad=True):
    if input is None or input == '':
        # print('Unspecified color requested', file=sys.stderr)
        return [default_color]
    if len(input) == 4:  # give wires with EXACTLY 2 colors that striped/banded look
        input = input + input[:2]
    # hacky style fix: give single color wires a triple-up so that wires are the same size
    if pad and len(input) == 2:
        input = input + input + input
    try:
        output = [_color_hex[input[i:i + 2]] for i in range(0, len(input), 2)]
    except KeyError:
        print("Unknown Color Specified", file=sys.stderr)
        output = [default_color]
        # raise Exception('Unknown Color Name')
    return output


def translate_color(input, color_mode):
    if input == '' or input is None:
        # print('Unspecified color requested', file=sys.stderr)
        return default_color
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

