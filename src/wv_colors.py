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

shield_color = 'TI'

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
    'BN': '#a52a2a',
    'SL': '#708090',
    # Faux-copper look, for bare CU wire
    'CU': '#d6775e:#895956',
    # Silvery look for tinned bare wire
    'TI': '#aaaaaa:#84878c',
    # Yellow-green PE wire
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
    'TI': 'tinned copper',  # Could be changed to SN, as that's the elemental symbol
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
    'CU': 'ku',
    # Tinned
    'TI': 'si'
}



def get_color_hex(input):
    if len(input) == 4:  # give wires with EXACTLY 2 colors that striped/banded look
        input = input + input[:2]
    try:
        output = ":".join([_color_hex[input[i:i + 2]] for i in range(0, len(input), 2)])
    except KeyError:
        raise Exception('Unknown Color Name')
    if output == '':
        output = default_color
    return output


def translate_color(input, color_mode):
    if input == '':
        return ''
    upper = color_mode.isupper()
    if not (color_mode.isupper() or color_mode.islower()):
        raise Exception('Unknown color mode capitalization')

    color_mode = color_mode.lower()
    if color_mode == 'full':
        output = "/".join([_color_full[input[i:i+2]] for i in range(0,len(input),2)])
    elif color_mode == 'hex':
        output = get_color_hex(input)
    elif color_mode == 'ger':
        output = "".join([_color_ger[input[i:i+2]] for i in range(o,len(input),2)])
    elif color_mode == 'short':
        output = input
    else:
        raise Exception('Unknown color mode')
    if upper:
        return output.upper()
    else:
        return output.lower()

