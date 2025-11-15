# Human-Like TTS Logger for Apple Silicon

A console Python application for natural text-to-speech synthesis with comprehensive logging capabilities, optimized for Apple Silicon (M1/M2) Macs.

## Features

- 🎙️ Natural-sounding TTS synthesis (English)
- 📝 Automatic text segmentation by headers and punctuation
- ⏱️ Detailed timestamp logging for each segment
- 🍎 Optimized for Apple Silicon with Metal Performance Shaders (MPS)
- 🔧 Support for multiple TTS engines (Coqui TTS local, ElevenLabs cloud)
- 🔊 Audio normalization and concatenation
- 📊 Comprehensive log files with duration tracking

## Requirements

- macOS 13+ (Ventura/Sonoma)
- Python 3.10 or 3.11
- Homebrew (for ffmpeg installation)
- Apple Silicon Mac (M1/M2) recommended for best performance

## Installation

1. **Install ffmpeg via Homebrew:**
   ```bash
   brew install ffmpeg
   ```

2. **Clone or navigate to the project directory:**
   ```bash
   cd TTS-AppleSilicon
   ```

3. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.yaml` to customize settings:

- **TTS Engine**: Choose between `coqui` (local) or `elevenlabs` (cloud API)
- **Model/Voice**: Select TTS model and voice settings
- **Output Format**: Choose WAV or MP3
- **Paths**: Configure input/output directories

### Coqui TTS (Local)

The default configuration uses Coqui TTS for local processing. The first run will download the model automatically.

### ElevenLabs (Cloud)

To use ElevenLabs, add your API key to `config.yaml`:

```yaml
tts:
  engine: "elevenlabs"
  elevenlabs:
    api_key: "your-api-key-here"
```

## Usage

### Basic Usage

Process a text file:

```bash
python3 main.py --text input.txt
```

Or use the default input file:

```bash
python3 main.py
```

### Command-Line Options

```bash
python3 main.py [OPTIONS]

Options:
  --text PATH     Path to input text file (default: input.txt)
  --config PATH   Path to configuration file (default: config.yaml)
  --voice NAME    Override voice/speaker from config
  --rate FLOAT    Override speech rate/speed from config
```

### Example

```bash
python3 main.py --text my_document.txt --voice "speaker_name"
```

## Output

The application generates:

1. **Audio File**: `outputs/output.wav` - Combined audio file with all segments
2. **Log File**: `outputs/tts_log.txt` - Detailed log with timestamps and durations
3. **Segments**: `outputs/segments/` - Individual audio files for each segment

### Log Format

The log file contains:

```
TTS Generation Log
==================================================

[00:00:00] # Introduction to Text-to-Speech
[00:00:05] Segment started
[00:00:18] Segment finished (duration: 13.00s)
  File: outputs/segments/segment_0001.wav
[00:00:18] # Features
...

==================================================
Total duration: 45.23 seconds (0.75 minutes)
Total processing time: 120.45 seconds
```

## Project Structure

```
TTS-AppleSilicon/
├── main.py                # Main orchestration script
├── tts_engine.py          # TTS synthesis engine
├── parser.py              # Text parsing and segmentation
├── logger.py              # Timestamp logging
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── input.txt              # Example input file
├── README.md              # This file
└── outputs/               # Generated files
    ├── segments/          # Individual audio segments
    ├── output.wav         # Final combined audio
    └── tts_log.txt        # Generation log
```

## Text Format

The application supports Markdown-style headers:

```markdown
# Main Title

This is the first paragraph. It will be synthesized as a separate segment.

## Subsection

This is another paragraph under the subsection.
```

Headers are automatically detected and logged separately.

## Troubleshooting

### MPS Device Not Available

If you see warnings about MPS not being available, the application will automatically fall back to CPU processing. Ensure you're running on macOS 13+ with Apple Silicon.

### Model Download Issues

On first run, Coqui TTS will download the model. This may take several minutes depending on your internet connection. Ensure you have sufficient disk space (models can be several GB).

### FFmpeg Errors

Ensure ffmpeg is installed and accessible:

```bash
which ffmpeg
brew install ffmpeg  # If not found
```

### Audio Quality Issues

Adjust the sample rate in `config.yaml`:

```yaml
tts:
  coqui:
    sample_rate: 22050  # Try 44100 for higher quality
```

## Performance Tips

- Use Coqui TTS for local processing (no API costs)
- Apple Silicon Macs provide significant speedup with MPS
- Larger models provide better quality but slower synthesis
- Consider splitting very long texts into multiple files

## License

This project is provided as-is for educational and personal use.

## Contributing

Feel free to submit issues or pull requests for improvements.

