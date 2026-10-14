#!/usr/bin/env bash
set -euo pipefail

# Standalone macOS installer. No Codex account, Python packages, or cloud API.
readonly PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BIN_DIR="${WHISPER_YUE_BIN_DIR:-$HOME/bin}"
readonly MODEL_DIR="$HOME/whisper-local/models"
readonly MODEL_FILE="$MODEL_DIR/ggml-large-v3.bin"
readonly MODEL_PART="$MODEL_FILE.part"
readonly MODEL_SHA1="ad82bf6a9043ceed055076d0fd39f5f186ff8062"
readonly MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin"

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

model_sha1() {
  shasum -a 1 "$1" | awk '{print $1}'
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "This installer supports macOS."
fi

if ! command -v brew >/dev/null 2>&1; then
  fail "Homebrew is required. Install it from https://brew.sh/ and rerun this script."
fi

if ! command -v python3 >/dev/null 2>&1 ||
   ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
  brew install python
fi
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  brew install ffmpeg
fi
if ! command -v whisper-cli >/dev/null 2>&1; then
  brew install whisper.cpp
fi

for tool in python3 ffmpeg ffprobe whisper-cli curl shasum; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool is unavailable after installation. Check your PATH."
done
python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' ||
  fail "Python 3.8 or newer is required. Check which python3 is first on your PATH."

mkdir -p "$MODEL_DIR"
if [[ -f "$MODEL_FILE" ]]; then
  printf 'Checking existing GGML model...\n'
  [[ "$(model_sha1 "$MODEL_FILE")" == "$MODEL_SHA1" ]] ||
    fail "Existing model failed its checksum. Move it aside and rerun the installer."
  printf 'Model verified; download skipped.\n'
else
  printf 'Downloading large-v3 GGML model (about 2.9 GiB)...\n'
  curl --fail --location --retry 3 --continue-at - --output "$MODEL_PART" "$MODEL_URL" ||
    fail "Model download failed. Rerun the installer to resume it."
  [[ "$(model_sha1 "$MODEL_PART")" == "$MODEL_SHA1" ]] ||
    fail "Downloaded model failed its checksum. Keep the .part file for inspection."
  mv "$MODEL_PART" "$MODEL_FILE"
  printf 'Model downloaded and verified.\n'
fi

mkdir -p "$BIN_DIR"
destination="$BIN_DIR/transcribe-yue"
if [[ -L "$destination" ]]; then
  fail "The command location is a symbolic link. Choose another WHISPER_YUE_BIN_DIR."
fi
if [[ -f "$destination" ]] && ! cmp -s "$PROJECT_DIR/bin/transcribe-yue" "$destination"; then
  backup="$destination.backup.$(date +%Y%m%d-%H%M%S)"
  number=2
  while [[ -e "$backup" ]]; do
    backup="$destination.backup.$(date +%Y%m%d-%H%M%S).$number"
    number=$((number + 1))
  done
  cp -p "$destination" "$backup"
  printf 'Previous command backed up: %s\n' "$backup"
fi
install -m 755 "$PROJECT_DIR/bin/transcribe-yue" "$destination"

if [[ "$BIN_DIR" == "$HOME/bin" ]]; then
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *)
      profile="$HOME/.zprofile"
      if [[ ! -f "$profile" ]] || ! grep -Fq '# local-whisper-terminal PATH' "$profile"; then
        printf '\n# local-whisper-terminal PATH\nexport PATH="$HOME/bin:$PATH"\n' >> "$profile"
      fi
      printf 'Open a new Terminal window to pick up the command on PATH.\n'
      ;;
  esac
fi

printf 'Installed: %s\n' "$destination"
printf 'Run: transcribe-yue\n'
