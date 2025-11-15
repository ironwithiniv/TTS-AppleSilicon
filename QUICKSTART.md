# Quick Start Guide

## Installation Steps

1. **Install ffmpeg:**
   ```bash
   brew install ffmpeg
   ```

2. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python3 main.py
   ```

## First Run

On the first run, Coqui TTS will download the model (this may take several minutes). The application will:

1. Parse `input.txt`
2. Generate audio segments
3. Combine them into `outputs/output.wav`
4. Create a log file at `outputs/tts_log.txt`

## Example Output

After running, you'll find:
- `outputs/output.wav` - Final audio file
- `outputs/tts_log.txt` - Detailed log with timestamps
- `outputs/segments/` - Individual audio segments

## Customization

Edit `config.yaml` to:
- Change TTS model
- Adjust voice settings
- Modify output paths
- Enable/disable features

## Troubleshooting

- **Model download fails**: Check internet connection and disk space
- **MPS not available**: Application will use CPU automatically
- **FFmpeg errors**: Ensure ffmpeg is installed: `brew install ffmpeg`

