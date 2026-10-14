# Local Whisper Terminal（廣東話錄音轉文字）

[繁體中文](README.md) · [English](README.en.md)

喺 macOS Terminal 輸入 `transcribe-yue`，揀選錄音或影片，即可用本機的 [whisper.cpp](https://github.com/ggml-org/whisper.cpp) 產生 TXT 謄本和 SRT 字幕。預設語言為廣東話（`yue`），預設模型為多語言 `large-v3`。音訊轉錄在本機完成，不需要 Codex、雲端 API 或帳戶。

## 安裝

1. 先安裝 [Homebrew](https://brew.sh/)。
2. 下載或 clone 此 repository，在 Terminal 進入專案目錄，執行：

   ```bash
   bash install.sh
   ```

安裝器會檢查或安裝 Python、FFmpeg 和 Homebrew 版 `whisper.cpp`，下載並驗證 GGML `large-v3` 模型，再安裝 `transcribe-yue` 指令。模型約佔 2.9 GiB；第一次安裝需要網絡，之後轉錄可以離線進行。[Homebrew 說明](https://formulae.brew.sh/formula/whisper.cpp)確認模型不會隨套件自動下載；[whisper.cpp 模型清單](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md)提供模型大小和校驗碼。

如果已有完整模型，安裝器會校驗並沿用。下載中斷後重新執行 `bash install.sh` 可嘗試續傳。安裝器不會刪除既有檔案；如需更新舊版指令，會先建立備份。

安裝完成後，開一個新的 Terminal 視窗，再輸入：

```bash
transcribe-yue
```

macOS 會彈出選檔視窗。你亦可以直接提供檔案：

```bash
transcribe-yue "錄音.m4a"
```

程式會先用 FFmpeg 轉成 `whisper-cli` 所需的 16 kHz、單聲道、16-bit WAV，再轉錄。WAV 暫存檔會在轉錄後由系統清理；原始錄音不會修改。[whisper.cpp README](https://github.com/ggml-org/whisper.cpp#quick-start)亦說明此 WAV 格式要求。

## 輸出和選項

預設在原始檔案旁邊建立 `<檔名>_transcript.txt` 和 `<檔名>_transcript.srt`。如同名檔案已存在，會加上數字，避免覆蓋。支援檔名包含空格、中文和多個句點。

```bash
transcribe-yue "錄音.m4a" --output-dir "輸出資料夾"
transcribe-yue "錄音.m4a" --cpu
transcribe-yue "錄音.m4a" --language zh
transcribe-yue "錄音.m4a" --model "另一個GGML模型.bin"
transcribe-yue --help
```

`--cpu` 可直接使用 CPU。若預設的 Metal 執行因記憶體分配失敗，程式會自動重試 CPU。`--language zh` 適合想改用一般中文語言提示的情況；廣東話錄音通常維持預設 `yue`。

執行期間會顯示進度百分比；完成後會顯示音訊長度、實際耗時、相對實時速度、CPU 時間及子程序記憶體峰值。記憶體數字不包括 GPU 記憶體；CPU 時間係所有 CPU 核心加總，所以可能大於實際耗時。`0.5x real time` 表示轉錄需約兩倍錄音時間。

## 常見問題

- **找不到 `transcribe-yue`：** 開新的 Terminal 視窗；安裝器會在需要時把預設的指令目錄加入 zsh 的啟動設定。可用 `command -v transcribe-yue` 檢查。
- **沒有選檔視窗：** 只支援 macOS 圖形桌面工作階段；遠端或無圖形環境請在指令後直接提供音訊檔名。
- **模型校驗失敗：** 安裝器不會覆蓋現有模型；先自行檢查或移走受損檔案，再重跑安裝器。
- **Metal 記憶體不足：** 程式會自動改用 CPU；如想一開始就使用 CPU，加 `--cpu`。
- **檔案未能轉錄：** 先用 `ffmpeg -i "錄音.m4a"` 檢查 FFmpeg 能否讀取。沒有音軌的影片不能產生謄本。

## 上載到你自己的 GitHub repository

在 GitHub 建立一個空白 repository 後，在本專案目錄執行：

```bash
git init -b main
git add .
git commit -m "Add local Cantonese transcription workflow"
git remote add origin "https://github.com/你的帳戶/你的repository.git"
git push -u origin main
```

模型、錄音和轉錄結果不應上載；`.gitignore` 已排除常見檔案格式。首次 `git add` 後仍應用 `git status` 檢查將要上載的檔案。

`SKILL.md` 係可選的代理說明檔；只用 Terminal 時完全不需要安裝或啟用任何 AI skill。

## 驗證

在 macOS 並已安裝 FFmpeg 的環境，可執行：

```bash
python3 -m unittest discover -s tests -v
```

測試會使用模擬的 `whisper-cli` 和模型下載，不會轉錄真實錄音或下載大型模型。

## 授權與來源

本專案程式碼採用 MIT License。`whisper.cpp`、FFmpeg 和 GGML 模型分別來自其原專案，模型與第三方工具不包含在此 repository。
