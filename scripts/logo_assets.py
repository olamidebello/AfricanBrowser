"""Convert the supplied logo to browser icon formats; preserve original artwork."""
import argparse
import base64
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / 'assets/branding/africanbrowser-logo.png'
ICON_ROOTS = (
    'chrome/app/theme/chromium',
    'chrome/app/theme/default_100_percent/chromium',
    'chrome/app/theme/default_200_percent/chromium',
    'chrome/app/theme/default_300_percent/chromium',
    'chrome/android/java/res_chromium_base',
    'ios/chrome/app/resources/ChromiumIcons.xcassets',
    'ios/chrome/app/resources/ChromiumIconsLegacy.xcassets',
)


def emblem():
    with Image.open(LOGO) as original:
        original.load()
        # Use the complete supplied artwork on every platform, including its wordmark.
        return original.convert('RGB')


def render(image, size, padding=0):
    canvas = Image.new('RGB', size, 'black')
    available = tuple(max(1, round(n * (1 - 2 * padding))) for n in size)
    logo = ImageOps.contain(image, available, Image.Resampling.LANCZOS)
    canvas.paste(logo, ((size[0] - logo.width) // 2, (size[1] - logo.height) // 2))
    return canvas


def apply(source):
    source = Path(source)
    image = emblem()
    pngs = set()
    for folder in ICON_ROOTS[:4]:
        pngs.update((source / folder).rglob('product_logo*.png'))
    android = source / ICON_ROOTS[4]
    launcher_icons = set(android.glob('mipmap-*/app_icon.png'))
    adaptive_icons = set(android.glob('mipmap-*/layered_app_icon.png'))
    if not launcher_icons or not adaptive_icons:
        raise RuntimeError('Required Android launcher icons missing; refusing an unbranded build')
    # Cover branded Android channel/splash/product images as well as launchers.
    for pattern in ('**/product_logo*.png', '**/chromium_logo*.png', '**/chromium.png'):
        pngs.update(android.glob(pattern))
    pngs.update(launcher_icons)
    pngs.update(adaptive_icons)
    backgrounds = set(android.glob('mipmap-*/layered_app_icon_background.png'))
    mac = source / 'chrome/app/theme/chromium/mac'
    pngs.update((mac / 'Assets.xcassets').rglob('appicon_*.png'))
    pngs.update((mac / 'Assets.xcassets/Icon.iconset').glob('*.png'))
    pngs.update((source / ICON_ROOTS[6]).rglob('Icon-*.png'))
    # Keep existing SVG resource names and dimensions so build references stay valid.
    svgs = set()
    for folder in ICON_ROOTS[:5]:
        for pattern in ('product_logo*.svg', 'chromium_logo*.svg', 'chromium.svg'):
            svgs.update((source / folder).rglob(pattern))
    svg_outputs = {}
    encoded = base64.b64encode(LOGO.read_bytes()).decode('ascii')
    for path in sorted(svgs):
        root = ET.fromstring(path.read_text())
        attrs = {key: root.attrib[key] for key in ('width', 'height', 'viewBox') if key in root.attrib}
        if 'viewBox' not in attrs:
            attrs['viewBox'] = '0 0 1024 1024'
        x, y, width, height = attrs['viewBox'].split()
        svg = ET.Element('svg', {'xmlns': 'http://www.w3.org/2000/svg', **attrs})
        ET.SubElement(svg, 'image', {'x': x, 'y': y, 'width': width, 'height': height,
                                  'preserveAspectRatio': 'xMidYMid meet',
                                  'href': 'data:image/png;base64,' + encoded})
        svg_outputs[path] = ET.tostring(svg, encoding='unicode')
    compositions = []
    for folder in (mac / 'AppIcon.icon', source / ICON_ROOTS[5] / 'AppIcon.icon'):
        config = folder / 'icon.json'
        if config.exists():
            data = json.loads(config.read_text())
            ring = folder / 'Assets/ring.png'
            if not ring.is_file() or not isinstance(data.get('groups'), list):
                raise RuntimeError(f'Upstream Apple icon structure changed: {folder}')
            # Reuse an existing tracked resource so GN dependencies remain intact.
            data['fill'] = {'solid': 'extended-gray:0.00000,1.00000'}
            data['groups'] = [{'layers': [{'image-name': 'ring.png',
                                          'name': 'AfricanBrowser', 'glass': False}],
                               'shadow': {'kind': 'none', 'opacity': 0},
                               'translucency': {'enabled': False, 'value': 0}}]
            compositions.append((config, data))
            pngs.add(ring)
    ico = source / 'chrome/app/theme/chromium/win/chromium.ico'
    icns = mac / 'app.icns'
    if not pngs or not ico.exists() or not icns.exists():
        raise RuntimeError('Required upstream browser icons missing; check pinned source')
    # Decode every PNG before changing files so malformed upstream inputs fail early.
    sizes = {}
    for p in sorted(pngs | backgrounds):
        with Image.open(p) as old:
            old.load()
            sizes[p] = old.size
    changed = []
    for p, size in sizes.items():
        if p in backgrounds:
            output = Image.new('RGB', size, 'black')
        else:
            padding = .18 if p.name == 'layered_app_icon.png' else .025
            output = render(image, size, padding)
            if 'Tinted' in p.name or '_mono' in p.name:
                output = ImageOps.grayscale(output).convert('RGB')
        output.save(p, format='PNG')
        changed.append(str(p.relative_to(source)))
    render(image, (256, 256)).save(ico, format='ICO', sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    render(image, (1024, 1024)).save(icns, format='ICNS')
    changed.extend([str(ico.relative_to(source)), str(icns.relative_to(source))])
    for p, data in compositions:
        p.write_text(json.dumps(data, indent=2) + '\n')
        changed.append(str(p.relative_to(source)))
    for p, text in svg_outputs.items():
        p.write_text(text, encoding='utf-8')
        changed.append(str(p.relative_to(source)))
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if args.source:
        print(json.dumps(apply(args.source), indent=2))
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        render(emblem(), (512, 512), .025).save(args.preview)
    if not args.source and not args.preview:
        parser.error('Provide --source or --preview')
