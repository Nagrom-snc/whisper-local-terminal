# Local Whisper Terminal (Cantonese speech to text)

[繁體中文](README.md) · [English](README.en.md)

Run `transcribe-yue` in macOS Terminal, choose an audio or video file, and generate a TXT transcript and SRT subtitles locally with [whisper.cpp](https://github.com/ggml-org/whisper.cpp). The default language is Cantonese (`yue`), and the default model is multilingual `large-v3`. Transcription runs on your Mac without Codex, a cloud API, or an account.

## Installation

1. Install [Homebrew](https://brew.sh/).
2. Download or clone this repository, enter its directory in Terminal, and run:

   ```bash
   bash install.sh
   ```

The installer checks for or installs Python, FFmpeg, and the Homebrew version of `whisper.cpp`. It then downloads and verifies the GGML `large-v3` model and installs the `transcribe-yue` command. The model uses about 2.9 GiB of disk space. The first installation needs an internet connection; transcription can run offline afterward. The [Homebrew formula](https://formulae.brew.sh/formula/whisper.cpp) does not include model files, and the [whisper.cpp model list](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md) provides model sizes and checksums.

If a complete model is already present, the installer verifies and reuses it. If a download is interrupted, rerun `bash install.sh` to attempt to resume it. The installer does not delete existing files; it makes a backup before replacing an older copy of the command.

After installation, open a new Terminal window and run:

```bash
transcribe-yue
```

A macOS file picker will appear. You can also pass the file directly:

```bash
transcribe-yue "recording.m4a"
```

Before transcription, FFmpeg converts the input to the 16 kHz, mono, 16-bit WAV format expected by `whisper-cli`. The temporary WAV is cleaned up afterward, and the original recording is left unchanged. The [whisper.cpp README](https://github.com/ggml-org/whisper.cpp#quick-start) documents this WAV requirement.

## Output and options

By default, the command writes `<filename>_transcript.txt` and `<filename>_transcript.srt` beside the original file. If those names are already taken, it adds a number rather than overwriting them. File names with spaces, Chinese characters, and multiple periods are supported.

```bash
transcribe-yue "recording.m4a" --output-dir "output-folder"
transcribe-yue "recording.m4a" --cpu
transcribe-yue "recording.m4a" --language zh
transcribe-yue "recording.m4a" --model "another-ggml-model.bin"
transcribe-yue --help
```

Use `--cpu` to start directly on the CPU. If Metal cannot allocate enough memory, the command automatically retries on the CPU. `--language zh` changes the language hint to general Chinese; for Cantonese recordings, the default `yue` is usually appropriate.

The Terminal displays progress percentages while transcribing. When it finishes, it reports the audio duration, elapsed time, speed relative to real time, total CPU time, and peak child-process RAM. The RAM figure does not include GPU memory. CPU time adds usage across CPU cores, so it can exceed elapsed time. A speed of `0.5x real time` means transcription took about twice the recording's duration.

## Troubleshooting

- **`transcribe-yue` is not found:** Open a new Terminal window. When necessary, the installer adds the default command directory to zsh's startup configuration. Check with `command -v transcribe-yue`.
- **No file picker appears:** The picker requires a macOS graphical desktop session. In a remote or headless session, pass the audio file name to the command.
- **The model checksum fails:** The installer leaves the existing model untouched. Inspect or move the damaged file yourself, then rerun the installer.
- **Metal runs out of memory:** The command retries on the CPU. Add `--cpu` to use the CPU from the start.
- **A file cannot be transcribed:** Try `ffmpeg -i "recording.m4a"` to check whether FFmpeg can read it. A video without an audio track cannot produce a transcript.

## Upload to your own GitHub repository

Create an empty repository on GitHub, then run these commands from this project's directory:

```bash
git init -b main
git add .
git commit -m "Add local Cantonese transcription workflow"
git remote add origin "https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git"
git push -u origin main
```

Do not upload models, recordings, or transcripts. `.gitignore` excludes common formats, but check `git status` after the first `git add` to review what will be uploaded.

`SKILL.md` is optional guidance for AI agents. Terminal use does not require installing or enabling an AI skill.

## Verification

On macOS with FFmpeg installed, run:

```bash
python3 -m unittest discover -s tests -v
```

The tests use a simulated `whisper-cli` and model download. They do not transcribe real audio or download the large model.

## License and sources

This project's code is available under the MIT License. `whisper.cpp`, FFmpeg, and the GGML model come from their respective projects; third-party tools and model files are not included in this repository.
