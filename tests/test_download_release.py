import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_release


class PublicReleaseTests(unittest.TestCase):
    def fixture(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            for name in ('AndroidManifest.xml', 'classes.dex', 'lib/arm64-v8a/libchrome.so'):
                z.writestr(name, b'fixture')
        apk = buffer.getvalue()
        base = 'https://github.com/olamidebello/AfricanBrowser/releases/'
        files = {'AfricanBrowser.apk': apk,
                 'SHA256SUMS': (hashlib.sha256(apk).hexdigest() + '  AfricanBrowser.apk\n').encode(),
                 'build-info.json': b'{"platform":"android","cpu":"arm64"}'}
        release = dict(target_commitish='a' * 40, html_url=base + 'tag/android-development-123',
                       assets=[dict(name=n, browser_download_url=base + 'download/android-development-123/' + n) for n in files])
        def fetch(url, **kwargs):
            if '/releases/tags/' in url:
                return io.BytesIO(json.dumps(release).encode())
            return io.BytesIO(files[url.rsplit('/', 1)[-1]])
        return files, fetch

    def test_stages_exact_release_and_current_legal_artwork(self):
        _, fetch = self.fixture()
        with tempfile.TemporaryDirectory() as temp, patch.object(download_release.urllib.request, 'urlopen', side_effect=fetch):
            out = Path(temp) / 'site'
            download_release.stage('123', out)
            info = json.loads((out / 'deployment.json').read_text())
            self.assertEqual(info['run_id'], 123)
            self.assertIn(info['apk'], (out / 'index.html').read_text())
            self.assertTrue((out / 'legal/privacy.html').is_file())
            self.assertTrue((out / 'assets/africanbrowser-logo.png').is_file())

    def test_missing_release_does_not_create_site(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(download_release.urllib.request, 'urlopen', side_effect=HTTPError('url', 404, 'Missing', {}, None)):
            out = Path(temp) / 'site'
            with self.assertRaisesRegex(RuntimeError, 'no public release yet'):
                download_release.stage('123', out)
            self.assertFalse(out.exists())

    def test_tampered_release_is_not_staged(self):
        files, fetch = self.fixture()
        files['AfricanBrowser.apk'] += b'tampered'
        with tempfile.TemporaryDirectory() as temp, patch.object(download_release.urllib.request, 'urlopen', side_effect=fetch):
            out = Path(temp) / 'site'
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                download_release.stage('123', out)
            self.assertFalse(out.exists())
