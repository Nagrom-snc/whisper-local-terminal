---
name: local-whisper-terminal
description: Set up or use the standalone macOS Terminal command for local Cantonese transcription with whisper.cpp, including a file picker and TXT/SRT output. Use when the user wants this workflow without an AI service.
---

# Local Whisper Terminal

The executable workflow is independent of this skill. Read `README.md` (Traditional Chinese) or `README.en.md` (English) for installation, options, output, and limitations. The repository's `install.sh` handles dependencies and the GGML model. `bin/transcribe-yue` is the command users run after installation.

When helping with this workflow:

- Keep transcription local. Do not send audio to external services.
- Use the user's provided audio file, or let the Terminal command open the macOS picker when no file is specified.
- Preserve existing recordings, models, transcripts, and command backups.
- Verify output TXT and SRT files and report the paths to the user when carrying out a transcription.
- Follow the user's preference to operate directly from Terminal; this skill is optional and does not need to be installed for CLI use.
