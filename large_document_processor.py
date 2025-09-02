#!/usr/bin/env python3
"""
Large Document Processor for handling documents with many pages
Chunks large documents into smaller, manageable pieces for processing
"""

import os
import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path
import fitz  # PyMuPDF
import pypdfium2
import pdfplumber

logger = logging.getLogger(__name__)

class LargeDocumentProcessor:
    def __init__(self, 
                 max_chunk_size: int = 4000,  # characters per chunk
                 overlap_size: int = 200,     # overlap between chunks
                 max_pages_per_chunk: int = 10,  # max pages per chunk
                 min_chunk_size: int = 500):     # minimum chunk size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.max_pages_per_chunk = max_pages_per_chunk
        self.min_chunk_size = min_chunk_size
    
    def process_large_pdf(self, filepath: str) -> List[Dict[str, any]]:
        """
        Process a large PDF by chunking it into smaller pieces
        Returns a list of chunks with metadata
        """
        print(f"📄 [LARGE DOC] Processing large PDF: {filepath}")
        
        try:
            # Get total page count
            total_pages = self._get_pdf_page_count(filepath)
            print(f"📊 [LARGE DOC] Total pages: {total_pages}")
            
            if total_pages <= self.max_pages_per_chunk:
                print(f"📄 [LARGE DOC] Document is small enough, processing normally")
                return self._process_small_document(filepath)
            
            # For large documents, chunk by pages first
            print(f"📄 [LARGE DOC] Document is large, chunking by pages...")
            page_chunks = self._chunk_by_pages(filepath, total_pages)
            
            # Then further chunk each page chunk if needed
            final_chunks = []
            for i, page_chunk in enumerate(page_chunks):
                print(f"📄 [LARGE DOC] Processing page chunk {i+1}/{len(page_chunks)}")
                
                if len(page_chunk['content']) <= self.max_chunk_size:
                    final_chunks.append(page_chunk)
                else:
                    # Further chunk this page chunk
                    text_chunks = self._chunk_by_text(page_chunk['content'], page_chunk['metadata'])
                    final_chunks.extend(text_chunks)
            
            print(f"✅ [LARGE DOC] Created {len(final_chunks)} chunks from {total_pages} pages")
            return final_chunks
            
        except Exception as e:
            logger.error(f"Error processing large PDF {filepath}: {e}")
            print(f"❌ [LARGE DOC] Error: {e}")
            return []
    
    def _get_pdf_page_count(self, filepath: str) -> int:
        """Get the total number of pages in a PDF"""
        try:
            # Try PyMuPDF first
            doc = fitz.open(filepath)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.warning(f"PyMuPDF failed, trying pypdfium2: {e}")
            try:
                # Fallback to pypdfium2
                pdf = pypdfium2.PdfDocument(filepath)
                count = len(pdf)
                pdf.close()
                return count
            except Exception as e2:
                logger.error(f"Failed to get page count: {e2}")
                return 0
    
    def _process_small_document(self, filepath: str) -> List[Dict[str, any]]:
        """Process a small document normally"""
        try:
            text = self._extract_pdf_text(filepath)
            return [{
                'content': text,
                'metadata': {
                    'source_file': filepath,
                    'chunk_type': 'full_document',
                    'page_range': 'all',
                    'chunk_index': 0,
                    'total_chunks': 1
                }
            }]
        except Exception as e:
            logger.error(f"Error processing small document: {e}")
            return []
    
    def _chunk_by_pages(self, filepath: str, total_pages: int) -> List[Dict[str, any]]:
        """Chunk document by pages"""
        chunks = []
        
        try:
            # Use PyMuPDF for page-by-page extraction
            doc = fitz.open(filepath)
            
            for start_page in range(0, total_pages, self.max_pages_per_chunk):
                end_page = min(start_page + self.max_pages_per_chunk, total_pages)
                
                print(f"📄 [LARGE DOC] Extracting pages {start_page+1}-{end_page}")
                
                # Extract text from this page range
                text_parts = []
                for page_num in range(start_page, end_page):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    text_parts.append(text)
                
                combined_text = "\n\n".join(text_parts)
                
                # Clean up the text
                combined_text = self._clean_text(combined_text)
                
                if combined_text.strip():
                    chunks.append({
                        'content': combined_text,
                        'metadata': {
                            'source_file': filepath,
                            'chunk_type': 'page_range',
                            'page_range': f"{start_page+1}-{end_page}",
                            'chunk_index': len(chunks),
                            'total_pages': total_pages,
                            'pages_in_chunk': end_page - start_page
                        }
                    })
            
            doc.close()
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking by pages: {e}")
            return []
    
    def _chunk_by_text(self, text: str, base_metadata: Dict) -> List[Dict[str, any]]:
        """Further chunk text if it's still too large"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and current_chunk:
                # Save current chunk
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': {
                            **base_metadata,
                            'chunk_type': 'text_segment',
                            'chunk_index': chunk_index,
                            'text_length': len(current_chunk)
                        }
                    })
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.overlap_size:] if self.overlap_size > 0 else ""
                current_chunk = overlap_text + "\n\n" + paragraph
            
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add the last chunk
        if current_chunk.strip() and len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': {
                    **base_metadata,
                    'chunk_type': 'text_segment',
                    'chunk_index': chunk_index,
                    'text_length': len(current_chunk)
                }
            })
        
        return chunks
    
    def _extract_pdf_text(self, filepath: str) -> str:
        """Extract text from PDF using multiple methods"""
        # Try pypdfium2 first
        try:
            pdf = pypdfium2.PdfDocument(filepath)
            pages_text = [page.get_textpage().get_text_range() for page in pdf]
            combined = "\n".join(pages_text).strip()
            pdf.close()
            if combined:
                return combined
        except Exception as e:
            logger.debug(f"pypdfium2 extraction failed: {e}")
        
        # Try pdfplumber
        try:
            texts = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        texts.append(page_text)
            return "\n\n".join(texts)
        except Exception as e:
            logger.debug(f"pdfplumber extraction failed: {e}")
        
        # Try PyMuPDF
        try:
            doc = fitz.open(filepath)
            texts = []
            for page in doc:
                text = page.get_text()
                if text.strip():
                    texts.append(text)
            doc.close()
            return "\n\n".join(texts)
        except Exception as e:
            logger.error(f"All PDF extraction methods failed: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Remove page numbers and headers/footers
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()
    
    def get_chunk_summary(self, chunks: List[Dict[str, any]]) -> str:
        """Generate a summary of all chunks"""
        total_chunks = len(chunks)
        total_pages = sum(chunk['metadata'].get('pages_in_chunk', 1) for chunk in chunks)
        total_chars = sum(len(chunk['content']) for chunk in chunks)
        
        summary = f"""
📊 Document Chunking Summary:
• Total chunks created: {total_chunks}
• Total pages processed: {total_pages}
• Total characters: {total_chars:,}
• Average chunk size: {total_chars // total_chunks if total_chunks > 0 else 0:,} characters

📄 Chunk Details:
"""
        
        for i, chunk in enumerate(chunks):
            metadata = chunk['metadata']
            chunk_type = metadata.get('chunk_type', 'unknown')
            page_range = metadata.get('page_range', 'unknown')
            text_length = len(chunk['content'])
            
            summary += f"  {i+1}. {chunk_type} ({page_range}) - {text_length:,} chars\n"
        
        return summary
