"""
Integration tests for Preprocess API endpoints
Run these tests with the backend server running.
"""

import requests
import json
from pathlib import Path


class TestPreprocessAPI:
    """Test the preprocess API endpoints"""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    def test_preprocess_with_sample_file(self):
        """Test preprocessing with the sample FASTA file"""
        
        # Path to sample file
        sample_file = Path(__file__).parent / "sample_data" / "test_sequences.fasta"
        
        if not sample_file.exists():
            print(f"❌ Sample file not found: {sample_file}")
            return
        
        # Prepare the request
        url = f"{self.BASE_URL}/preprocess"
        
        with open(sample_file, 'rb') as f:
            files = {'file': ('test_sequences.fasta', f, 'text/plain')}
            data = {
                'const5p': '',
                'const3p': '',
                'min_length': 10,
                'max_length': 100,
                'max_error': 0.005
            }
            
            response = requests.post(url, files=files, data=data)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print("✅ Preprocess API test passed!")
            print(f"   Total sequences: {result['total_sequences']}")
            print(f"   Success: {result['success']}")
            if result['data']:
                print(f"   First sequence ID: {result['data'][0]['id']}")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   Error: {response.text}")
    
    def test_preprocess_with_constant_regions(self):
        """Test preprocessing with constant region trimming"""
        
        sample_file = Path(__file__).parent / "sample_data" / "test_sequences.fasta"
        
        if not sample_file.exists():
            print(f"❌ Sample file not found: {sample_file}")
            return
        
        url = f"{self.BASE_URL}/preprocess"
        
        with open(sample_file, 'rb') as f:
            files = {'file': ('test_sequences.fasta', f, 'text/plain')}
            data = {
                'const5p': 'ATCG',  # Example 5' constant
                'const3p': 'GCTA',  # Example 3' constant
                'min_length': 5,
                'max_length': 200,
                'max_error': 0.01
            }
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Constant region trimming test passed!")
            print(f"   Total sequences after trimming: {result['total_sequences']}")
        else:
            print(f"❌ Test failed with status {response.status_code}")
            print(f"   Error: {response.text}")
    
    def test_download_preprocessed(self):
        """Test downloading preprocessed sequences"""
        
        url = f"{self.BASE_URL}/preprocess/download"
        
        # Sample data
        sequences = [
            {'id': 'seq1', 'sequence': 'ATCGATCG', 'length': 8},
            {'id': 'seq2', 'sequence': 'GGGGCCCC', 'length': 8}
        ]
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=sequences, headers=headers)
        
        if response.status_code == 200:
            print("✅ Download API test passed!")
            print(f"   Downloaded {len(response.content)} bytes")
            print("   Content preview:")
            print(response.text[:200])
        else:
            print(f"❌ Download test failed with status {response.status_code}")
            print(f"   Error: {response.text}")
    
    def test_invalid_parameters(self):
        """Test API with invalid parameters"""
        
        sample_file = Path(__file__).parent / "sample_data" / "test_sequences.fasta"
        
        if not sample_file.exists():
            print(f"❌ Sample file not found: {sample_file}")
            return
        
        url = f"{self.BASE_URL}/preprocess"
        
        # Test with invalid length range
        with open(sample_file, 'rb') as f:
            files = {'file': ('test_sequences.fasta', f, 'text/plain')}
            data = {
                'const5p': '',
                'const3p': '',
                'min_length': 100,  # Min > Max (invalid)
                'max_length': 10,
                'max_error': 0.005
            }
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code == 400:
            print("✅ Invalid parameter validation test passed!")
            print(f"   Correctly rejected with: {response.json()['detail']}")
        else:
            print(f"❌ Test failed - should have returned 400")


def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("Testing Preprocess API Endpoints")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running on http://localhost:8000\n")
    
    tester = TestPreprocessAPI()
    
    print("\n1️⃣  Testing basic preprocess...")
    tester.test_preprocess_with_sample_file()
    
    print("\n2️⃣  Testing with constant regions...")
    tester.test_preprocess_with_constant_regions()
    
    print("\n3️⃣  Testing download endpoint...")
    tester.test_download_preprocessed()
    
    print("\n4️⃣  Testing invalid parameters...")
    tester.test_invalid_parameters()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == '__main__':
    run_all_tests()
