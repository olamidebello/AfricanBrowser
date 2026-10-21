#!/usr/bin/env python3
"""Stage one explicit public GitHub release without a server login."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request
from build_website import build
from rebuild_apk import verify_apk


def stage(run_id, output):
    if not re.fullmatch(r'[0-9]+', str(run_id)):
        raise ValueError('Expected a numeric GitHub build run ID')
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory')
    tag = 'android-development-' + str(run_id)
    api = 'https://api.github.com/repos/olamidebello/AfricanBrowser/releases/tags/' + tag
    try:
        with urllib.request.urlopen(api, timeout=60) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise RuntimeError('The requested build has no public release yet. Wait for compilation and release publication; no older APK was selected.') from error
        raise
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as folder:
        temporary = Path(folder)
        artifact = temporary / 'artifact'
        artifact.mkdir()
        for name in ('AfricanBrowser.apk', 'SHA256SUMS', 'build-info.json'):
            assets = [a for a in release['assets'] if a['name'] == name]
            if len(assets) != 1:
                raise RuntimeError('Missing or ambiguous release asset: ' + name)
            url = assets[0]['browser_download_url']
            expected = 'https://github.com/olamidebello/AfricanBrowser/releases/download/' + tag + '/'
            if url != expected + name:
                raise RuntimeError('Unexpected release asset URL')
            with urllib.request.urlopen(url, timeout=300) as response, (artifact / name).open('wb') as stream:
                shutil.copyfileobj(response, stream)
        digest = verify_apk(artifact / 'AfricanBrowser.apk')
        info = json.loads((artifact / 'build-info.json').read_text())
        if info.get('platform') != 'android' or info.get('cpu') != 'arm64':
            raise RuntimeError('Expected an Android ARM64 build')
        site = build(temporary / 'site')
        relative = 'downloads/android-' + str(run_id)
        destination = site / relative
        shutil.copytree(artifact, destination)
        index = site / 'index.html'
        text, count = re.subn(r'https://github.com/olamidebello/AfricanBrowser/releases/download/[^" ]+/AfricanBrowser.apk', relative + '/AfricanBrowser.apk', index.read_text())
        if count != 1:
            raise RuntimeError('Website APK anchor changed')
        text = re.sub(r'https://github.com/olamidebello/AfricanBrowser/releases/tag/[^" ]+', release['html_url'], text)
        text = re.sub(r'Published October 15, 2026\. APK size: approximately 528 MB\.',
                      f'Build {run_id}. APK size: {(artifact / "AfricanBrowser.apk").stat().st_size / 1024**2:.1f} MiB.', text)
        index.write_text(text)
        (site / 'deployment.json').write_text(json.dumps(dict(
            run_id=int(run_id), source=release['target_commitish'], apk=relative + '/AfricanBrowser.apk',
            sha256=digest, release=release['html_url']), indent=2) + '\n')
        site.rename(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    stage(args.run_id, args.output)
