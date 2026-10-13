"""Generate self-contained legal pages from the authoritative repository notices."""
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LEGAL_FILES = ('LICENSE', 'COPYRIGHT.md', 'NOTICE.md', 'TERMS.md', 'PRIVACY.md')
PAGES = {'privacy': 'PRIVACY.md', 'terms': 'TERMS.md', 'copyright': 'COPYRIGHT.md',
         'notices': 'NOTICE.md', 'license': 'LICENSE'}


def paragraphs(text):
    blocks = []
    for block in re.split(r'\n\s*\n', text.strip()):
        if block.startswith('#'):
            line = block.splitlines()[0]
            level = min(len(line) - len(line.lstrip('#')), 6)
            blocks.append(f'<h{level}>' + escape(line.lstrip('#').strip()) + f'</h{level}>')
        else:
            blocks.append('<p>' + escape(' '.join(block.splitlines())) + '</p>')
    return '\n'.join(blocks)


def generate():
    product = json.loads((ROOT / 'config/product.json').read_text())
    documents = {name: (ROOT / path).read_text() for name, path in PAGES.items()}
    documents['about'] = ('# AfricanBrowser\n\nOwner: ' + product['owner'] +
        '\n\nCopyright © ' + str(product['copyright_year']) + ' ' + product['owner'] +
        ' for eligible original AfricanBrowser work.\n\n' + product['slogan'] +
        '\n\nOriginal code license: ' + product['code_license'] +
        '. Upstream Chromium and other components retain their own licenses and attribution.' +
        '\n\nThis is an independent Chromium distribution project. Build and release validation '
        'status is documented in the repository; this page does not certify a production binary.' +
        '\n\nProject: https://github.com/olamidebello/AfricanBrowser')
    nav = ' · '.join(f'<a href="{name}.html">{name.title()}</a>' for name in documents)
    output = []
    for base in (ROOT / 'ai/web/legal', ROOT / 'extensions/africanbrowser-support/legal'):
        base.mkdir(parents=True, exist_ok=True)
        for name, text in documents.items():
            body = '<pre>' + escape(text) + '</pre>' if name == 'license' else paragraphs(text)
            page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>AfricanBrowser ' + escape(name.title()) + '</title>'
                    '<link rel="stylesheet" href="../style.css"></head><body><main>'
                    '<nav aria-label="Legal pages">' + nav + '</nav>' + body +
                    '<p><a href="../index.html">Back to local support</a></p>'
                    '</main></body></html>\n')
            path = base / (name + '.html')
            path.write_text(page)
            output.append(str(path.relative_to(ROOT)))
    return output


if __name__ == '__main__':
    print('\n'.join(generate()))
