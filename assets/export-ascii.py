#!/usr/bin/env python3
"""Turunkan simbol Const menjadi ASCII untuk Fastfetch saja."""
from io import BytesIO
from pathlib import Path
import subprocess
from PIL import Image

root = Path(__file__).resolve().parents[1]
render = subprocess.run(['rsvg-convert', '-w', '70', '-h', '35', str(root / 'assets/const-logo.svg')],
                        check=True, capture_output=True)
image = Image.open(BytesIO(render.stdout)).convert('RGBA').resize((35, 18))
rows = [''.join('#' if image.getpixel((x, y))[3] > 110 else ' '
                for x in range(image.width)).rstrip() for y in range(image.height)]
while rows and not rows[0]:
    rows.pop(0)
while rows and not rows[-1]:
    rows.pop()
left = min(len(row) - len(row.lstrip()) for row in rows if row)
(root / 'desktop/fastfetch/const.txt').write_text('\n'.join('$1' + row[left:] for row in rows) + '\n')
