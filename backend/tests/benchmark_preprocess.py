"""
Performance Benchmark: Original vs Optimized PreprocessService

Run this to compare performance between implementations.
"""

import time
import random
import string
import sys
from pathlib import Path
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import both versions
from services.preprocess_service import PreprocessService as OriginalService
from services.preprocess_service_optimized import PreprocessService as OptimizedService


def generate_test_fasta(num_sequences: int = 1000, seq_length: int = 100) -> bytes:
    """Generate a test FASTA file with random sequences"""
    bases = 'ATCG'
    fasta_lines = []
    
    for i in range(num_sequences):
        seq = ''.join(random.choice(bases) for _ in range(seq_length))
        fasta_lines.append(f">seq_{i}")
        fasta_lines.append(seq)
    
    return '\n'.join(fasta_lines).encode('utf-8')


def generate_test_fastq(num_sequences: int = 1000, seq_length: int = 100) -> bytes:
    """Generate a test FASTQ file with random sequences and quality scores"""
    bases = 'ATCG'
    # Quality characters (Phred+33 encoding, scores 20-40)
    quality_chars = ''.join(chr(i) for i in range(53, 74))  # Phred 20-40
    
    fastq_lines = []
    
    for i in range(num_sequences):
        seq = ''.join(random.choice(bases) for _ in range(seq_length))
        qual = ''.join(random.choice(quality_chars) for _ in range(seq_length))
        
        fastq_lines.append(f"@seq_{i}")
        fastq_lines.append(seq)
        fastq_lines.append("+")
        fastq_lines.append(qual)
    
    return '\n'.join(fastq_lines).encode('utf-8')


def benchmark_service(service_class, file_content: bytes, filename: str, 
                      const5p: str = "", const3p: str = "", 
                      iterations: int = 5):
    """Benchmark a service implementation"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        result = service_class.preprocess_sequences(
            file_content=file_content,
            filename=filename,
            const5p=const5p,
            const3p=const3p,
            length_range=(10, 150),
            max_error=0.005
        )
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        'avg': avg_time,
        'min': min_time,
        'max': max_time,
        'result_count': len(result)
    }


def run_benchmarks():
    """Run comprehensive benchmarks"""
    
    print("=" * 80)
    print("PERFORMANCE BENCHMARK: Original vs Optimized PreprocessService")
    print("=" * 80)
    
    test_cases = [
        ("Small FASTA (100 sequences)", generate_test_fasta(100, 100), "test.fasta"),
        ("Medium FASTA (1000 sequences)", generate_test_fasta(1000, 100), "test.fasta"),
        ("Large FASTA (10000 sequences)", generate_test_fasta(10000, 100), "test.fasta"),
        ("Small FASTQ (100 sequences)", generate_test_fastq(100, 100), "test.fastq"),
        ("Medium FASTQ (1000 sequences)", generate_test_fastq(1000, 100), "test.fastq"),
        ("Large FASTQ (10000 sequences)", generate_test_fastq(10000, 100), "test.fastq"),
    ]
    
    for test_name, file_content, filename in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Test: {test_name}")
        print(f"{'=' * 80}")
        
        # Benchmark original
        print("\n🔵 Original Implementation:")
        original_result = benchmark_service(OriginalService, file_content, filename)
        print(f"   Average: {original_result['avg']:.4f}s")
        print(f"   Min:     {original_result['min']:.4f}s")
        print(f"   Max:     {original_result['max']:.4f}s")
        print(f"   Results: {original_result['result_count']} sequences")
        
        # Benchmark optimized
        print("\n🟢 Optimized Implementation:")
        optimized_result = benchmark_service(OptimizedService, file_content, filename)
        print(f"   Average: {optimized_result['avg']:.4f}s")
        print(f"   Min:     {optimized_result['min']:.4f}s")
        print(f"   Max:     {optimized_result['max']:.4f}s")
        print(f"   Results: {optimized_result['result_count']} sequences")
        
        # Calculate speedup
        speedup = original_result['avg'] / optimized_result['avg']
        improvement = ((original_result['avg'] - optimized_result['avg']) / original_result['avg']) * 100
        
        print(f"\n📊 Performance Improvement:")
        print(f"   Speedup: {speedup:.2f}x faster")
        print(f"   Improvement: {improvement:.1f}% reduction in time")
        
        if speedup > 1:
            print(f"   ✅ Optimized version is {speedup:.2f}x faster!")
        else:
            print(f"   ⚠️  Optimized version is slower (needs review)")
    
    print("\n" + "=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    
    # Test with constant regions
    print("\n\n" + "=" * 80)
    print("Additional Test: With Constant Region Trimming")
    print("=" * 80)
    
    # Create sequences with known constant regions
    const5p = "ATCGATCG"
    const3p = "GCTAGCTA"
    
    file_content = generate_test_fasta(1000, 100)
    
    print("\n🔵 Original with trimming:")
    original_trim = benchmark_service(OriginalService, file_content, "test.fasta", const5p, const3p)
    print(f"   Average: {original_trim['avg']:.4f}s")
    
    print("\n🟢 Optimized with trimming:")
    optimized_trim = benchmark_service(OptimizedService, file_content, "test.fasta", const5p, const3p)
    print(f"   Average: {optimized_trim['avg']:.4f}s")
    
    speedup = original_trim['avg'] / optimized_trim['avg']
    print(f"\n📊 Speedup with trimming: {speedup:.2f}x faster")


if __name__ == '__main__':
    print("\n⚠️  Note: First run may be slower due to JIT compilation and caching.\n")
    run_benchmarks()
