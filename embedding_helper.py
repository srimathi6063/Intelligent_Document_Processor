import boto3
import logging
import json
from typing import List, Dict, Any, Tuple
import numpy as np
from collections import Counter
import re
from botocore.config import Config

logger = logging.getLogger(__name__)

class TitanEmbeddingHelper:
    """
    Helper class for AWS Titan embedding model integration with hybrid search capabilities
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize Titan embedding client
        """
        self.region_name = region_name
        self.model_id = 'amazon.titan-embed-text-v1'
        self.titan_available = False
        
        try:
            # Configure Bedrock client with extended timeouts for Titan embeddings
            try:
                from config.settings import settings
                bedrock_config = Config(
                    read_timeout=settings.TITAN_READ_TIMEOUT,
                    connect_timeout=settings.TITAN_CONNECT_TIMEOUT,
                    retries={'max_attempts': settings.TITAN_MAX_RETRIES}
                )
            except ImportError:
                # Fallback configuration if settings not available
                bedrock_config = Config(
                    read_timeout=120,      # 2 minutes for embedding generation
                    connect_timeout=30,    # 30 seconds for connection
                    retries={'max_attempts': 2}  # Retry up to 2 times
                )
            
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name,
                config=bedrock_config
            )
            
            # Test if Titan model is accessible
            self._test_titan_access()
            
        except Exception as e:
            logger.warning(f"Failed to initialize Titan embedding client: {e}")
            self.bedrock_client = None
            self.titan_available = False
    
    def _test_titan_access(self):
        """
        Test if Titan model is accessible
        """
        try:
            # Try a simple test call
            test_body = {
                "inputText": "test"
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(test_body)
            )
            
            # If we get here, Titan is available
            self.titan_available = True
            logger.info("✅ Titan embedding model is accessible")
            
        except Exception as e:
            if "AccessDeniedException" in str(e):
                logger.warning("❌ Titan embedding model access denied - using fallback methods")
                self.titan_available = False
            else:
                logger.warning(f"❌ Titan embedding model test failed: {e}")
                self.titan_available = False
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Titan model
        """
        if not self.titan_available:
            logger.warning("Titan embeddings not available, using fallback embeddings")
            return self._generate_fallback_embeddings(texts)
        
        try:
            embeddings = []
            
            for text in texts:
                # Truncate text if too long (Titan has limits)
                # Increased limit to preserve more content
                if len(text) > 32000:  # Increased from 8000 to 32000
                    logger.warning(f"Text too long ({len(text)} chars), truncating to 32000 chars")
                    text = text[:32000]
                
                # Prepare the request body
                request_body = {
                    "inputText": text
                }
                
                # Call Titan embedding model
                response = self.bedrock_client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
                
                logger.debug(f"Generated Titan embedding for text of length {len(text)}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating Titan embeddings: {e}")
            logger.info("Falling back to basic embeddings")
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate basic fallback embeddings when Titan is not available
        """
        embeddings = []
        
        for text in texts:
            # Create a simple hash-based embedding
            # This is not as good as Titan but provides some vector representation
            embedding = self._text_to_simple_embedding(text)
            embeddings.append(embedding)
            
            logger.debug(f"Generated fallback embedding for text of length {len(text)}")
        
        return embeddings
    
    def _text_to_simple_embedding(self, text: str, dimensions: int = 384) -> List[float]:
        """
        Convert text to a simple embedding using hash-based approach
        """
        try:
            # Create a simple hash-based embedding
            import hashlib
            
            # Normalize text
            text_lower = text.lower()
            
            # Create embedding based on character frequencies and hashes
            embedding = []
            
            # Use character frequency
            char_freq = {}
            for char in text_lower:
                if char.isalnum():
                    char_freq[char] = char_freq.get(char, 0) + 1
            
            # Create hash-based values
            text_hash = hashlib.md5(text_lower.encode()).hexdigest()
            
            # Generate embedding values
            for i in range(dimensions):
                if i < len(char_freq):
                    # Use character frequency
                    char = list(char_freq.keys())[i % len(char_freq)]
                    value = char_freq[char] / len(text_lower)
                else:
                    # Use hash-based values
                    hash_part = text_hash[i % len(text_hash)]
                    value = (ord(hash_part) - ord('a')) / 26.0 if hash_part.isalpha() else int(hash_part) / 10.0
                
                embedding.append(value)
            
            # Normalize to unit vector
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            
            return embedding_array.tolist()
            
        except Exception as e:
            logger.error(f"Error generating fallback embedding: {e}")
            # Return zero vector as last resort
            return [0.0] * dimensions
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Ensure same dimensions
            if len(vec1) != len(vec2):
                min_len = min(len(vec1), len(vec2))
                vec1 = vec1[:min_len]
                vec2 = vec2[:min_len]
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def bm25_search(self, query: str, documents: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword-based search
        """
        try:
            # Preprocess query
            query_terms = self._preprocess_text(query)
            query_term_freq = Counter(query_terms)
            
            results = []
            
            for doc in documents:
                content = doc.get('content', '')
                doc_terms = self._preprocess_text(content)
                doc_term_freq = Counter(doc_terms)
                
                # Calculate BM25 score
                bm25_score = self._calculate_bm25_score(
                    query_term_freq, doc_term_freq, len(doc_terms), 
                    len(documents), self._get_avg_doc_length(documents)
                )
                
                if bm25_score > 0:
                    results.append({
                        'document': doc,
                        'bm25_score': bm25_score,
                        'search_type': 'bm25'
                    })
            
            # Sort by BM25 score (highest first)
            results.sort(key=lambda x: x['bm25_score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def vector_search(self, query_embedding: List[float], 
                     documents: List[Dict[str, Any]], 
                     k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        """
        try:
            results = []
            
            for doc in documents:
                doc_embedding = doc.get('embedding', [])
                if doc_embedding:
                    similarity = self.calculate_similarity(query_embedding, doc_embedding)
                    results.append({
                        'document': doc,
                        'vector_score': similarity,
                        'search_type': 'vector'
                    })
            
            # Sort by vector similarity (highest first)
            results.sort(key=lambda x: x['vector_score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []
    
    def hybrid_search(self, query: str, documents: List[Dict[str, Any]], 
                     query_embedding: List[float] = None,
                     bm25_weight: float = 0.5, vector_weight: float = 0.5,
                     k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and vector similarity
        """
        try:
            # Generate query embedding if not provided
            if query_embedding is None:
                query_embedding = self.generate_single_embedding(query)
            
            # Perform BM25 search
            bm25_results = self.bm25_search(query, documents, k * 2)
            
            # Perform vector search (if embeddings are available)
            vector_results = []
            if query_embedding and any(doc.get('embedding') for doc in documents):
                vector_results = self.vector_search(query_embedding, documents, k * 2)
            
            # If no vector results, use only BM25
            if not vector_results:
                logger.info("No vector search results available, using BM25 only")
                return bm25_results[:k]
            
            # Combine results
            combined_results = self._combine_search_results(
                bm25_results, vector_results, bm25_weight, vector_weight
            )
            
            # Sort by combined score and return top k
            combined_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return combined_results[:k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to BM25 search
            return self.bm25_search(query, documents, k)
    
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for BM25 search
        """
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words (basic list)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _calculate_bm25_score(self, query_terms: Counter, doc_terms: Counter, 
                             doc_length: int, total_docs: int, avg_doc_length: float) -> float:
        """
        Calculate BM25 score for a document
        """
        # Import settings for BM25 parameters
        try:
            from config.settings import settings
            k1 = settings.BM25_K1
            b = settings.BM25_B
        except ImportError:
            k1 = 1.2  # Default BM25 parameter
            b = 0.75   # Default BM25 parameter
        
        score = 0.0
        
        for term, query_freq in query_terms.items():
            if term in doc_terms:
                # Calculate IDF (Inverse Document Frequency)
                doc_freq = doc_terms[term]
                
                # Calculate BM25 score for this term
                numerator = doc_freq * (k1 + 1)
                denominator = doc_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
                
                term_score = (numerator / denominator) * query_freq
                score += term_score
        
        return score
    
    def _get_avg_doc_length(self, documents: List[Dict[str, Any]]) -> float:
        """
        Calculate average document length
        """
        if not documents:
            return 0.0
        
        total_length = sum(len(self._preprocess_text(doc.get('content', ''))) for doc in documents)
        return total_length / len(documents)
    
    def _combine_search_results(self, bm25_results: List[Dict[str, Any]], 
                               vector_results: List[Dict[str, Any]],
                               bm25_weight: float, vector_weight: float) -> List[Dict[str, Any]]:
        """
        Combine BM25 and vector search results
        """
        # Create document ID to result mapping
        bm25_map = {result['document'].get('document_id', str(i)): result for i, result in enumerate(bm25_results)}
        vector_map = {result['document'].get('document_id', str(i)): result for i, result in enumerate(vector_results)}
        
        # Get all unique document IDs
        all_doc_ids = set(bm25_map.keys()) | set(vector_map.keys())
        
        combined_results = []
        
        for doc_id in all_doc_ids:
            bm25_result = bm25_map.get(doc_id, {'bm25_score': 0.0, 'document': None})
            vector_result = vector_map.get(doc_id, {'vector_score': 0.0, 'document': None})
            
            # Normalize scores to 0-1 range
            bm25_score = min(bm25_result['bm25_score'] / 10.0, 1.0) if bm25_result['bm25_score'] > 0 else 0.0
            vector_score = vector_result['vector_score']
            
            # Calculate hybrid score
            hybrid_score = (bm25_weight * bm25_score) + (vector_weight * vector_score)
            
            # Use the document from either result
            document = bm25_result['document'] or vector_result['document']
            
            if document:
                combined_results.append({
                    'document': document,
                    'bm25_score': bm25_score,
                    'vector_score': vector_score,
                    'hybrid_score': hybrid_score,
                    'search_type': 'hybrid'
                })
        
        return combined_results
    
    def find_most_similar(self, query_embedding: List[float], 
                         document_embeddings: List[Dict[str, Any]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar documents to a query (legacy method)
        """
        try:
            similarities = []
            
            for doc in document_embeddings:
                doc_embedding = doc.get('embedding', [])
                if doc_embedding:
                    similarity = self.calculate_similarity(query_embedding, doc_embedding)
                    similarities.append({
                        'document': doc,
                        'similarity': similarity
                    })
            
            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
    
    def is_titan_available(self) -> bool:
        """
        Check if Titan embeddings are available
        """
        return self.titan_available
