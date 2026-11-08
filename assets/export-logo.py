#!/usr/bin/env python3
"""Ekspor logo Const dari satu master SVG; jalankan manual sebelum build."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Direktori ekspor alternatif untuk pemeriksaan.')
    args = parser.parse_args()
    assets = Path(__file__).resolve().parent
    output = args.output if args.output is not None else assets / 'exports'
    output.mkdir(parents=True, exist_ok=True)
    master = ET.parse(assets / 'const-logo.svg')
    black = ET.fromstring(ET.tostring(master.getroot()))
    black.set('color', '#161616')
    ET.ElementTree(black).write(output / 'const-logo-black.svg', encoding='utf-8', xml_declaration=True)

    # Badge netral menjaga logo OS terbaca pada tema aplikasi terang maupun gelap.
    icon = ET.fromstring(ET.tostring(master.getroot()))
    icon.insert(0, ET.Element(f'{{{SVG}}}rect', {
        'x': '64', 'y': '64', 'width': '384', 'height': '384', 'rx': '48', 'fill': '#161616',
    }))
    ET.ElementTree(icon).write(output / 'constos.svg', encoding='utf-8', xml_declaration=True)
    with tempfile.TemporaryDirectory(prefix='constos-logo-') as tmp:
        # Warna eksplisit pada root SVG juga dipakai renderer raster boot.
        source = Path(tmp) / 'const-logo.svg'
        master.write(source, encoding='utf-8', xml_declaration=True)
        subprocess.run([
            'rsvg-convert', '--width', '160', '--height', '160',
            '--output', str(output / 'const-logo-boot.png'), str(source),
        ], check=True)
    print(f'Ekspor logo: {output}')


if __name__ == '__main__':
    main()
