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

_default_color = '#ffffff'

# default_bkgnd_color = '#ffffff' # white
default_bknd_color = '#fffbf8'  # off-white beige-ish

color_hex = {
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

# TODO: Add a helper method for this, that can deal with banded wires
color_full = {
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
    'TI': 'tinned copper',
}

# TODO Help wanted! Need help translating colors/banded colors to german shortcodes
color_ger = {
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
}


def get_color_hex(input):
    if len(input) == 4:  # give wires with EXACTLY 2 colors that striped/banded look
        input = input + input[:2]
    output = ''
    for i in range(0, len(input), 2):  # Split into 2 letter chunks
        if input[i:i + 2] in color_hex:
            output += color_hex[input[i:i + 2]]
            if i + 2 != len(input):
                output += ':'
    if output == '':
        output = _default_color
    return output


def translate_color(input, color_mode):
    if input == '':
        output = ''
    else:
        if color_mode == 'full':
            output = color_full[input].lower()
        elif color_mode == 'FULL':
            output = color_full[input].upper()
        elif color_mode == 'hex':
            output = get_color_hex(input).lower()
        elif color_mode == 'HEX':
            output = get_color_hex(input).upper()
        elif color_mode == 'ger':
            output = color_ger[input].lower()
        elif color_mode == 'GER':
            output = color_ger[input].upper()
        elif color_mode == 'short':
            output = input.lower()
        elif color_mode == 'SHORT':
            output = input.upper()
        else:
            raise Exception('Unknown color mode')
    return output
