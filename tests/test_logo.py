import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from logo_assets import apply, emblem, LOGO


class LogoTests(unittest.TestCase):
    def test_icon_uses_complete_supplied_artwork(self):
        with Image.open(LOGO) as original:
            self.assertEqual(emblem().size, original.size)
            self.assertEqual(emblem().tobytes(), original.convert('RGB').tobytes())

    def test_overlay_preserves_dimensions_and_generates_native_formats(self):
        original = LOGO.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            names = {
                'chrome/app/theme/chromium/product_logo_16.png': (16, 16),
                'chrome/android/java/res_chromium_base/mipmap-mdpi/app_icon.png': (48, 48),
                'chrome/android/java/res_chromium_base/mipmap-mdpi/layered_app_icon.png': (108, 108),
                'chrome/android/java/res_chromium_base/mipmap-mdpi/layered_app_icon_background.png': (108, 108),
                'ios/chrome/app/resources/ChromiumIconsLegacy.xcassets/AppIcon.appiconset/Icon-1024Tinted.png': (1024, 1024),
                'ios/chrome/app/resources/ChromiumIcons.xcassets/AppIcon.icon/Assets/ring.png': (1024, 1024),
            }
            for name, size in names.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', size, 'white').save(p)
            icon = root / 'ios/chrome/app/resources/ChromiumIcons.xcassets/AppIcon.icon/icon.json'
            icon.write_text(json.dumps({'groups': [], 'supported-platforms': {'ios': 'square'}}))
            for name in ['chrome/app/theme/chromium/win/chromium.ico',
                         'chrome/app/theme/chromium/mac/app.icns']:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch()
            changed = apply(root)
            for name, size in names.items():
                with Image.open(root / name) as image:
                    self.assertEqual(image.size, size)
            with Image.open(root / 'chrome/app/theme/chromium/win/chromium.ico') as image:
                self.assertEqual(image.format, 'ICO')
            with Image.open(root / 'chrome/app/theme/chromium/mac/app.icns') as image:
                self.assertEqual(image.format, 'ICNS')
            self.assertIn('ios/chrome/app/resources/ChromiumIcons.xcassets/AppIcon.icon/icon.json', changed)
            self.assertEqual(json.loads(icon.read_text())['supported-platforms'], {'ios': 'square'})
        self.assertEqual(LOGO.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
