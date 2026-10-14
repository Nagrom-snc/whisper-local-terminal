"""Integration checks for file selection, output naming, and CPU fallback."""

import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock


COMMAND = Path(__file__).resolve().parents[1] / "bin" / "transcribe-yue"


@unittest.skipUnless(sys.platform == "darwin" and shutil.which("ffmpeg"),
                     "requires macOS and ffmpeg")
class TranscribeCLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="transcribe-yue-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin_dir = self.root / "fake-bin"
        self.bin_dir.mkdir()
        self.model = self.root / "model.bin"
        self.model.write_bytes(b"fake model")
        fake_whisper = self.bin_dir / "whisper-cli"
        fake_whisper.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "if os.environ.get('FAKE_METAL_FAIL') == '1' and '--no-gpu' not in args:\n"
            "    print('ggml_metal_buffer_init: error: failed to allocate Metal buffer')\n"
            "    sys.exit(1)\n"
            "prefix = args[args.index('--output-file') + 1]\n"
            "print('whisper_print_progress_callback: progress =  50%')\n"
            "print('whisper_print_progress_callback: progress = 100%')\n"
            "if os.environ.get('FAKE_INJECT_LINK_PATH'):\n"
            "    Path(os.environ['FAKE_INJECT_LINK_PATH']).symlink_to(os.environ['FAKE_INJECT_LINK_TARGET'])\n"
            "Path(prefix + '.txt').write_text('Test transcript.\\n', encoding='utf-8')\n"
            "if os.environ.get('FAKE_FAIL_AFTER_TXT') == '1':\n"
            "    sys.exit(7)\n"
            "Path(prefix + '.srt').write_text('1\\n00:00:00,000 --> 00:00:01,000\\nTest transcript.\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_whisper.chmod(0o755)
        fake_osascript = self.bin_dir / "osascript"
        fake_osascript.write_text("#!/bin/sh\nprintf '%s\\n' \"$FAKE_AUDIO_PATH\"\n",
                                    encoding="utf-8")
        fake_osascript.chmod(0o755)

    def audio(self, name):
        path = self.root / name
        with wave.open(str(path), "wb") as file:
            file.setnchannels(1)
            file.setsampwidth(2)
            file.setframerate(16000)
            file.writeframes(b"\x00\x00" * 16000)
        return path

    def run_command(self, *args, extra_env=None):
        env = os.environ.copy()
        env["PATH"] = str(self.bin_dir) + os.pathsep + env.get("PATH", "")
        env.update(extra_env or {})
        return subprocess.run([sys.executable, str(COMMAND), *map(str, args)],
                              text=True, capture_output=True, env=env, check=False)

    def test_progress_outputs_and_numbered_names_with_multiple_dots(self):
        audio = self.audio("meeting.final.wav")
        options = (audio, "--model", self.model)
        first = self.run_command(*options, extra_env={"FAKE_METAL_FAIL": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("Progress: 50%", first.stdout)
        self.assertIn("Backend: CPU", first.stdout)
        self.assertIn("Speed:", first.stdout)
        self.assertTrue((self.root / "meeting.final_transcript.txt").is_file())
        self.assertTrue((self.root / "meeting.final_transcript.srt").is_file())
        second = self.run_command(*options)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.root / "meeting.final_transcript_2.txt").is_file())
        self.assertEqual((self.root / "meeting.final_transcript.txt").read_text(),
                         "Test transcript.\n")
        cpu = self.run_command(*options, "--cpu")
        self.assertEqual(cpu.returncode, 0, cpu.stderr)
        self.assertIn("Backend: CPU", cpu.stdout)

    def test_picker_preserves_trailing_space_in_filename(self):
        audio = self.audio("voice.wav ")
        result = self.run_command("--model", self.model,
                                  extra_env={"FAKE_AUDIO_PATH": str(audio)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "voice_transcript.txt").is_file())

    def test_dangling_srt_symlink_does_not_redirect_output(self):
        audio = self.audio("shared.wav")
        target = self.root / "outside.srt"
        (self.root / "shared_transcript.srt").symlink_to(target)

        result = self.run_command(audio, "--model", self.model)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertTrue((self.root / "shared_transcript_2.txt").is_file())
        self.assertTrue((self.root / "shared_transcript_2.srt").is_file())

    def test_link_added_during_transcription_does_not_redirect_output(self):
        audio = self.audio("meeting.wav")
        target = self.root / "outside.txt"
        link = self.root / "meeting_transcript.txt"

        result = self.run_command(
            audio, "--model", self.model,
            extra_env={"FAKE_INJECT_LINK_PATH": str(link),
                       "FAKE_INJECT_LINK_TARGET": str(target)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertTrue((self.root / "meeting_transcript_2.txt").is_file())
        self.assertTrue((self.root / "meeting_transcript_2.srt").is_file())

    def test_link_raced_after_name_check_is_rejected_at_open(self):
        publish_outputs = runpy.run_path(str(COMMAND), run_name="test")["publish_outputs"]
        staging = self.root / "staging"
        staging.mkdir()
        staged_prefix = staging / "transcript"
        (staging / "transcript.txt").write_text("Private TXT", encoding="utf-8")
        (staging / "transcript.srt").write_text("Private SRT", encoding="utf-8")
        output_dir = self.root / "output"
        output_dir.mkdir()
        target = self.root / "outside.txt"
        original_open = os.open
        injected = False
        directory_fd = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)

        def race_open(path, flags, *args, **kwargs):
            nonlocal injected
            if path == "race_transcript.txt" and not injected:
                (output_dir / path).symlink_to(target)
                injected = True
            return original_open(path, flags, *args, **kwargs)

        try:
            with mock.patch("os.open", side_effect=race_open):
                txt, srt = publish_outputs(staged_prefix, output_dir, "race", directory_fd)
        finally:
            os.close(directory_fd)

        self.assertTrue(injected)
        self.assertFalse(target.exists())
        self.assertEqual(txt.name, "race_transcript_2.txt")
        self.assertEqual(srt.name, "race_transcript_2.srt")
        self.assertEqual(txt.read_text(encoding="utf-8"), "Private TXT")
        self.assertEqual(srt.read_text(encoding="utf-8"), "Private SRT")

    def test_output_directory_replacement_cannot_redirect_publication(self):
        publish_outputs = runpy.run_path(str(COMMAND), run_name="test")["publish_outputs"]
        staging = self.root / "staging"
        staging.mkdir()
        staged_prefix = staging / "transcript"
        (staging / "transcript.txt").write_text("Private TXT", encoding="utf-8")
        (staging / "transcript.srt").write_text("Private SRT", encoding="utf-8")
        output_dir = self.root / "output"
        output_dir.mkdir()
        directory_fd = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)
        original_dir = self.root / "original-output"
        output_dir.rename(original_dir)
        output_dir.mkdir()

        try:
            publish_outputs(staged_prefix, output_dir, "race", directory_fd)
        finally:
            os.close(directory_fd)

        self.assertTrue((original_dir / "race_transcript.txt").is_file())
        self.assertTrue((original_dir / "race_transcript.srt").is_file())
        self.assertFalse((output_dir / "race_transcript.txt").exists())
        self.assertFalse((output_dir / "race_transcript.srt").exists())

    def test_srt_collision_during_publication_preserves_existing_file(self):
        publish_outputs = runpy.run_path(str(COMMAND), run_name="test")["publish_outputs"]
        staging = self.root / "staging"
        staging.mkdir()
        staged_prefix = staging / "transcript"
        (staging / "transcript.txt").write_text("Private TXT", encoding="utf-8")
        (staging / "transcript.srt").write_text("Private SRT", encoding="utf-8")
        output_dir = self.root / "output"
        output_dir.mkdir()
        existing = output_dir / "race_transcript.srt"
        original_open = os.open
        directory_fd = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)

        def race_open(path, flags, *args, **kwargs):
            if path == existing.name and not existing.exists():
                existing.write_text("Keep me", encoding="utf-8")
            return original_open(path, flags, *args, **kwargs)

        try:
            with mock.patch("os.open", side_effect=race_open):
                with self.assertRaisesRegex(OSError, "TXT was kept"):
                    publish_outputs(staged_prefix, output_dir, "race", directory_fd)
        finally:
            os.close(directory_fd)

        self.assertEqual(existing.read_text(encoding="utf-8"), "Keep me")
        self.assertEqual((output_dir / "race_transcript.txt").read_text(encoding="utf-8"),
                         "Private TXT")

    def test_output_directory_and_existing_srt_get_numbered(self):
        audio = self.audio("interview.wav")
        output_dir = self.root / "results"
        output_dir.mkdir()
        existing = output_dir / "interview_transcript.srt"
        existing.write_text("Keep me", encoding="utf-8")

        result = self.run_command(audio, "--model", self.model,
                                  "--output-dir", output_dir)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(existing.read_text(encoding="utf-8"), "Keep me")
        self.assertTrue((output_dir / "interview_transcript_2.txt").is_file())
        self.assertTrue((output_dir / "interview_transcript_2.srt").is_file())

    def test_failed_transcription_does_not_publish_partial_output(self):
        audio = self.audio("failed.wav")

        result = self.run_command(
            audio, "--model", self.model,
            extra_env={"FAKE_FAIL_AFTER_TXT": "1"},
        )

        self.assertEqual(result.returncode, 7)
        self.assertFalse((self.root / "failed_transcript.txt").exists())
        self.assertFalse((self.root / "failed_transcript.srt").exists())


if __name__ == "__main__":
    unittest.main()
