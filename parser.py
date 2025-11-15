"""
Text parser module for extracting headers and splitting text into segments.
Handles Markdown-style headers and punctuation-based splitting.
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class TextSegment:
    """Represents a text segment with optional header."""
    text: str
    header: str = None
    is_header: bool = False


class TextParser:
    """Parser for splitting text into segments based on headers and punctuation."""
    
    def __init__(self, split_by_headers: bool = True, 
                 split_by_punctuation: bool = True,
                 min_segment_length: int = 50):
        """
        Initialize the text parser.
        
        Args:
            split_by_headers: Whether to split text by Markdown headers
            split_by_punctuation: Whether to split by sentence-ending punctuation
            min_segment_length: Minimum length of a segment in characters
        """
        self.split_by_headers = split_by_headers
        self.split_by_punctuation = split_by_punctuation
        self.min_segment_length = min_segment_length
        
        # Pattern for Markdown headers (# Header, ## Header, etc.)
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        # Pattern for sentence-ending punctuation
        self.sentence_end_pattern = re.compile(r'([.!?]+)\s+')
    
    def parse(self, text: str) -> List[TextSegment]:
        """
        Parse text into segments.
        
        Args:
            text: Input text to parse
            
        Returns:
            List of TextSegment objects
        """
        if not text.strip():
            return []
        
        segments = []
        
        if self.split_by_headers:
            segments = self._split_by_headers(text)
        else:
            # If not splitting by headers, treat entire text as one segment
            segments = [TextSegment(text=text.strip())]
        
        # Further split by punctuation if enabled
        if self.split_by_punctuation:
            segments = self._split_by_punctuation(segments)
        
        # Filter out segments that are too short
        segments = [s for s in segments if len(s.text.strip()) >= self.min_segment_length]
        
        return segments
    
    def _split_by_headers(self, text: str) -> List[TextSegment]:
        """
        Split text by Markdown headers.
        
        Args:
            text: Input text
            
        Returns:
            List of TextSegment objects with headers identified
        """
        segments = []
        lines = text.split('\n')
        
        current_header = None
        current_text = []
        
        for line in lines:
            # Check if line is a header
            header_match = self.header_pattern.match(line.strip())
            
            if header_match:
                # Save previous segment if it has content
                if current_text:
                    segment_text = '\n'.join(current_text).strip()
                    if segment_text:
                        segments.append(TextSegment(
                            text=segment_text,
                            header=current_header,
                            is_header=False
                        ))
                
                # Start new segment with header
                header_text = header_match.group(2).strip()
                segments.append(TextSegment(
                    text=header_text,
                    header=header_text,
                    is_header=True
                ))
                
                current_header = header_text
                current_text = []
            else:
                # Add line to current segment
                if line.strip():
                    current_text.append(line)
        
        # Add remaining text
        if current_text:
            segment_text = '\n'.join(current_text).strip()
            if segment_text:
                segments.append(TextSegment(
                    text=segment_text,
                    header=current_header,
                    is_header=False
                ))
        
        return segments
    
    def _split_by_punctuation(self, segments: List[TextSegment]) -> List[TextSegment]:
        """
        Further split segments by sentence-ending punctuation.
        
        Args:
            segments: List of TextSegment objects
            
        Returns:
            List of TextSegment objects split by punctuation
        """
        result = []
        
        for segment in segments:
            # Don't split header segments
            if segment.is_header:
                result.append(segment)
                continue
            
            # Split text by sentence endings (including punctuation)
            # Pattern: text ending with . ! or ? followed by whitespace or end of string
            sentences = re.split(r'([.!?]+)\s+', segment.text)
            
            # Reconstruct sentences (alternating text and punctuation)
            current_sentence = ""
            for i, part in enumerate(sentences):
                if i % 2 == 0:
                    # Text part
                    current_sentence += part
                else:
                    # Punctuation part
                    current_sentence += part
                    sentence_text = current_sentence.strip()
                    
                    # Only add if it meets minimum length requirement
                    if sentence_text and len(sentence_text) >= self.min_segment_length:
                        result.append(TextSegment(
                            text=sentence_text,
                            header=segment.header,
                            is_header=False
                        ))
                    current_sentence = ""
            
            # Add remaining text if any (last part without punctuation)
            if current_sentence.strip():
                remaining = current_sentence.strip()
                if len(remaining) >= self.min_segment_length:
                    result.append(TextSegment(
                        text=remaining,
                        header=segment.header,
                        is_header=False
                    ))
                elif remaining:  # If too short, append to last segment or create anyway
                    # If we have previous segments, append to last one
                    if result and not result[-1].is_header:
                        result[-1].text += " " + remaining
                    else:
                        # Create new segment even if short
                        result.append(TextSegment(
                            text=remaining,
                            header=segment.header,
                            is_header=False
                        ))
        
        return result
    
    def extract_headers(self, text: str) -> List[str]:
        """
        Extract all headers from text.
        
        Args:
            text: Input text
            
        Returns:
            List of header strings
        """
        headers = []
        matches = self.header_pattern.finditer(text)
        
        for match in matches:
            headers.append(match.group(2).strip())
        
        return headers

