#!/usr/bin/env python3
"""
Main script for Human-Like TTS Logger for Apple Silicon.
Orchestrates text parsing, TTS synthesis, and logging.
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
import ffmpeg
from parser import TextParser, TextSegment
from tts_engine import TTSEngine
from logger import TTSLogger


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def read_input_text(input_path: str) -> str:
    """
    Read input text from file.
    
    Args:
        input_path: Path to input text file
        
    Returns:
        Text content
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return text


def combine_audio_files(segment_files: list, output_path: str, normalize: bool = True):
    """
    Combine multiple audio files into one using ffmpeg.
    
    Args:
        segment_files: List of paths to audio segment files
        output_path: Path to save combined audio
        normalize: Whether to normalize audio volume
    """
    if not segment_files:
        raise ValueError("No audio files to combine")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Create a temporary file list for ffmpeg concat
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for segment_file in segment_files:
            if os.path.exists(segment_file):
                # Use absolute path and escape single quotes
                abs_path = os.path.abspath(segment_file).replace("'", "'\\''")
                f.write(f"file '{abs_path}'\n")
        temp_list_path = f.name
    
    try:
        # Use ffmpeg to concatenate files
        input_stream = ffmpeg.input(temp_list_path, format='concat', safe=0)
        
        if normalize:
            # Normalize audio using loudnorm filter
            output_stream = ffmpeg.output(
                input_stream,
                output_path,
                acodec='pcm_s16le',
                ar=22050,
                ac=1,
                **{'filter:a': 'loudnorm=I=-16:TP=-1.5:LRA=11'}
            )
        else:
            output_stream = ffmpeg.output(
                input_stream,
                output_path,
                acodec='pcm_s16le',
                ar=22050,
                ac=1
            )
        
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_list_path):
            os.remove(temp_list_path)


def process_text(text: str, config: dict) -> tuple:
    """
    Process text through TTS pipeline.
    
    Args:
        text: Input text to process
        config: Configuration dictionary
        
    Returns:
        Tuple of (list of segment file paths, logger instance)
    """
    # Initialize components
    text_config = config.get('text_processing', {})
    parser = TextParser(
        split_by_headers=text_config.get('split_by_headers', True),
        split_by_punctuation=text_config.get('split_by_punctuation', True),
        min_segment_length=text_config.get('min_segment_length', 50)
    )
    
    paths_config = config.get('paths', {})
    segments_dir = paths_config.get('segments_dir', 'outputs/segments')
    log_file = paths_config.get('log_file', 'outputs/tts_log.txt')
    
    # Ensure segments directory exists
    os.makedirs(segments_dir, exist_ok=True)
    
    # Initialize TTS engine
    tts_engine = TTSEngine(config)
    
    # Initialize logger
    logger = TTSLogger(log_file)
    logger.start()
    
    # Parse text into segments
    logger.log_info("Starting text parsing...")
    segments = parser.parse(text)
    logger.log_info(f"Parsed text into {len(segments)} segments")
    
    segment_files = []
    current_header = None
    
    # Process each segment
    for i, segment in enumerate(segments):
        if segment.is_header:
            # Log header
            logger.log_header(segment.text)
            current_header = segment.text
            continue
        
        # Log segment start
        logger.log_segment_start(segment.text, current_header)
        
        # Generate audio file path
        segment_filename = f"segment_{i:04d}.wav"
        segment_path = os.path.join(segments_dir, segment_filename)
        
        # Synthesize speech
        try:
            voice_config = config.get('voice', {})
            speaker = voice_config.get('speaker', None)
            
            duration = tts_engine.synthesize(
                text=segment.text,
                output_path=segment_path,
                speaker=speaker
            )
            
            segment_files.append(segment_path)
            
            # Log segment end
            logger.log_segment_end(duration, segment_path)
            
            print(f"Generated segment {i+1}/{len(segments)}: {duration:.2f}s")
            
        except Exception as e:
            logger.log_info(f"Error processing segment {i}: {e}")
            print(f"Error processing segment {i}: {e}", file=sys.stderr)
            continue
    
    return segment_files, logger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Human-Like TTS Logger for Apple Silicon',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--text',
        type=str,
        help='Path to input text file (default: input.txt)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--voice',
        type=str,
        help='Override voice/speaker from config'
    )
    
    parser.add_argument(
        '--rate',
        type=float,
        help='Override speech rate/speed from config'
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config(args.config)
        
        # Override voice if provided
        if args.voice:
            if 'voice' not in config:
                config['voice'] = {}
            config['voice']['speaker'] = args.voice
        
        # Override rate if provided
        if args.rate:
            if 'voice' not in config:
                config['voice'] = {}
            config['voice']['speed'] = args.rate
        
        # Determine input text
        if args.text:
            input_path = args.text
        else:
            input_path = config.get('paths', {}).get('input_file', 'input.txt')
        
        # Read input text
        print(f"Reading input from: {input_path}")
        text = read_input_text(input_path)
        print(f"Input text length: {len(text)} characters")
        
        # Process text
        print("\nProcessing text through TTS pipeline...")
        segment_files, logger = process_text(text, config)
        
        if not segment_files:
            print("No audio segments were generated. Exiting.")
            return 1
        
        # Combine audio files
        print(f"\nCombining {len(segment_files)} audio segments...")
        output_config = config.get('output', {})
        normalize = output_config.get('normalize_audio', True)
        final_output = config.get('paths', {}).get('final_output', 'outputs/output.wav')
        
        combine_audio_files(segment_files, final_output, normalize=normalize)
        print(f"Final audio saved to: {final_output}")
        
        # Write log file
        logger.log_info(f"Final audio file: {final_output}")
        logger.write_log()
        log_file = config.get('paths', {}).get('log_file', 'outputs/tts_log.txt')
        print(f"Log file saved to: {log_file}")
        
        # Print summary
        total_duration = logger.get_total_duration()
        print(f"\n{'='*50}")
        print(f"Processing complete!")
        print(f"Total audio duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        print(f"{'='*50}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
        return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

