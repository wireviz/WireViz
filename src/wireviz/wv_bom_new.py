# -*- coding: utf-8 -*-

from collections import namedtuple
from typing import Any, Dict, List, Optional, Tuple, Union

BOM_HASH_FIELDS = 'description unit pn manufacturer mpn supplier spn'
Bom_hash = namedtuple('Bom_hash', BOM_HASH_FIELDS)
Bom_hash_list = namedtuple('Bom_hash_list', BOM_HASH_FIELDS)

HEADER_PN = 'P/N'
HEADER_MPN = 'MPN'
HEADER_SPN = 'SPN'

def pn_info_string(header: str, name: Optional[str], number: Optional[str]) -> Optional[str]:
    """Return the company name and/or the part number in one single string or None otherwise."""
    number = str(number).strip() if number is not None else ''
    if name or number:
        return f'{name if name else header}{": " + number if number else ""}'
    else:
        return None
