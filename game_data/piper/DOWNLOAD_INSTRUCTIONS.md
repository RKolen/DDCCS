# Piper TTS Setup Instructions

## Required Downloads

### 1. Piper Executable (Windows)

Download from: <https://github.com/rhasspy/piper/releases/latest>

**File to download**: `piper_windows_amd64.zip`

**Installation**:

1. Extract the zip file
2. Copy `piper.exe` to this directory (`backend/piper/`)
3. Verify: You should have `backend/piper/piper.exe`

### 2. Voice Models

#### Voice 1: Alan (Medium Quality) - REQUIRED (default narrator)

**File**: `en_GB-alan-medium.onnx` + `en_GB-alan-medium.onnx.json`
**Download from**: <https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx>
**Config**: <https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json>
**Size**: ~60MB
**Quality**: British male — default story narrator
**Save to**: `game_data/piper/voices/`

#### Voice 2: Amy (Medium Quality) - REQUIRED

**File**: `en_US-amy-medium.onnx` + `en_US-amy-medium.onnx.json`
**Download from**: <https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx>
**Config**: <https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json>
**Size**: ~60MB
**Quality**: Clear, pleasant female voice
**Save to**: `game_data/piper/voices/`

#### Voice 3: Joe / Ryan (optional character voices)

Also commonly used: `en_US-joe-medium`, `en_US-ryan-low` in the same
`game_data/piper/voices/` directory.

## Final Directory Structure

After downloads, you should have:

game_data/piper/
├── voices/
│   ├── en_GB-alan-medium.onnx
│   ├── en_GB-alan-medium.onnx.json
│   ├── en_US-amy-medium.onnx
│   ├── en_US-amy-medium.onnx.json
│   ├── en_US-joe-medium.onnx
│   └── en_US-joe-medium.onnx.json
└── DOWNLOAD_INSTRUCTIONS.md (this file)

## Testing Piper

Once downloaded, test from PowerShell:

```powershell
cd "c:\Users\raymo\Documents\Unity projects\new\backend\piper"
echo "Hello, this is a test." | .\piper.exe --model voices\en_US-amy-medium.onnx --output_file test.wav
```

If successful, you'll have a `test.wav` file with audio.

## Voice Comparison

| Voice           | Quality   | Size | Best For                         |
|-----------------|-----------|------|----------------------------------|
| Amy Medium      | Good      | 28MB | Fast, clear communication        |
| Libritts High   | Excellent | 85MB | Natural, expressive storytelling |

## Troubleshooting

**Problem**: "piper.exe is not recognized"

- Ensure you extracted piper.exe to `backend/piper/` directory
- Check the file is named exactly `piper.exe` (not `piper.exe.exe`)

**Problem**: "Model file not found"

- Verify .onnx files are in `backend/piper/voices/`
- Ensure you downloaded BOTH the .onnx and .onnx.json files
- Check file names match exactly

**Problem**: "Cannot generate audio"

- Test manually with PowerShell command above
- Check Windows Defender didn't block the download
- Ensure you have ~150MB free disk space

## Ready to Use

Once files are in place, restart your backend:

```powershell
# Close backend window and restart via start-chat.bat
```

The TTS functionality will automatically detect available voices!
