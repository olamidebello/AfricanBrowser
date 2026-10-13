"""Bounded Chromium compilation with validated, size-limited Ninja checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile

INPUT_EPOCH = 1577836800
MAX_ARCHIVE_BYTES = 9 * 1024**3


def normalize_inputs(source):
    source = Path(source)
    count = 0
    for directory, folders, files in os.walk(source, followlinks=False):
        folders[:] = [name for name in folders if name != '.git' and
                      not (Path(directory) == source and name == 'out')]
        for name in files:
            path = Path(directory) / name
            if not path.is_symlink():
                os.utime(path, (INPUT_EPOCH, INPUT_EPOCH))
                count += 1
    print(f'Normalized {count} build inputs for incremental compilation.', flush=True)


def bounded_compile(args, source, env, seconds):
    process = subprocess.Popen([str(arg) for arg in args], cwd=source, env=env,
                               start_new_session=True)
    try:
        result = process.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print('Segment limit reached; stopping Ninja to preserve completed work.', flush=True)
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        return False
    if result != 0:
        raise subprocess.CalledProcessError(result, args)
    return True


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(source, checkpoint, identity):
    source, checkpoint = Path(source), Path(checkpoint)
    checkpoint.mkdir(parents=True, exist_ok=True)
    archive = checkpoint / 'outputs.tar.zst'
    temporary = checkpoint / 'outputs.tmp.tar.zst'
    if not (source / 'out/AfricanBrowser/build.ninja').is_file():
        raise RuntimeError('No configured Ninja build exists; refusing an empty checkpoint')
    archive.unlink(missing_ok=True)
    subprocess.run(['tar', '--use-compress-program=zstd -3 -T2', '--hard-dereference',
                    '-cf', str(temporary), '-C', str(source), 'out/AfricanBrowser'], check=True)
    size = temporary.stat().st_size
    if size > MAX_ARCHIVE_BYTES:
        temporary.unlink()
        raise RuntimeError('Checkpoint exceeds 9 GiB; use a larger persistent build worker')
    temporary.replace(archive)
    metadata = {'schema': 1, 'identity': identity, 'source_path': str(source.resolve()),
                'archive_sha256': digest(archive), 'archive_bytes': size}
    (checkpoint / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Saved completed build work: {size / 1024**3:.2f} GiB checkpoint.', flush=True)


def restore(source, checkpoint, identity):
    source, checkpoint = Path(source), Path(checkpoint)
    metadata_path = checkpoint / 'metadata.json'
    archive = checkpoint / 'outputs.tar.zst'
    if not metadata_path.exists() and not archive.exists():
        print('No prior checkpoint; starting a clean build.', flush=True)
        return False
    metadata = json.loads(metadata_path.read_text())
    if metadata.get('schema') != 1 or metadata.get('identity') != identity:
        raise RuntimeError('Checkpoint identity does not match this pinned build')
    if metadata.get('source_path') != str(source.resolve()):
        raise RuntimeError('Ninja checkpoints require the same absolute source path')
    if archive.stat().st_size > MAX_ARCHIVE_BYTES or digest(archive) != metadata.get('archive_sha256'):
        raise RuntimeError('Checkpoint failed its size or integrity check')
    process = subprocess.Popen(['zstd', '-dc', str(archive)], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode='r|') as tar:
            for entry in tar:
                path = Path(entry.name)
                if path.is_absolute() or '..' in path.parts or path.parts[:2] != ('out', 'AfricanBrowser'):
                    raise RuntimeError('Checkpoint contains an unexpected path')
                if not (entry.isfile() or entry.isdir()):
                    raise RuntimeError('Checkpoint links or special files are not allowed')
                tar.extract(entry, path=source, filter='data')
    finally:
        process.stdout.close()
        code = process.wait()
    if code != 0:
        raise RuntimeError('Cannot decompress checkpoint')
    print('Restored Ninja outputs and dependency state.', flush=True)
    return True
