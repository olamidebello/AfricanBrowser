import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from branding import ANDROID_NAME_FILE, brand_android_names, apply, brand_strings, STRING_FILES, LITERAL_CHANGES
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
                'COMPANY_FULLNAME', 'COMPANY_SHORTNAME',
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
            android_names = source / ANDROID_NAME_FILE
            android_names.parent.mkdir(parents=True, exist_ok=True)
            android_names.write_text('<resources><!-- Copyright The Chromium Authors -->' + ''.join(
                f'<string name="{name}" translatable="false">Chromium{suffix}</string>'
                for name, suffix in [('app_name', ''), ('bookmark_widget_title', ' bookmarks'),
                                     ('search_widget_title', ' search'),
                                     ('quick_action_search_widget_title', ' quick action search')]) + '</resources>')
            apply(source)
            self.assertEqual(ET.fromstring(android_names.read_text()).find("string[@name='app_name']").text,
                             'AfricanBrowser')
            self.assertIn('Copyright The Chromium Authors', android_names.read_text())
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

    def test_android_names_reject_incomplete_resources(self):
        with self.assertRaises(RuntimeError):
            brand_android_names('<resources><string name="app_name">Chromium</string></resources>')

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

class AndroidLauncherBrandingTests(unittest.TestCase):
    def test_launcher_name_removes_channel_suffix(self):
        text = '<resources>' + ''.join(
            '<string name="' + name + '">Chromium Development</string>'
            for name in ['app_name', 'bookmark_widget_title', 'search_widget_title',
                         'quick_action_search_widget_title']) + '</resources>'
        self.assertIn('<string name="app_name">AfricanBrowser</string>',
                      brand_android_names(text))

class VisibleResourceBrandingTests(unittest.TestCase):
    def test_translations_preserve_attribution_and_urls(self):
        from branding import brand_resource
        text = '<translationbundle><translation id="1">Open Chromium</translation><translation id="2">The Chromium Authors</translation><translation id="3">https://Chromium.org</translation></translationbundle>'
        result = brand_resource(text)
        self.assertIn('Open AfricanBrowser', result)
        self.assertIn('The Chromium Authors', result)
        self.assertIn('https://Chromium.org', result)
        self.assertEqual(result, brand_resource(result))
