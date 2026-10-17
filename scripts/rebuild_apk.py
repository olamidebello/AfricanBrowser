#!/usr/bin/env python3
"""Request an exact-source GitHub build and stage a verified development download."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from build_website import build


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, timeout=120)


def verify_apk(apk):
    checksum_file = apk.parent / 'SHA256SUMS'
    matches = []
    for line in checksum_file.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == 'AfricanBrowser.apk':
            matches.append(parts[0])
    if len(matches) != 1 or not re.fullmatch(r'[0-9a-f]{64}', matches[0]):
        raise RuntimeError('Missing or ambiguous APK checksum')
    with apk.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != matches[0]:
        raise RuntimeError('APK checksum mismatch')
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        if not {'AndroidManifest.xml', 'classes.dex'}.issubset(names) or not any(
                n.startswith('lib/arm64-v8a/') and n.endswith('.so') for n in names):
            raise RuntimeError('Artifact is not an ARM64 browser APK')
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='olamidebello/AfricanBrowser')
    parser.add_argument('--ref', default='main')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=100800)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        parser.error('Expected owner/repository')
    if args.output.exists():
        parser.error('Use a fresh staging output directory')
    local_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    remote_sha = json.loads(gh('api', f'repos/{args.repo}/commits/{args.ref}'))['sha']
    if local_sha != remote_sha:
        raise RuntimeError('Repository advanced after pull; rerun to build the current source')
    request = 'deploy-' + uuid.uuid4().hex
    gh('workflow', 'run', 'android-apk.yml', '--repo', args.repo, '--ref', args.ref,
       '-f', 'deploy_request=' + request)
    deadline = time.monotonic() + args.timeout
    run = None
    while time.monotonic() < deadline:
        runs = json.loads(gh('run', 'list', '--repo', args.repo, '--workflow',
                            'android-apk.yml', '--event', 'workflow_dispatch', '--limit', '100',
                            '--json', 'databaseId,displayTitle,headSha,status,conclusion'))
        found = [r for r in runs if r['displayTitle'] == request and r['headSha'] == local_sha]
        if len(found) > 1:
            raise RuntimeError('Ambiguous build request')
        if found:
            run = found[0]
            if run['status'] == 'completed':
                if run['conclusion'] != 'success':
                    raise RuntimeError(f"Build {run['databaseId']} ended: {run['conclusion']}")
                break
        time.sleep(min(30, max(0, deadline - time.monotonic())))
    else:
        raise RuntimeError('Build wait timed out; existing deployment was preserved')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
        temp = Path(temporary)
        gh('run', 'download', str(run['databaseId']), '--repo', args.repo,
           '--name', 'AfricanBrowser-Android-ARM64-development', '--dir', str(temp / 'artifact'))
        apks = list((temp / 'artifact').rglob('AfricanBrowser.apk'))
        if len(apks) != 1:
            raise RuntimeError('Expected exactly one APK')
        apk = apks[0]
        digest = verify_apk(apk)
        info = json.loads((apk.parent / 'build-info.json').read_text())
        lock = json.loads(Path('config/upstream.json').read_text())
        if info['upstream'] != lock or info['platform'] != 'android' or info['cpu'] != 'arm64':
            raise RuntimeError('Artifact metadata does not match the requested build')
        site = build(temp / 'site')
        relative = f"downloads/android-{run['databaseId']}"
        download = site / relative
        download.mkdir(parents=True)
        for name in ('AfricanBrowser.apk', 'SHA256SUMS', 'build-info.json'):
            shutil.copy2(apk.parent / name, download / name)
        (download / 'release-notes.txt').write_text(
            f'AfricanBrowser Android ARM64 development build\nSource: {local_sha}\n'
            f'Run: https://github.com/{args.repo}/actions/runs/{run["databaseId"]}\n'
            f'SHA-256: {digest}\nDevelopment signing; device acceptance testing remains required.\n')
        index = site / 'index.html'
        text = index.read_text()
        text, count = re.subn(r'https://github.com/olamidebello/AfricanBrowser/releases/download/[^" ]+/AfricanBrowser.apk',
                             relative + '/AfricanBrowser.apk', text)
        if count != 1:
            raise RuntimeError('Website download anchor changed')
        text = re.sub(r'https://github.com/olamidebello/AfricanBrowser/releases/tag/[^" ]+',
                      relative + '/release-notes.txt', text)
        text, count = re.subn(r'Published October 15, 2026\. APK size: approximately 528 MB\.',
                             f'Build {run["databaseId"]}. APK size: {apk.stat().st_size / 1024**2:.1f} MiB.', text)
        if count != 1:
            raise RuntimeError('Website build status anchor changed')
        text = text.replace('Release notes &amp; checksums', 'Release notes')
        text = text.replace('</div><p class="note">For compatible ARM64',
                            f'<a class="button secondary" href="{relative}/SHA256SUMS">SHA-256 checksums</a></div><p class="note">For compatible ARM64')
        index.write_text(text)
        (site / 'deployment.json').write_text(json.dumps(
            {'source': local_sha, 'run_id': run['databaseId'], 'apk': relative + '/AfricanBrowser.apk',
             'sha256': digest}, indent=2) + '\n')
        site.rename(args.output)
    print((args.output / 'deployment.json').read_text())


if __name__ == '__main__':
    main()
