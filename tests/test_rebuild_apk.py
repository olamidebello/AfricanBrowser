import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import rebuild_apk


class DeploymentTests(unittest.TestCase):
    def artifact(self, folder):
        folder.mkdir(parents=True, exist_ok=True)
        apk = folder / 'AfricanBrowser.apk'
        with zipfile.ZipFile(apk, 'w') as archive:
            for name in ('AndroidManifest.xml', 'classes.dex', 'lib/arm64-v8a/libchrome.so'):
                archive.writestr(name, b'fixture')
        checksum = hashlib.sha256(apk.read_bytes()).hexdigest()
        (folder / 'SHA256SUMS').write_text(checksum + '  AfricanBrowser.apk\n')
        (folder / 'build-info.json').write_text(json.dumps({
            'platform': 'android', 'cpu': 'arm64',
            'upstream': json.loads(Path('config/upstream.json').read_text())}))
        return apk

    def test_checksum_rejects_tampered_apk(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = self.artifact(Path(folder))
            rebuild_apk.verify_apk(apk)
            apk.write_bytes(apk.read_bytes() + b'tampered')
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                rebuild_apk.verify_apk(apk)

    def test_exact_run_stages_versioned_download_and_fresh_homepage(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'site'
            request = {}
            def github(*args):
                if args[0] == 'api':
                    return json.dumps({'sha': 'a' * 40})
                if args[:2] == ('workflow', 'run'):
                    request['title'] = args[-1].split('=', 1)[1]
                    return ''
                if args[:2] == ('run', 'list'):
                    return json.dumps([{'databaseId': 123, 'displayTitle': request['title'],
                                        'headSha': 'a' * 40, 'status': 'completed', 'conclusion': 'success'}])
                if args[:2] == ('run', 'download'):
                    self.artifact(Path(args[-1]) / 'nested')
                    return ''
                raise AssertionError(args)
            with patch.object(sys, 'argv', ['rebuild_apk.py', '--output', str(output)]), \
                 patch.object(rebuild_apk, 'gh', side_effect=github), \
                 patch.object(rebuild_apk.subprocess, 'check_output', return_value='a' * 40):
                rebuild_apk.main()
            self.assertTrue((output / 'downloads/android-123/AfricanBrowser.apk').is_file())
            text = (output / 'index.html').read_text()
            self.assertIn('downloads/android-123/AfricanBrowser.apk', text)
            self.assertIn('downloads/android-123/SHA256SUMS', text)
            self.assertNotIn('528 MB', text)
            self.assertEqual(json.loads((output / 'deployment.json').read_text())['source'], 'a' * 40)


if __name__ == '__main__':
    unittest.main()
