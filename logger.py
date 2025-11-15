"""
Logging module for TTS operations with timestamps and duration tracking.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class LogEntry:
    """Represents a single log entry."""
    timestamp: datetime
    message: str
    duration_seconds: Optional[float] = None
    segment_path: Optional[str] = None


class TTSLogger:
    """Logger for TTS operations with timestamp tracking."""
    
    def __init__(self, log_file_path: str):
        """
        Initialize the logger.
        
        Args:
            log_file_path: Path to the log file
        """
        self.log_file_path = log_file_path
        self.entries: List[LogEntry] = []
        self.start_time = None
        self.current_time = None
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def start(self):
        """Start logging session."""
        self.start_time = datetime.now()
        self.current_time = self.start_time
        self.entries = []
    
    def log_header(self, header: str):
        """
        Log a header entry.
        
        Args:
            header: Header text to log
        """
        if not self.start_time:
            self.start()
        
        self.current_time = datetime.now()
        entry = LogEntry(
            timestamp=self.current_time,
            message=f"# {header}"
        )
        self.entries.append(entry)
    
    def log_segment_start(self, segment_text: str, header: Optional[str] = None):
        """
        Log the start of a segment.
        
        Args:
            segment_text: Text being synthesized
            header: Optional header for this segment
        """
        if not self.start_time:
            self.start()
        
        self.current_time = datetime.now()
        message = f"Segment started"
        if header:
            message += f" (under header: {header})"
        
        entry = LogEntry(
            timestamp=self.current_time,
            message=message
        )
        self.entries.append(entry)
    
    def log_segment_end(self, duration_seconds: float, segment_path: Optional[str] = None):
        """
        Log the end of a segment with duration.
        
        Args:
            duration_seconds: Duration of the segment in seconds
            segment_path: Path to the generated audio file
        """
        if not self.start_time:
            self.start()
        
        self.current_time = datetime.now()
        message = f"Segment finished (duration: {duration_seconds:.2f}s)"
        
        entry = LogEntry(
            timestamp=self.current_time,
            message=message,
            duration_seconds=duration_seconds,
            segment_path=segment_path
        )
        self.entries.append(entry)
    
    def log_info(self, message: str):
        """
        Log an informational message.
        
        Args:
            message: Message to log
        """
        if not self.start_time:
            self.start()
        
        self.current_time = datetime.now()
        entry = LogEntry(
            timestamp=self.current_time,
            message=message
        )
        self.entries.append(entry)
    
    def format_timestamp(self, dt: datetime) -> str:
        """
        Format datetime as [HH:MM:SS].
        
        Args:
            dt: Datetime object
            
        Returns:
            Formatted timestamp string
        """
        if not self.start_time:
            return "[00:00:00]"
        
        delta = dt - self.start_time
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
    
    def write_log(self):
        """Write all log entries to file."""
        if not self.entries:
            return
        
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("TTS Generation Log\n")
            f.write("=" * 50 + "\n\n")
            
            total_duration = 0.0
            
            for entry in self.entries:
                timestamp_str = self.format_timestamp(entry.timestamp)
                f.write(f"{timestamp_str} {entry.message}\n")
                
                if entry.duration_seconds:
                    total_duration += entry.duration_seconds
                
                if entry.segment_path:
                    f.write(f"  File: {entry.segment_path}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)\n")
            
            if self.start_time and self.current_time:
                total_time = (self.current_time - self.start_time).total_seconds()
                f.write(f"Total processing time: {total_time:.2f} seconds\n")
    
    def get_total_duration(self) -> float:
        """
        Calculate total duration of all segments.
        
        Returns:
            Total duration in seconds
        """
        return sum(entry.duration_seconds for entry in self.entries if entry.duration_seconds)

