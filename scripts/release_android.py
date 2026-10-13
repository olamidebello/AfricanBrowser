#!/usr/bin/env python3
"""Sign an APK and validate it on a dedicated ARM64 Android release device."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

PACKAGE = 'org.africanbrowser.browser'


def command(args, binary=False):
    result = subprocess.run([str(a) for a in args], check=True, capture_output=True, text=not binary)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    required = ['ANDROID_KEYSTORE_BASE64', 'ANDROID_KEYSTORE_PASSWORD',
                'ANDROID_KEY_ALIAS', 'ANDROID_SIGNING_CERT_SHA256', 'ADB_SERIAL']
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError('Configure the release worker: ' + ', '.join(missing))
    for name in ('zipalign', 'apksigner', 'aapt', 'adb'):
        if shutil.which(name) is None:
            raise RuntimeError('Install Android SDK tool: ' + name)
    expected = re.sub(r'[^0-9a-f]', '', os.environ['ANDROID_SIGNING_CERT_SHA256'].lower())
    if len(expected) != 64:
        raise RuntimeError('The expected signing certificate must be a SHA-256 fingerprint')
    serial = os.environ['ADB_SERIAL']
    adb = ['adb', '-s', serial]
    if command(adb + ['get-state']).strip() != 'device':
        raise RuntimeError('Dedicated Android release device is unavailable')
    abi = command(adb + ['shell', 'getprop', 'ro.product.cpu.abi']).strip()
    if abi != 'arm64-v8a':
        raise RuntimeError('Use an ARM64 device for this APK')
    existing = command(adb + ['shell', 'pm', 'list', 'packages', PACKAGE])
    if 'package:' + PACKAGE in existing.splitlines():
        raise RuntimeError('Release device already has AfricanBrowser; use a clean test device')
    badging = command(['aapt', 'dump', 'badging', args.apk])
    if f"package: name='{PACKAGE}'" not in badging:
        raise RuntimeError('APK package identity does not match AfricanBrowser')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise RuntimeError('Output already exists; use a fresh release directory')
    if not os.environ.get('ANDROID_KEY_PASSWORD'):
        os.environ['ANDROID_KEY_PASSWORD'] = os.environ['ANDROID_KEYSTORE_PASSWORD']
    with tempfile.TemporaryDirectory(prefix='africanbrowser-signing-') as folder:
        key = Path(folder) / 'release.keystore'
        key.write_bytes(base64.b64decode(os.environ['ANDROID_KEYSTORE_BASE64'], validate=True))
        key.chmod(0o600)
        aligned = Path(folder) / 'aligned.apk'
        command(['zipalign', '-P', '16', '-f', '4', args.apk, aligned])
        command(['apksigner', 'sign', '--ks', key, '--ks-key-alias', os.environ['ANDROID_KEY_ALIAS'],
                 '--ks-pass', 'env:ANDROID_KEYSTORE_PASSWORD', '--key-pass', 'env:ANDROID_KEY_PASSWORD',
                 '--out', args.output, aligned])
    signature = command(['apksigner', 'verify', '--verbose', '--print-certs', args.output])
    match = re.search(r'Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]+)', signature)
    if not match or match.group(1).lower() != expected:
        args.output.unlink(missing_ok=True)
        raise RuntimeError('Signed APK certificate does not match the expected release identity')
    command(['zipalign', '-c', '-P', '16', '4', args.output])
    installed = False
    try:
        output = command(adb + ['install', str(args.output)])
        if 'Success' not in output:
            raise RuntimeError('APK installation did not succeed')
        installed = True
        command(adb + ['shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW',
                       '-d', 'https://example.com', '-p', PACKAGE])
        passed = False
        for attempt in range(12):
            time.sleep(2)
            command(adb + ['shell', 'uiautomator', 'dump', '/sdcard/africanbrowser-release-test.xml'])
            xml = command(adb + ['exec-out', 'cat', '/sdcard/africanbrowser-release-test.xml'])
            tree = ET.fromstring(xml)
            nodes = list(tree.iter('node'))
            if any('Example Domain' in node.get('text', '') for node in nodes):
                passed = True
                break
            # Complete only the fresh test install's standard English onboarding.
            labels = {'Accept & continue', 'No thanks', 'Use without an account'}
            for node in nodes:
                if node.get('text') in labels and node.get('enabled') == 'true':
                    bounds = re.findall(r'\d+', node.get('bounds', ''))
                    if len(bounds) == 4:
                        x1, y1, x2, y2 = map(int, bounds)
                        command(adb + ['shell', 'input', 'tap', str((x1 + x2) // 2), str((y1 + y2) // 2)])
                        break
        if not passed:
            raise RuntimeError('Browser did not display the HTTPS test page; do not publish this APK')
        screenshot = command(adb + ['exec-out', 'screencap', '-p'], binary=True)
        (args.output.parent / 'android-smoke-test.png').write_bytes(screenshot)
        with args.output.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        report = {'package': PACKAGE, 'abi': abi, 'certificate_sha256': expected,
                  'apk_sha256': digest, 'installation': 'passed', 'https_navigation': 'passed',
                  'test_url': 'https://example.com',
                  'scope': 'Native installation and HTTPS navigation smoke test; not Chrome feature-parity certification'}
        (args.output.parent / 'device-smoke-test.json').write_text(json.dumps(report, indent=2) + '\n')
        (args.output.parent / 'SHA256SUMS').write_text(digest + '  ' + args.output.name + '\n')
        print('Release APK signature, alignment, installation and HTTPS navigation passed.')
    except Exception:
        args.output.unlink(missing_ok=True)
        raise
    finally:
        if installed:
            command(adb + ['uninstall', PACKAGE])
        command(adb + ['shell', 'rm', '-f', '/sdcard/africanbrowser-release-test.xml'])


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError, ET.ParseError) as error:
        # Subprocess exceptions contain argument names, not plaintext passwords.
        raise SystemExit(str(error))
