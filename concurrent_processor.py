#!/usr/bin/env python3
"""
Concurrent Document Processor
Handles chunking, embedding generation, and LLM summarization in parallel
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

class ConcurrentProcessor:
    def __init__(self, max_workers: int = 4):
        """
        Initialize concurrent processor
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def process_document_concurrently(self, 
                                    chunks: List[Dict[str, Any]],
                                    summarizer,
                                    embedding_helper) -> Dict[str, Any]:
        """
        Process document chunks concurrently for both summarization and embedding
        
        Args:
            chunks: List of document chunks
            summarizer: ChunkedSummarizer instance
            embedding_helper: TitanEmbeddingHelper instance
            
        Returns:
            Dict with summaries and embeddings
        """
        print(f"🚀 [CONCURRENT] Starting concurrent processing of {len(chunks)} chunks")
        start_time = time.time()
        
        try:
            # Submit both summarization and embedding tasks concurrently
            futures = []
            
            # Submit summarization tasks
            for i, chunk in enumerate(chunks):
                future = self.executor.submit(
                    self._summarize_chunk_wrapper, 
                    chunk, 
                    summarizer, 
                    i
                )
                futures.append(('summary', i, future))
            
            # Submit embedding tasks (can be done in parallel with summarization)
            for i, chunk in enumerate(chunks):
                future = self.executor.submit(
                    self._embed_chunk_wrapper,
                    chunk,
                    embedding_helper,
                    i
                )
                futures.append(('embedding', i, future))
            
            # Collect results
            results = {
                'summaries': [None] * len(chunks),
                'embeddings': [None] * len(chunks),
                'successful_summaries': 0,
                'successful_embeddings': 0,
                'failed_summaries': 0,
                'failed_embeddings': 0
            }
            
            # Process completed futures
            for task_type, chunk_index, future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per task
                    
                    if task_type == 'summary':
                        if result:
                            results['summaries'][chunk_index] = result
                            results['successful_summaries'] += 1
                            print(f"✅ [CONCURRENT] Summary {chunk_index + 1} completed")
                        else:
                            results['failed_summaries'] += 1
                            print(f"❌ [CONCURRENT] Summary {chunk_index + 1} failed")
                    
                    elif task_type == 'embedding':
                        if result:
                            results['embeddings'][chunk_index] = result
                            results['successful_embeddings'] += 1
                            print(f"✅ [CONCURRENT] Embedding {chunk_index + 1} completed")
                        else:
                            results['failed_embeddings'] += 1
                            print(f"❌ [CONCURRENT] Embedding {chunk_index + 1} failed")
                            
                except Exception as e:
                    if task_type == 'summary':
                        results['failed_summaries'] += 1
                        print(f"❌ [CONCURRENT] Summary {chunk_index + 1} failed: {e}")
                    else:
                        results['failed_embeddings'] += 1
                        print(f"❌ [CONCURRENT] Embedding {chunk_index + 1} failed: {e}")
            
            # Create final summary from successful summaries
            successful_summaries = [s for s in results['summaries'] if s is not None]
            final_summary = None
            
            if successful_summaries:
                final_summary = self._create_final_summary_concurrent(successful_summaries, summarizer)
            
            processing_time = time.time() - start_time
            
            print(f"📊 [CONCURRENT] Processing complete in {processing_time:.2f} seconds")
            print(f"📊 [CONCURRENT] Results: {results['successful_summaries']}/{len(chunks)} summaries, {results['successful_embeddings']}/{len(chunks)} embeddings")
            
            return {
                "success": True,
                "summary": final_summary,
                "embeddings": results['embeddings'],
                "chunk_count": len(chunks),
                "successful_summaries": results['successful_summaries'],
                "successful_embeddings": results['successful_embeddings'],
                "processing_time": processing_time,
                "processing_method": "concurrent_processing"
            }
            
        except Exception as e:
            logger.error(f"Error in concurrent processing: {e}")
            return {
                "success": False,
                "summary": f"Error during concurrent processing: {str(e)}",
                "error": str(e)
            }
    
    def _summarize_chunk_wrapper(self, chunk: Dict[str, Any], summarizer, chunk_index: int) -> Dict[str, Any]:
        """Wrapper for chunk summarization"""
        try:
            summary = summarizer._summarize_chunk(chunk)
            if summary:
                return {
                    'chunk_index': chunk_index,
                    'metadata': chunk.get('metadata', {}),
                    'summary': summary
                }
            return None
        except Exception as e:
            logger.error(f"Error summarizing chunk {chunk_index}: {e}")
            return None
    
    def _embed_chunk_wrapper(self, chunk: Dict[str, Any], embedding_helper, chunk_index: int) -> List[float]:
        """Wrapper for chunk embedding"""
        try:
            content = chunk.get('content', '')
            if content:
                embedding = embedding_helper.generate_single_embedding(content)
                return embedding
            return None
        except Exception as e:
            logger.error(f"Error embedding chunk {chunk_index}: {e}")
            return None
    
    def _create_final_summary_concurrent(self, chunk_summaries: List[Dict[str, Any]], summarizer) -> str:
        """Create final summary from chunk summaries"""
        try:
            # Use the existing final summary creation method
            return summarizer._create_final_summary(chunk_summaries)
        except Exception as e:
            logger.error(f"Error creating final summary: {e}")
            # Fallback: simple concatenation
            summaries = [cs['summary'] for cs in chunk_summaries if cs.get('summary')]
            return "\n\n".join(summaries)
    
    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown(wait=True)
