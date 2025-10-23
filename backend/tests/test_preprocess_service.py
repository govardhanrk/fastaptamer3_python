"""
Unit tests for PreprocessService
"""

import unittest
from io import BytesIO
from services.preprocess_service import PreprocessService


class TestPreprocessService(unittest.TestCase):
    
    def test_fuzzy_match_exact(self):
        """Test exact pattern matching"""
        pattern = "ATCG"
        sequence = "XXATCGXX"
        result = PreprocessService._fuzzy_match(pattern, sequence, max_distance=0.1)
        self.assertIsNotNone(result)
        self.assertEqual(result, (2, 6))
    
    def test_fuzzy_match_with_errors(self):
        """Test pattern matching with errors"""
        pattern = "ATCG"
        sequence = "XXATCAXX"  # One mismatch
        result = PreprocessService._fuzzy_match(pattern, sequence, max_distance=0.3)
        self.assertIsNotNone(result)
    
    def test_fuzzy_match_no_match(self):
        """Test when pattern is not found"""
        pattern = "ATCG"
        sequence = "GGGGGGGG"
        result = PreprocessService._fuzzy_match(pattern, sequence, max_distance=0.1)
        self.assertIsNone(result)
    
    def test_trim_constant_regions_5p(self):
        """Test trimming 5' constant region"""
        sequence = "ATCGNNNNNN"
        quality = "IIIIIIIIII"
        const5p = "ATCG"
        const3p = ""
        
        trimmed_seq, trimmed_qual = PreprocessService._trim_constant_regions(
            sequence, quality, const5p, const3p
        )
        
        self.assertEqual(trimmed_seq, "NNNNNN")
        self.assertEqual(trimmed_qual, "IIIIII")
    
    def test_trim_constant_regions_3p(self):
        """Test trimming 3' constant region"""
        sequence = "NNNNNNGGGG"
        quality = "IIIIIIIIII"
        const5p = ""
        const3p = "GGGG"
        
        trimmed_seq, trimmed_qual = PreprocessService._trim_constant_regions(
            sequence, quality, const5p, const3p
        )
        
        self.assertEqual(trimmed_seq, "NNNNNN")
        self.assertEqual(trimmed_qual, "IIIIII")
    
    def test_calculate_avg_error(self):
        """Test average error calculation"""
        # High quality scores (Q=40, error ~0.0001)
        quality_string = "I" * 10  # I = 73 - 33 = 40
        avg_error = PreprocessService._calculate_avg_error(quality_string)
        self.assertLess(avg_error, 0.001)
    
    def test_preprocess_sequences_fasta(self):
        """Test preprocessing FASTA file"""
        fasta_content = b">seq1\nATCGATCGATCGATCG\n>seq2\nGGGGGGGGGGGG\n"
        
        result = PreprocessService.preprocess_sequences(
            file_content=fasta_content,
            filename="test.fasta",
            const5p="",
            const3p="",
            length_range=(10, 20),
            max_error=0.005
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'seq1')
        self.assertEqual(result[0]['sequence'], 'ATCGATCGATCGATCG')
        self.assertEqual(result[0]['length'], 16)
    
    def test_export_to_fasta(self):
        """Test exporting to FASTA format"""
        data = [
            {'id': 'seq1', 'sequence': 'ATCG', 'length': 4},
            {'id': 'seq2', 'sequence': 'GGGG', 'length': 4}
        ]
        
        fasta_output = PreprocessService.export_to_fasta(data)
        
        self.assertIn('>seq1', fasta_output)
        self.assertIn('ATCG', fasta_output)
        self.assertIn('>seq2', fasta_output)
        self.assertIn('GGGG', fasta_output)


if __name__ == '__main__':
    unittest.main()
