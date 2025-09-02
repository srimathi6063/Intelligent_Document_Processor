#!/usr/bin/env python3
"""
Configuration for Large Document Processing
"""

# Large Document Detection
LARGE_DOCUMENT_PAGE_THRESHOLD = 20  # Documents with >20 pages are considered large

# Chunking Parameters
CHUNKING_CONFIG = {
    'max_chunk_size': 4000,        # Maximum characters per chunk
    'overlap_size': 200,           # Overlap between chunks (for context)
    'max_pages_per_chunk': 10,     # Maximum pages per chunk
    'min_chunk_size': 500,         # Minimum chunk size
}

# Summarization Parameters
SUMMARIZATION_CONFIG = {
    'chunk_max_tokens': 1000,      # Max tokens for chunk summaries
    'final_max_tokens': 2000,      # Max tokens for final summary
    'temperature': 0.1,            # Low temperature for consistent summaries
    'chunk_content_limit': 8000,   # Max characters per chunk for LLM input
    'final_content_limit': 12000,  # Max characters for final summary input
}

# Processing Options
PROCESSING_OPTIONS = {
    'enable_chunked_processing': True,    # Enable/disable chunked processing
    'store_chunks_in_weaviate': True,     # Store individual chunks in Weaviate
    'enable_progress_logging': True,      # Show progress during processing
    'fallback_to_normal': True,          # Fallback to normal processing if chunking fails
}

# Performance Settings
PERFORMANCE_CONFIG = {
    'max_concurrent_chunks': 3,    # Maximum concurrent chunk processing
    'chunk_processing_timeout': 300,  # Timeout for chunk processing (seconds)
    'retry_failed_chunks': True,   # Retry failed chunk processing
    'max_retries': 2,              # Maximum retry attempts
}
