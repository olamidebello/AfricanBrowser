import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from branding import apply, brand_strings, STRING_FILES, LITERAL_CHANGES
from browser import gn_args, PLATFORMS, LOCK


class BuildTests(unittest.TestCase):
    def test_branding_does_not_change_symbols_or_credits(self):
        xml = '<grit><message name="IDS_CHROMIUM" desc="Chromium help">Open Chromium <ph name="CHROMIUM">$1<ex>Chromium</ex></ph></message></grit>'
        result = brand_strings(xml)
        self.assertIn('name="IDS_CHROMIUM"', result)
        self.assertIn('desc="Chromium help"', result)
        self.assertIn('name="CHROMIUM"', result)
        self.assertIn('Open AfricanBrowser', result)

    def test_branding_is_idempotent(self):
        xml = '<grit><message name="NAME">Chromium</message></grit>'
        result = brand_strings(xml)
        self.assertEqual(result, brand_strings(result))

    def test_branding_validates_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'chrome/app/theme/chromium/BRANDING'
            path.parent.mkdir(parents=True)
            path.write_text('COPYRIGHT=The Chromium Authors\n')
            with self.assertRaises(RuntimeError):
                apply(folder)
            self.assertEqual(path.read_text(), 'COPYRIGHT=The Chromium Authors\n')

    def test_complete_overlay_and_changed_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)
            brand = source / 'chrome/app/theme/chromium/BRANDING'
            brand.parent.mkdir(parents=True)
            brand.write_text('\n'.join(k + '=Chromium' for k in (
                'PRODUCT_FULLNAME', 'PRODUCT_SHORTNAME', 'PRODUCT_INSTALLER_FULLNAME',
                'PRODUCT_INSTALLER_SHORTNAME', 'MAC_BUNDLE_ID')) + '\nCOPYRIGHT=The Chromium Authors\n')
            for name in STRING_FILES:
                p = source / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('<grit><message name="NAME">Chromium</message></grit>')
            for name, (old, _) in LITERAL_CHANGES.items():
                p = source / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(old)
            apply(source)
            snapshots = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
            apply(source)
            self.assertTrue(all(p.read_bytes() == value for p, value in snapshots.items()))
            self.assertIn('COPYRIGHT=The Chromium Authors', brand.read_text())
            self.assertIn('africanbrowser', (source / 'chrome/common/chrome_paths_linux.cc').read_text())
            (source / 'ios/build/chrome_build.gni').write_text('unexpected upstream change')
            before = brand.read_bytes()
            with self.assertRaises(RuntimeError):
                apply(source)
            self.assertEqual(brand.read_bytes(), before)

    def test_platform_flags_keep_sandbox_defaults(self):
        for target in PLATFORMS:
            args = gn_args(target, 'arm64')
            self.assertIn('is_chrome_branded=false', args)
            self.assertNotIn('no_sandbox', args)
            self.assertNotIn('proprietary_codecs=true', args)
        self.assertIn('target_os="android"', gn_args('android', 'arm64'))
        self.assertIn('chrome_public_manifest_package="org.africanbrowser.browser"', gn_args('android', 'arm64'))
        self.assertIn('target_environment="simulator"', gn_args('ios', 'arm64'))

    def test_lock_uses_immutable_revisions(self):
        for key in ('chromium_revision', 'depot_tools_revision'):
            self.assertRegex(LOCK[key], r'^[a-f0-9]{40}$')


if __name__ == '__main__':
    unittest.main()
