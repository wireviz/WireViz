#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import base64
from pathlib import Path

def embed_svg_images(fn):
    fn = Path(fn).resolve()
    images_b64 = {}  # cache base-64 encoded images
    num_images = 0   # just for debugging
    re_xlink=re.compile(r"xlink:href=\"(?P<URL>.*?)\"")
    with open(fn) as file_in, open(f'{fn.with_suffix("")}.b64.svg','w') as file_out:
        for line in file_in:
            for xlink in re_xlink.finditer(line):
                num_images = num_images + 1
                imgurl = xlink.group(1)
                print(' Found URL in SVG:', imgurl)
                if not imgurl in images_b64:
                    print('  ✅This URL is new')
                    if not Path(imgurl).is_absolute():  # resolve relative image path
                        imgurl_abs = (Path(fn).parent / imgurl).resolve()
                        print(imgurl, '-->', imgurl_abs)
                    else:
                        imgurl_abs = imgurl
                    with open(imgurl_abs, 'rb') as img:
                        data_bin = img.read()
                        data_b64 = base64.b64encode(data_bin)
                        data_str = data_b64.decode('utf-8')
                    images_b64[imgurl] = data_str
                else:  # only cache every image once
                    print('  ❌This URL is not new')
                line = line.replace(imgurl, f'data:image/png;base64, {images_b64[imgurl]}')
            file_out.write(line)

    print(f'Embedded {num_images} instances of {len(images_b64)} different images.')
    print()

# for debugging, run:
# python -m svgembed.py path/to/file.svg
if __name__ == '__main__':
    import sys
    embed_svg_images(sys.argv[1])
