"""
Preprocess Service
Handles FASTA/FASTQ file preprocessing including trimming, length filtering, and quality filtering.
"""

import re
import gzip
import tempfile
from typing import List, Dict, Tuple, Optional
from io import StringIO
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import numpy as np


class PreprocessService:
    """Service for preprocessing FASTA/FASTQ files"""
    
    @staticmethod
    def _fuzzy_match(pattern: str, sequence: str, max_distance: float = 0.1) -> Optional[Tuple[int, int]]:
        """
        Fuzzy match to find pattern in sequence with allowed errors.
        
        Args:
            pattern: The pattern to search for
            sequence: The sequence to search in
            max_distance: Maximum allowed error rate (0.1 = 10% errors)
            
        Returns:
            Tuple of (start, end) positions if match found, None otherwise
        """
        if not pattern:
            return None
            
        pattern_len = len(pattern)
        max_errors = int(pattern_len * max_distance)
        
        # Try to find the pattern with fuzzy matching
        for i in range(len(sequence) - pattern_len + 1):
            substr = sequence[i:i + pattern_len]
            errors = sum(1 for a, b in zip(pattern.upper(), substr.upper()) if a != b)
            
            if errors <= max_errors:
                return (i, i + pattern_len)
        
        return None
    
    @staticmethod
    def _trim_constant_regions(sequence: str, quality: Optional[str], 
                               const5p: str, const3p: str) -> Tuple[str, Optional[str]]:
        """
        Trim constant regions from sequence.
        
        Args:
            sequence: The sequence to trim
            quality: Optional quality string
            const5p: 5' constant region
            const3p: 3' constant region
            
        Returns:
            Tuple of (trimmed_sequence, trimmed_quality)
        """
        trimmed_seq = sequence
        trimmed_qual = quality
        
        # Trim 5' constant region
        if const5p:
            match = PreprocessService._fuzzy_match(const5p, trimmed_seq)
            if match:
                start, end = match
                trimmed_seq = trimmed_seq[end:]
                if trimmed_qual:
                    trimmed_qual = trimmed_qual[end:]
        
        # Trim 3' constant region
        if const3p:
            match = PreprocessService._fuzzy_match(const3p, trimmed_seq)
            if match:
                start, end = match
                trimmed_seq = trimmed_seq[:start]
                if trimmed_qual:
                    trimmed_qual = trimmed_qual[:start]
        
        return trimmed_seq, trimmed_qual
    
    @staticmethod
    def _calculate_avg_error(quality_string: str) -> float:
        """
        Calculate average error probability from Phred quality scores.
        
        Args:
            quality_string: String of Phred quality scores
            
        Returns:
            Average error probability
        """
        if not quality_string:
            return 0.0
        
        # Convert Phred scores to error probabilities
        # Phred score Q relates to error probability P as: Q = -10 * log10(P)
        # Therefore: P = 10^(-Q/10)
        phred_scores = [ord(c) - 33 for c in quality_string]  # Assuming Phred+33 encoding
        error_probs = [10 ** (-q / 10) for q in phred_scores]
        
        return np.mean(error_probs)
    
    @staticmethod
    def preprocess_sequences(
        file_content: bytes,
        filename: str,
        const5p: str = "",
        const3p: str = "",
        length_range: Tuple[int, int] = (10, 100),
        max_error: float = 0.005
    ) -> List[Dict]:
        """
        Preprocess sequences from FASTA/FASTQ file.
        
        Args:
            file_content: The file content as bytes
            filename: Name of the uploaded file
            const5p: 5' constant region to trim
            const3p: 3' constant region to trim
            length_range: Tuple of (min_length, max_length)
            max_error: Maximum allowed average error
            
        Returns:
            List of dictionaries containing processed sequences
        """
        # Determine file format
        is_gzipped = filename.endswith('.gz')
        file_ext = filename.lower()
        
        if '.fastq' in file_ext or '.fq' in file_ext:
            file_format = 'fastq'
        elif '.fasta' in file_ext or '.fa' in file_ext:
            file_format = 'fasta'
        else:
            raise ValueError("Unsupported file format. Please provide FASTA or FASTQ file.")
        
        # Read file content
        if is_gzipped:
            content = gzip.decompress(file_content).decode('utf-8')
        else:
            content = file_content.decode('utf-8')
        
        # Parse sequences
        sequences_handle = StringIO(content)
        records = list(SeqIO.parse(sequences_handle, file_format))
        
        processed_data = []
        
        for record in records:
            sequence = str(record.seq)
            quality = None
            
            # Get quality scores if available (FASTQ)
            if hasattr(record, 'letter_annotations') and 'phred_quality' in record.letter_annotations:
                # Convert quality scores back to ASCII string
                quality_scores = record.letter_annotations['phred_quality']
                quality = ''.join(chr(q + 33) for q in quality_scores)
            
            # Trim constant regions
            trimmed_seq, trimmed_qual = PreprocessService._trim_constant_regions(
                sequence, quality, const5p, const3p
            )
            
            # Check length
            seq_length = len(trimmed_seq)
            if seq_length < length_range[0] or seq_length > length_range[1]:
                continue
            
            # Check quality if available
            avg_error = 0.0
            if trimmed_qual:
                avg_error = PreprocessService._calculate_avg_error(trimmed_qual)
                if avg_error > max_error:
                    continue
            
            # Add to results
            result = {
                'id': record.id,
                'sequence': trimmed_seq,
                'length': seq_length
            }
            
            if trimmed_qual:
                result['quality'] = trimmed_qual
                result['avg_error'] = round(avg_error, 6)
            
            processed_data.append(result)
        
        return processed_data
    
    @staticmethod
    def export_to_fasta(processed_data: List[Dict]) -> str:
        """
        Convert processed data to FASTA format string.
        
        Args:
            processed_data: List of processed sequence dictionaries
            
        Returns:
            FASTA formatted string
        """
        fasta_lines = []
        for item in processed_data:
            fasta_lines.append(f">{item['id']}")
            fasta_lines.append(item['sequence'])
        
        return '\n'.join(fasta_lines)
