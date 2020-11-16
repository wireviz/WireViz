#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import base64
from pathlib import Path

mime_subtype_replacements = {'jpg': 'jpeg', 'tif': 'tiff'}

def embed_svg_images(svg_in: str, base_path: Path):
    # first, find any image references in SVG data, and cache the respective base64-encoded image
    images_b64 = {}  # cache of base64-encoded images
    re_xlink=re.compile(r"xlink:href=\"(?P<URL>.*?)\"", re.IGNORECASE)
    for xlink in re_xlink.finditer(svg_in):
        imgurl = xlink.group('URL')
        if not imgurl in images_b64:  # only encode/cache every unique URL once
            if not Path(imgurl).is_absolute():
                imgurl_abs = (Path(base_path) / imgurl).resolve()
            else:
                imgurl_abs = Path(imgurl)

            with open(imgurl_abs,'rb') as img:
                img_bin = img.read()
                img_b64 = base64.b64encode(img_bin)
                img_str = img_b64.decode('utf-8')
            images_b64[imgurl] = img_str
    # second, replace links with the base64-encoded data
    svg_out = svg_in
    for url, b64 in images_b64.items():
        svg_out = svg_out.replace(url, f'data:image/{get_mime_subtype(url)};base64, {b64}')

    return svg_out


def get_mime_subtype(filename: Path):
    mime_subtype = str(Path(filename).suffix[1:]).lower()  # remove `.`
    if mime_subtype in mime_subtype_replacements:
        mime_subtype = mime_subtype_replacements[mime_subtype]
    return mime_subtype


def embed_svg_images_file(filename_in: Path, overwrite: bool = True):
    filename_in = Path(filename_in).resolve()
    filename_out = Path(f'{filename_in.with_suffix("")}.b64.svg')
    with open(filename_in,'r') as file_in, open(filename_out,'w') as file_out:
        file_out.write(embed_svg_images(file_in.read(), filename_in.parent))
    if overwrite:
        filename_out.replace(filename_in)
