"""Installer checks with mocked downloads and isolated HOME directories."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"
EXPECTED_HASH = "ad82bf6a9043ceed055076d0fd39f5f186ff8062"


@unittest.skipUnless(sys.platform == "darwin", "macOS installer")
class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="transcribe-yue-install-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.fake_bin = self.root / "fake-bin"
        self.fake_bin.mkdir()
        for name in ("brew", "ffmpeg", "ffprobe", "whisper-cli"):
            self.executable(name, "#!/bin/sh\nexit 0\n")
        self.executable("curl", """#!/usr/bin/env python3
import sys
from pathlib import Path
output = sys.argv[sys.argv.index('--output') + 1]
Path(output).write_bytes(b'fake model')
""")
        self.executable("shasum", """#!/usr/bin/env python3
import os
import sys
print(os.environ.get('FAKE_HASH', 'ad82bf6a9043ceed055076d0fd39f5f186ff8062') + '  ' + sys.argv[-1])
""")

    def executable(self, name, content):
        path = self.fake_bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def install(self, extra_env=None):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["WHISPER_YUE_BIN_DIR"] = str(self.root / "bin")
        env["PATH"] = str(self.fake_bin) + os.pathsep + env.get("PATH", "")
        env.update(extra_env or {})
        return subprocess.run(["bash", str(INSTALLER)], capture_output=True,
                              text=True, env=env, check=False)

    def test_fresh_install_then_rerun_uses_existing_model(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        model = self.home / "whisper-local" / "models" / "ggml-large-v3.bin"
        command = self.root / "bin" / "transcribe-yue"
        self.assertEqual(model.read_bytes(), b"fake model")
        self.assertTrue(command.is_file())
        self.assertTrue(os.access(command, os.X_OK))
        second = self.install()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("download skipped", second.stdout)

    def test_bad_existing_model_is_preserved(self):
        model = self.home / "whisper-local" / "models" / "ggml-large-v3.bin"
        model.parent.mkdir(parents=True)
        model.write_bytes(b"existing data")
        result = self.install({"FAKE_HASH": "bad-checksum"})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(model.read_bytes(), b"existing data")
        self.assertFalse((self.root / "bin" / "transcribe-yue").exists())


if __name__ == "__main__":
    unittest.main()
