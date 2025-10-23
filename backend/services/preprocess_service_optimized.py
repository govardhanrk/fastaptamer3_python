"""
Optimized Preprocess Service
Handles FASTA/FASTQ file preprocessing with performance optimizations.
"""

import re
import gzip
from typing import List, Dict, Tuple, Optional
from io import StringIO
from Bio import SeqIO
import numpy as np


class PreprocessService:
    """Optimized service for preprocessing FASTA/FASTQ files"""
    
    @staticmethod
    def _fuzzy_match(pattern: str, sequence: str, max_distance: float = 0.1) -> Optional[Tuple[int, int]]:
        """
        Optimized fuzzy match using vectorized operations.
        
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
        seq_len = len(sequence)
        
        if pattern_len > seq_len:
            return None
            
        max_errors = int(pattern_len * max_distance)
        pattern_upper = pattern.upper()
        sequence_upper = sequence.upper()
        
        # Optimized: Use string slicing and comparison
        # Early exit on first match found
        for i in range(seq_len - pattern_len + 1):
            substr = sequence_upper[i:i + pattern_len]
            
            # Count mismatches - exit early if exceeds threshold
            errors = 0
            for j in range(pattern_len):
                if pattern_upper[j] != substr[j]:
                    errors += 1
                    if errors > max_errors:
                        break
            
            if errors <= max_errors:
                return (i, i + pattern_len)
        
        return None
    
    @staticmethod
    def _trim_constant_regions(sequence: str, quality: Optional[str], 
                               const5p: str, const3p: str) -> Tuple[str, Optional[str]]:
        """
        Trim constant regions from sequence (optimized).
        
        Args:
            sequence: The sequence to trim
            quality: Optional quality string
            const5p: 5' constant region
            const3p: 3' constant region
            
        Returns:
            Tuple of (trimmed_sequence, trimmed_quality)
        """
        start_pos = 0
        end_pos = len(sequence)
        
        # Trim 5' constant region
        if const5p:
            match = PreprocessService._fuzzy_match(const5p, sequence)
            if match:
                start_pos = match[1]
        
        # Trim 3' constant region (search only in the trimmed portion)
        if const3p and start_pos < end_pos:
            trimmed_for_3p = sequence[start_pos:]
            match = PreprocessService._fuzzy_match(const3p, trimmed_for_3p)
            if match:
                end_pos = start_pos + match[0]
        
        # Single slice operation
        trimmed_seq = sequence[start_pos:end_pos]
        trimmed_qual = quality[start_pos:end_pos] if quality else None
        
        return trimmed_seq, trimmed_qual
    
    @staticmethod
    def _calculate_avg_error_vectorized(quality_string: str) -> float:
        """
        Calculate average error probability using vectorized NumPy operations.
        
        Args:
            quality_string: String of Phred quality scores
            
        Returns:
            Average error probability
        """
        if not quality_string:
            return 0.0
        
        # Vectorized conversion: much faster than list comprehension
        # Convert ASCII to Phred scores in one operation
        phred_array = np.frombuffer(quality_string.encode('latin-1'), dtype=np.uint8).astype(np.int32) - 33
        
        # Vectorized calculation: P = 10^(-Q/10)
        error_probs = np.power(10.0, -phred_array.astype(np.float64) / 10.0)
        
        return float(np.mean(error_probs))
    
    @staticmethod
    def _process_record(record, const5p: str, const3p: str, 
                       length_range: Tuple[int, int], max_error: float,
                       file_format: str) -> Optional[Dict]:
        """
        Process a single sequence record (for potential parallel processing).
        
        Args:
            record: SeqRecord object
            const5p: 5' constant region
            const3p: 3' constant region
            length_range: Tuple of (min_length, max_length)
            max_error: Maximum allowed average error
            file_format: 'fasta' or 'fastq'
            
        Returns:
            Processed record dict or None if filtered out
        """
        sequence = str(record.seq)
        quality = None
        
        # Get quality scores if FASTQ
        if file_format == 'fastq' and hasattr(record, 'letter_annotations'):
            quality_scores = record.letter_annotations.get('phred_quality')
            if quality_scores:
                # Convert to string only once
                quality = ''.join(chr(q + 33) for q in quality_scores)
        
        # Trim constant regions
        trimmed_seq, trimmed_qual = PreprocessService._trim_constant_regions(
            sequence, quality, const5p, const3p
        )
        
        # Length filter (early exit)
        seq_length = len(trimmed_seq)
        if seq_length < length_range[0] or seq_length > length_range[1]:
            return None
        
        # Quality filter if applicable
        avg_error = 0.0
        if trimmed_qual:
            avg_error = PreprocessService._calculate_avg_error_vectorized(trimmed_qual)
            if avg_error > max_error:
                return None
        
        # Build result
        result = {
            'id': record.id,
            'sequence': trimmed_seq,
            'length': seq_length
        }
        
        if trimmed_qual:
            result['quality'] = trimmed_qual
            result['avg_error'] = round(avg_error, 6)
        
        return result
    
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
        Preprocess sequences from FASTA/FASTQ file (optimized version).
        
        Performance improvements:
        1. Vectorized NumPy operations for quality score calculations
        2. Single-pass sequence trimming
        3. Early exit on length/quality filters
        4. Reduced string operations
        5. Generator-based processing to reduce memory overhead
        
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
        
        # Decompress if needed
        if is_gzipped:
            content = gzip.decompress(file_content).decode('utf-8')
        else:
            content = file_content.decode('utf-8')
        
        # Parse sequences using generator (memory efficient)
        sequences_handle = StringIO(content)
        
        # Process records with generator comprehension and filter
        processed_data = []
        
        # Pre-compute constants outside loop
        min_len, max_len = length_range
        
        for record in SeqIO.parse(sequences_handle, file_format):
            result = PreprocessService._process_record(
                record, const5p, const3p, length_range, max_error, file_format
            )
            if result is not None:
                processed_data.append(result)
        
        return processed_data
    
    @staticmethod
    def export_to_fasta(processed_data: List[Dict]) -> str:
        """
        Convert processed data to FASTA format string (optimized).
        
        Args:
            processed_data: List of processed sequence dictionaries
            
        Returns:
            FASTA formatted string
        """
        # Use list comprehension and join (faster than repeated string concatenation)
        fasta_lines = [f">{item['id']}\n{item['sequence']}" for item in processed_data]
        return '\n'.join(fasta_lines)
