"""Windows launcher regression; isolated PATH/build, no npm or hosted calls."""
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(sys.platform == 'win32', 'Windows PowerShell launcher')
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix='SIMULATED launcher ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        scripts = self.root / 'scripts'
        scripts.mkdir()
        source = Path(__file__).resolve().parents[1] / 'scripts/start-portfolio-demo.ps1'
        self.script = scripts / source.name
        shutil.copyfile(source, self.script)
        self.dist = self.root / 'portfolio-ui/dist'
        self.dist.mkdir(parents=True)
        (self.dist / 'index.html').write_text('SIMULATED', encoding='utf-8')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        # No Node/npm or real Python executable on this controlled PATH.
        self.env = {**os.environ, 'PATH': str(self.bin)}
        self.shell = str(Path(os.environ['SystemRoot']) /
                         'System32/WindowsPowerShell/v1.0/powershell.exe')

    def python_stub(self, version='3.11.9', probe_exit=0, server_exit=37):
        (self.bin / 'python.cmd').write_text(
            '@echo off\nif "%~1"=="-c" (\n'
            f'echo {version}\nexit /b {probe_exit}\n)\n'
            f'echo SERVER-FAILURE-SENTINEL 1>&2\nexit /b {server_exit}\n',
            encoding='ascii')

    def run_launcher(self):
        return subprocess.run(
            [self.shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(self.script)],
            cwd=self.root.parent, env=self.env, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=20)

    def test_python_missing(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Python was not found on PATH', result.stderr)

    def test_python_old_or_broken(self):
        for version, code in [('3.10.9', 1), ('Store alias failed', 9009)]:
            with self.subTest(version=version):
                self.python_stub(version, code)
                result = self.run_launcher()
                self.assertEqual(result.returncode, 1)
                self.assertIn('Python >=3.11 is required', result.stderr)
                self.assertIn(version, result.stderr)

    def test_missing_build(self):
        self.python_stub()
        (self.dist / 'index.html').unlink()
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn('React build missing', result.stderr)
        self.assertIn('npm run build', result.stderr)
        self.assertNotIn('SERVER-FAILURE-SENTINEL', result.stderr)

    def test_occupied_port(self):
        self.python_stub()
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 4190))
            listener.listen()
            result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Cannot bind 127.0.0.1:4190', result.stderr)
        self.assertNotIn('SERVER-FAILURE-SENTINEL', result.stderr)

    def test_outside_directory_no_node_native_failure_status(self):
        self.python_stub(server_exit=37)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 37)
        self.assertIn('SERVER-FAILURE-SENTINEL', result.stderr)
        self.assertIn('code 37', result.stderr)
        self.assertIn('http://127.0.0.1:4190/', result.stdout)
        self.assertNotIn('Demo preflight failed', result.stderr)


if __name__ == '__main__':
    unittest.main()
