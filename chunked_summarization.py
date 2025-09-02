#!/usr/bin/env python3
"""
Chunked Summarization Helper for Large Documents
Processes large documents by summarizing chunks and creating a final summary
"""

import json
import logging
from typing import List, Dict, Any
import boto3

logger = logging.getLogger(__name__)

class ChunkedSummarizer:
    def __init__(self):
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
            logger.info("AWS Bedrock client initialized for chunked summarization")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            self.bedrock_client = None
    
    def summarize_large_document(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize a large document by processing chunks and creating a final summary
        """
        if not self.bedrock_client:
            return {
                "success": False,
                "summary": "AWS Bedrock not available for summarization",
                "error": "Bedrock client not initialized"
            }
        
        try:
            print(f"📄 [CHUNKED SUMMARY] Starting chunked summarization for {len(chunks)} chunks")
            
            # Step 1: Summarize each chunk individually
            chunk_summaries = []
            successful_chunks = 0
            failed_chunks = 0
            
            for i, chunk in enumerate(chunks):
                print(f"📄 [CHUNKED SUMMARY] Summarizing chunk {i+1}/{len(chunks)} ({(i+1)/len(chunks)*100:.1f}%)")
                
                try:
                    chunk_summary = self._summarize_chunk(chunk)
                    if chunk_summary:
                        chunk_summaries.append({
                            'chunk_index': i,
                            'metadata': chunk.get('metadata', {}),
                            'summary': chunk_summary
                        })
                        successful_chunks += 1
                        print(f"✅ [CHUNKED SUMMARY] Chunk {i+1} summarized successfully")
                    else:
                        failed_chunks += 1
                        print(f"⚠️ [CHUNKED SUMMARY] Chunk {i+1} summary was empty")
                except Exception as e:
                    failed_chunks += 1
                    print(f"❌ [CHUNKED SUMMARY] Failed to summarize chunk {i+1}: {e}")
                    logger.error(f"Chunk {i+1} summarization failed: {e}")
            
            print(f"📊 [CHUNKED SUMMARY] Chunk summarization complete: {successful_chunks} successful, {failed_chunks} failed")
            
            if not chunk_summaries:
                return {
                    "success": False,
                    "summary": "Failed to summarize any chunks",
                    "error": "No chunk summaries generated"
                }
            
            print(f"✅ [CHUNKED SUMMARY] Generated {len(chunk_summaries)} chunk summaries")
            
            # Step 2: Create a final comprehensive summary from all chunk summaries
            final_summary = self._create_final_summary(chunk_summaries)
            
            return {
                "success": True,
                "summary": final_summary,
                "chunk_count": len(chunks),
                "summarized_chunks": len(chunk_summaries),
                "processing_method": "chunked_summarization"
            }
            
        except Exception as e:
            logger.error(f"Error in chunked summarization: {e}")
            return {
                "success": False,
                "summary": f"Error during chunked summarization: {str(e)}",
                "error": str(e)
            }
    
    def _summarize_chunk(self, chunk: Dict[str, Any]) -> str:
        """Summarize a single chunk"""
        try:
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})
            
            if not content.strip():
                return ""
            
            # Create a context-aware prompt for chunk summarization
            chunk_type = metadata.get('chunk_type', 'unknown')
            page_range = metadata.get('page_range', 'unknown')
            
            prompt = f"""
            Please provide a concise summary of the following document section.
            
            Document Section Information:
            - Section Type: {chunk_type}
            - Page Range: {page_range}
            - Content Length: {len(content)} characters
            
            Document Content:
                            {content[:16000]}  # Increased limit to preserve more content
            
            Instructions:
            1. Focus on the key information and main points
            2. Maintain the context and flow of information
            3. Include important facts, figures, and concepts
            4. Keep the summary concise but comprehensive
            5. If this is a technical document, preserve technical accuracy
            
            Summary:
            """
            
            # Call Bedrock for chunk summarization with timeout handling
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
                "top_k": 250,
                "top_p": 1.0,
                "stop_sequences": []
            }
            
            # Use timeout configuration for chunk summarization
            import boto3
            from botocore.config import Config
            
            config = Config(
                read_timeout=60,  # 1 minute timeout for chunks
                connect_timeout=30,
                retries={'max_attempts': 2}
            )
            
            bedrock_with_timeout = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',
                config=config
            )
            
            response = bedrock_with_timeout.invoke_model(
                modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            summary = result['content'][0]['text'].strip()
            
            print(f"📄 [CHUNKED SUMMARY] Chunk {metadata.get('chunk_index', 'unknown')} summarized ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing chunk: {e}")
            return ""
    
    def _create_final_summary(self, chunk_summaries: List[Dict[str, Any]]) -> str:
        """Create a final comprehensive summary from all chunk summaries"""
        try:
            print(f"📄 [CHUNKED SUMMARY] Creating final summary from {len(chunk_summaries)} chunk summaries")
            
            # If we have too many chunk summaries, process them in batches
            if len(chunk_summaries) > 8:
                print(f"📄 [CHUNKED SUMMARY] Too many summaries ({len(chunk_summaries)}), processing in batches...")
                return self._create_batched_final_summary(chunk_summaries)
            
            # For smaller numbers, process all at once but with better timeout handling
            combined_summaries = []
            for chunk_summary in chunk_summaries:
                metadata = chunk_summary['metadata']
                summary = chunk_summary['summary']
                
                section_info = f"[Section {chunk_summary['chunk_index']+1}: {metadata.get('chunk_type', 'unknown')} - {metadata.get('page_range', 'unknown')}]"
                combined_summaries.append(f"{section_info}\n{summary}")
            
            combined_text = "\n\n".join(combined_summaries)
            
            # Limit the input size to prevent timeouts
            max_input_size = 16000  # Increased to preserve more content
            if len(combined_text) > max_input_size:
                print(f"📄 [CHUNKED SUMMARY] Input too large ({len(combined_text)} chars), truncating to {max_input_size} chars")
                combined_text = combined_text[:max_input_size] + "\n\n[Content truncated due to size limits]"
            
            # Create final summary prompt
            prompt = f"""
            Please create a comprehensive final summary of the entire document based on the following section summaries.
            
            Document Overview:
            - Total Sections: {len(chunk_summaries)}
            - Document Type: Large document processed in chunks
            
            Section Summaries:
            {combined_text}
            
            Instructions for Final Summary:
            1. Create a coherent, well-structured summary of the entire document
            2. Organize information logically and maintain document flow
            3. Include the most important points from all sections
            4. Provide context and connections between different sections
            5. If this is a technical document, maintain technical accuracy
            6. Include key findings, conclusions, and recommendations if present
            7. Make the summary comprehensive but concise
            
            Final Document Summary:
            """
            
            # Call Bedrock for final summary with increased timeout
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1,
                "top_k": 250,
                "top_p": 1.0,
                "stop_sequences": []
            }
            
            # Use a custom session with longer timeout
            import boto3
            from botocore.config import Config
            
            config = Config(
                read_timeout=120,  # 2 minutes timeout
                connect_timeout=30,
                retries={'max_attempts': 3}
            )
            
            bedrock_with_timeout = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',
                config=config
            )
            
            response = bedrock_with_timeout.invoke_model(
                modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            final_summary = result['content'][0]['text'].strip()
            
            print(f"✅ [CHUNKED SUMMARY] Final summary created ({len(final_summary)} chars)")
            return final_summary
            
        except Exception as e:
            logger.error(f"Error creating final summary: {e}")
            # Fallback: return a simple combined summary
            print(f"⚠️ [CHUNKED SUMMARY] Using fallback summary due to error: {e}")
            return self._create_fallback_summary(chunk_summaries)
    
    def _create_batched_final_summary(self, chunk_summaries: List[Dict[str, Any]]) -> str:
        """Create final summary by processing summaries in batches"""
        try:
            print(f"📄 [CHUNKED SUMMARY] Processing {len(chunk_summaries)} summaries in batches...")
            
            # Process summaries in batches of 6
            batch_size = 6
            batch_summaries = []
            
            for i in range(0, len(chunk_summaries), batch_size):
                batch = chunk_summaries[i:i + batch_size]
                print(f"📄 [CHUNKED SUMMARY] Processing batch {i//batch_size + 1}/{(len(chunk_summaries) + batch_size - 1)//batch_size}")
                
                # Create intermediate summary for this batch
                batch_summary = self._create_batch_summary(batch, f"Batch {i//batch_size + 1}")
                if batch_summary:
                    batch_summaries.append(batch_summary)
            
            # Now create final summary from batch summaries
            if len(batch_summaries) > 1:
                print(f"📄 [CHUNKED SUMMARY] Creating final summary from {len(batch_summaries)} batch summaries")
                return self._create_final_from_batches(batch_summaries)
            elif len(batch_summaries) == 1:
                return batch_summaries[0]
            else:
                return "Failed to create summary from batches"
                
        except Exception as e:
            logger.error(f"Error in batched final summary: {e}")
            return self._create_fallback_summary(chunk_summaries)
    
    def _create_batch_summary(self, batch: List[Dict[str, Any]], batch_name: str) -> str:
        """Create summary for a batch of chunk summaries"""
        try:
            combined_summaries = []
            for chunk_summary in batch:
                metadata = chunk_summary['metadata']
                summary = chunk_summary['summary']
                
                section_info = f"[Section {chunk_summary['chunk_index']+1}: {metadata.get('chunk_type', 'unknown')} - {metadata.get('page_range', 'unknown')}]"
                combined_summaries.append(f"{section_info}\n{summary}")
            
            combined_text = "\n\n".join(combined_summaries)
            
            # Limit input size
            max_input_size = 6000
            if len(combined_text) > max_input_size:
                combined_text = combined_text[:max_input_size] + "\n\n[Content truncated]"
            
            prompt = f"""
            Create a concise summary of the following document sections ({batch_name}):
            
            {combined_text}
            
            Summary:
            """
            
            # Use timeout configuration
            import boto3
            from botocore.config import Config
            
            config = Config(
                read_timeout=90,
                connect_timeout=30,
                retries={'max_attempts': 2}
            )
            
            bedrock_with_timeout = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',
                config=config
            )
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.1,
                "top_k": 250,
                "top_p": 1.0,
                "stop_sequences": []
            }
            
            response = bedrock_with_timeout.invoke_model(
                modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Error creating batch summary: {e}")
            return ""
    
    def _create_final_from_batches(self, batch_summaries: List[str]) -> str:
        """Create final summary from batch summaries"""
        try:
            combined_batches = "\n\n".join([f"[Batch {i+1}]\n{summary}" for i, summary in enumerate(batch_summaries)])
            
            # Limit input size
            max_input_size = 8000
            if len(combined_batches) > max_input_size:
                combined_batches = combined_batches[:max_input_size] + "\n\n[Content truncated]"
            
            prompt = f"""
            Create a comprehensive final summary of the entire document based on these batch summaries:
            
            {combined_batches}
            
            Final Document Summary:
            """
            
            # Use timeout configuration
            import boto3
            from botocore.config import Config
            
            config = Config(
                read_timeout=120,
                connect_timeout=30,
                retries={'max_attempts': 3}
            )
            
            bedrock_with_timeout = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',
                config=config
            )
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.1,
                "top_k": 250,
                "top_p": 1.0,
                "stop_sequences": []
            }
            
            response = bedrock_with_timeout.invoke_model(
                modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Error creating final from batches: {e}")
            return "\n\n".join(batch_summaries)
    
    def _create_fallback_summary(self, chunk_summaries: List[Dict[str, Any]]) -> str:
        """Create a simple fallback summary when LLM calls fail"""
        try:
            print(f"📄 [CHUNKED SUMMARY] Creating fallback summary from {len(chunk_summaries)} chunks")
            
            # Create a simple combined summary
            summary_parts = []
            for chunk_summary in chunk_summaries:
                metadata = chunk_summary['metadata']
                summary = chunk_summary['summary']
                
                section_info = f"Section {chunk_summary['chunk_index']+1} ({metadata.get('page_range', 'unknown')}):"
                summary_parts.append(f"{section_info}\n{summary}")
            
            combined_summary = "\n\n".join(summary_parts)
            
            # Add a header
            final_summary = f"""
# Document Summary (Fallback Mode)

This document was processed in {len(chunk_summaries)} sections. Below is the combined summary of all sections:

{combined_summary}

---
*Note: This is a fallback summary created due to processing limitations. For a more comprehensive analysis, please try processing the document again or contact support.*
            """
            
            return final_summary.strip()
            
        except Exception as e:
            logger.error(f"Error creating fallback summary: {e}")
            return f"Error creating summary: {str(e)}"
    
    def get_processing_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get processing statistics for the chunks"""
        total_chunks = len(chunks)
        total_chars = sum(len(chunk.get('content', '')) for chunk in chunks)
        total_pages = sum(chunk.get('metadata', {}).get('pages_in_chunk', 1) for chunk in chunks)
        
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "total_pages": total_pages,
            "average_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
            "chunk_types": chunk_types,
            "processing_method": "chunked_summarization"
        }
