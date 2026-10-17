#!/usr/bin/env python3
"""Build the public static site without network access or third-party dependencies."""
import argparse
import html
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
LEGAL = {'privacy': 'PRIVACY.md', 'terms': 'TERMS.md', 'license': 'LICENSE',
         'notices': 'NOTICE.md', 'copyright': 'COPYRIGHT.md'}

def build(output):
    output = Path(output).resolve()
    if output == ROOT or ROOT.is_relative_to(output):
        raise ValueError('Output must not be the repository or its ancestor')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'assets').mkdir(exist_ok=True)
    (output / 'legal').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'website/index.html', output / 'index.html')
    for name in ('africanbrowser-icon.png', 'africanbrowser-logo.png'):
        shutil.copyfile(ROOT / 'assets/branding' / name, output / 'assets' / name)
    for slug, source in LEGAL.items():
        title = slug.title()
        content = html.escape((ROOT / source).read_text())
        (output / 'legal' / f'{slug}.html').write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{title} — AfricanBrowser</title>'
            '<style>body{max-width:850px;margin:40px auto;padding:0 20px;'
            'font:16px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;'
            'font:inherit}a{color:#17643c}</style><body>'
            f'<a href="../index.html">← AfricanBrowser</a><h1>{title}</h1>'
            f'<pre>{content}</pre></body></html>')
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/website')
    print(build(parser.parse_args().output))
