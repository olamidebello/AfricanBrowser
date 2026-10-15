import json
import io
import tarfile
from unittest.mock import patch
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_checkpoint import normalize_inputs, save, restore, bounded_compile, extract_entry, compatible_identity


class CheckpointTests(unittest.TestCase):
    def test_real_ninja_reuses_restored_outputs_after_fresh_checkout(self):
        try:
            import ninja
            executable = Path(ninja.BIN_DIR) / 'ninja'
        except ImportError:
            self.skipTest('Install ninja to test real incremental compilation')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'src'
            output = source / 'out/AfricanBrowser'
            output.mkdir(parents=True)
            input_file = source / 'input.txt'
            input_file.write_text('browser build input')
            script = source / 'compile.py'
            script.write_text('from pathlib import Path\nPath("object.bin").write_bytes(Path("../../input.txt").read_bytes())\n')
            (output / 'build.ninja').write_text('rule compile\n  command = ' + sys.executable +
                ' ../../compile.py\nbuild object.bin: compile ../../input.txt ../../compile.py\n')
            normalize_inputs(source)
            subprocess.run([executable, '-C', output], check=True, capture_output=True)
            checkpoint = root / 'checkpoint'
            identity = {'commit': 'test', 'target': 'arm64'}
            save(source, checkpoint, identity)
            shutil.rmtree(output)
            os.utime(input_file, None)
            os.utime(script, None)
            normalize_inputs(source)
            self.assertTrue(restore(source, checkpoint, identity))
            result = subprocess.run([executable, '-C', output], check=True, capture_output=True, text=True)
            self.assertIn('no work to do', result.stdout)
            self.assertEqual((output / 'object.bin').read_text(), 'browser build input')
            with self.assertRaises(RuntimeError):
                restore(source, checkpoint, {'commit': 'different'})
            archive = checkpoint / 'outputs.tar.zst'
            archive.write_bytes(archive.read_bytes() + b'tampered')
            with self.assertRaises(RuntimeError):
                restore(source, checkpoint, identity)

    def test_checkpoint_preserves_internal_links_and_blocks_link_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)
            output = source / 'out/AfricanBrowser'
            output.mkdir(parents=True)
            (output / 'object.bin').write_text('compiled output')
            (source / 'input.txt').write_text('protected input')
            def extract(name, kind, target=''):
                data = io.BytesIO()
                with tarfile.open(fileobj=data, mode='w') as archive:
                    entry = tarfile.TarInfo(name)
                    entry.type = kind
                    entry.linkname = target
                    archive.addfile(entry)
                data.seek(0)
                with tarfile.open(fileobj=data, mode='r') as archive:
                    extract_entry(archive, archive.next(), source)
            extract('out/AfricanBrowser/result.bin', tarfile.SYMTYPE, 'object.bin')
            self.assertEqual((output / 'result.bin').read_text(), 'compiled output')
            extract('out/AfricanBrowser/input-link', tarfile.SYMTYPE, '../../input.txt')
            self.assertEqual((output / 'input-link').read_text(), 'protected input')
            extract('out/AfricanBrowser/source-link', tarfile.SYMTYPE, '../..')
            for name, kind, target in [
                ('out/AfricanBrowser/escape', tarfile.SYMTYPE, '../../../../outside'),
                ('out/AfricanBrowser/absolute', tarfile.SYMTYPE, '/etc/passwd'),
                ('out/AfricanBrowser/source-link/input.txt', tarfile.REGTYPE, ''),
                ('out/AfricanBrowser/../outside', tarfile.REGTYPE, ''),
                ('out/AfricanBrowser/fifo', tarfile.FIFOTYPE, ''),
                ('out/AfricanBrowser/hard', tarfile.LNKTYPE, '../../input.txt'),
                ('out/AfricanBrowser', tarfile.SYMTYPE, '../..')]:
                with self.assertRaises(RuntimeError):
                    extract(name, kind, target)
            self.assertEqual((source / 'input.txt').read_text(), 'protected input')

    def test_legacy_checkpoint_reuse_requires_named_commit_and_only_tool_changes(self):
        old = {'project_commit': 'a' * 40, 'upstream': 'engine', 'gn_args': 'args'}
        new = dict(old, project_commit='b' * 40)
        self.assertFalse(compatible_identity(old, new))
        with patch.dict(os.environ, AFRICANBROWSER_COMPATIBLE_CHECKPOINT_COMMIT='a' * 40):
            with patch('build_checkpoint.subprocess.check_output', return_value='scripts/build_checkpoint.py\n.github/workflows/android-apk.yml\n'):
                self.assertTrue(compatible_identity(old, new))
                self.assertFalse(compatible_identity(old, dict(new, gn_args='changed')))
            with patch('build_checkpoint.subprocess.check_output', return_value='scripts/branding.py\n'):
                self.assertFalse(compatible_identity(old, new))

    def test_timeout_is_incomplete_but_actual_compile_failure_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(bounded_compile([sys.executable, '-c', 'import time;time.sleep(10)'],
                                             folder, dict(os.environ), .1))
            with self.assertRaises(subprocess.CalledProcessError):
                bounded_compile([sys.executable, '-c', 'raise SystemExit(3)'],
                                folder, dict(os.environ), 5)
            self.assertTrue(bounded_compile([sys.executable, '-c', 'pass'],
                                           folder, dict(os.environ), 5))


if __name__ == '__main__':
    unittest.main()
