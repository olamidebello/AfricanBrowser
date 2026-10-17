import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_website', ROOT / 'scripts/build_website.py')
website = importlib.util.module_from_spec(spec)
spec.loader.exec_module(website)

class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if name in attrs:
                self.references.append(attrs[name])

class WebsiteTests(unittest.TestCase):
    def test_generated_pages_have_resolvable_local_links(self):
        with tempfile.TemporaryDirectory() as temp:
            output = website.build(temp)
            for page in output.rglob('*.html'):
                parser = References()
                parser.feed(page.read_text())
                for reference in parser.references:
                    if reference.startswith('https://'):
                        continue
                    if reference.startswith('#'):
                        self.assertIn(reference[1:], parser.ids)
                    else:
                        self.assertTrue((page.parent / reference).exists(), reference)
    def test_legal_content_is_preserved_and_escaped(self):
        with tempfile.TemporaryDirectory() as temp:
            output = website.build(temp)
            self.assertIn(website.html.escape((ROOT / 'PRIVACY.md').read_text()),
                          (output / 'legal/privacy.html').read_text())
