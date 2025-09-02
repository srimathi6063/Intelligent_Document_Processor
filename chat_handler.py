#!/usr/bin/env python3
"""
Simplified Chat Handler without LangChain dependencies
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
import boto3
from botocore.config import Config

# Weaviate imports
try:
    import weaviate
    WEAVIATE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Weaviate not available: {e}")
    WEAVIATE_AVAILABLE = False

# Import existing modules
try:
    from MySQLChatbot.request_handler import handle_user_query as mysql_query_handler
    MYSQL_CHATBOT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MySQL chatbot not available: {e}")
    MYSQL_CHATBOT_AVAILABLE = False

# Import Titan embedding helper
try:
    from utils.embedding_helper import TitanEmbeddingHelper
    TITAN_EMBEDDING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Titan embedding helper not available: {e}")
    TITAN_EMBEDDING_AVAILABLE = False

logger = logging.getLogger(__name__)

class SimpleChatHandler:
    def __init__(self):
        # Initialize AWS Bedrock for LLM with extended timeouts
        try:
            # Configure Bedrock client with extended timeouts
            try:
                from config.settings import settings
                bedrock_config = Config(
                    read_timeout=settings.BEDROCK_READ_TIMEOUT,
                    connect_timeout=settings.BEDROCK_CONNECT_TIMEOUT,
                    retries={'max_attempts': settings.BEDROCK_MAX_RETRIES}
                )
            except ImportError:
                # Fallback configuration if settings not available
                bedrock_config = Config(
                    read_timeout=300,      # 5 minutes for read timeout
                    connect_timeout=60,    # 1 minute for connection timeout
                    retries={'max_attempts': 3}  # Retry up to 3 times
                )
            
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name='us-east-1',
                config=bedrock_config
            )
            logger.info("AWS Bedrock client initialized successfully with extended timeouts")
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}")
            self.bedrock_client = None
        
        # Initialize Titan embedding helper
        try:
            if TITAN_EMBEDDING_AVAILABLE:
                self.titan_embedding = TitanEmbeddingHelper()
                if self.titan_embedding.is_titan_available():
                    logger.info("✅ Titan embedding helper initialized successfully")
                else:
                    logger.warning("⚠️ Titan embedding helper initialized but Titan model not accessible - using fallback embeddings")
            else:
                self.titan_embedding = None
                logger.info("Titan embedding not available")
        except Exception as e:
            logger.warning(f"Titan embedding initialization failed: {e}")
            self.titan_embedding = None
        
        # Initialize Weaviate client
        try:
            if WEAVIATE_AVAILABLE:
                self.weaviate_client = weaviate.Client(url="http://localhost:8080")
                
                # Check if Weaviate is ready
                if self.weaviate_client.is_ready():
                    logger.info("Weaviate server is ready")
                    self._setup_weaviate_schema()
                else:
                    logger.warning("Weaviate server is not ready")
                    self.weaviate_client = None
            else:
                logger.info("Weaviate not available, using in-memory storage")
                self.weaviate_client = None
        except Exception as e:
            logger.warning(f"Weaviate client initialization failed: {e}")
            self.weaviate_client = None
        
        # Simple in-memory document storage (fallback)
        self.documents = {}
        self.document_embeddings = {}  # Store embeddings for in-memory search
        self.chat_history = []
    
    def _setup_weaviate_schema(self):
        """
        Setup Weaviate schema for document storage with Titan embeddings
        """
        try:
            # Define the class schema with Titan embedding support
            class_obj = {
                "class": "Document",
                "description": "A document for summarization queries with Titan embeddings",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The document content"
                    },
                    {
                        "name": "document_id",
                        "dataType": ["text"],
                        "description": "Unique document identifier"
                    },
                    {
                        "name": "uploaded_at",
                        "dataType": ["date"],
                        "description": "When the document was uploaded"
                    },
                    {
                        "name": "embedding",
                        "dataType": ["vector"],
                        "description": "Titan embedding vector",
                        "vectorizer": "none"  # We'll generate embeddings manually
                    }
                ],
                "vectorizer": "none"  # Use no vectorizer, we'll add embeddings manually
            }
            
            # Create the class if it doesn't exist
            try:
                self.weaviate_client.schema.create_class(class_obj)
                logger.info("Weaviate schema created successfully with Titan embedding support")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("Weaviate schema already exists")
                else:
                    logger.error(f"Error creating Weaviate schema: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Error setting up Weaviate schema: {e}")
    
    def process_document_for_chat(self, extracted_text: str, document_id: str) -> None:
        """
        Process and store document in Weaviate with Titan embeddings for summarization queries
        """
        print(f"📄 [DOCUMENT PROCESSING] Processing document for chat: {document_id}")
        print(f"📏 [DOCUMENT PROCESSING] Document length: {len(extracted_text)} characters")
        print(f"📝 [DOCUMENT PROCESSING] Document preview (first 200 chars): {extracted_text[:200]}...")
        
        try:
            # Generate Titan embedding if available
            embedding_vector = None
            if self.titan_embedding:
                try:
                    print(f"🧠 [DOCUMENT PROCESSING] Generating Titan embedding...")
                    embedding_vector = self.titan_embedding.generate_single_embedding(extracted_text)
                    print(f"✅ [DOCUMENT PROCESSING] Titan embedding generated (dimensions: {len(embedding_vector)})")
                except Exception as e:
                    print(f"⚠️ [DOCUMENT PROCESSING] Failed to generate Titan embedding: {e}")
                    embedding_vector = None
            
            # Store in Weaviate if available
            if self.weaviate_client and self.weaviate_client.is_ready():
                print(f"🗄️ [DOCUMENT PROCESSING] Storing document in Weaviate...")
                # Prepare document data
                document_data = {
                    "content": extracted_text,
                    "document_id": document_id,
                    "uploaded_at": "2024-01-01T00:00:00Z"  # You can make this dynamic
                }
                
                # Add to Weaviate with embedding if available
                print(f"🗄️ [DOCUMENT PROCESSING] Attempting to store in Weaviate...")
                if embedding_vector:
                    result = self.weaviate_client.data_object.create(
                        data_object=document_data,
                        class_name="Document",
                        vector=embedding_vector
                    )
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in Weaviate with Titan embedding, ID: {result}")
                else:
                    result = self.weaviate_client.data_object.create(
                        data_object=document_data,
                        class_name="Document"
                    )
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in Weaviate without embedding, ID: {result}")
                
                logger.info(f"Document stored in Weaviate with ID: {result}")
                
                # Verify the document was stored
                try:
                    retrieved = self.weaviate_client.data_object.get_by_id(
                        class_name="Document",
                        uuid=result
                    )
                    if retrieved:
                        print(f"✅ [DOCUMENT PROCESSING] Document verified in Weaviate")
                    else:
                        print(f"⚠️ [DOCUMENT PROCESSING] Document stored but could not be retrieved")
                except Exception as verify_error:
                    print(f"⚠️ [DOCUMENT PROCESSING] Could not verify document storage: {verify_error}")
                
            else:
                print(f"💾 [DOCUMENT PROCESSING] Weaviate not available, storing in memory")
                self.documents[document_id] = extracted_text
                if embedding_vector:
                    self.document_embeddings[document_id] = embedding_vector
                    print(f"✅ [DOCUMENT PROCESSING] Document and embedding stored in memory: {document_id}")
                else:
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in memory: {document_id}")
                    logger.info(f"Document stored in memory: {document_id}")
                
            logger.info(f"Stored document {document_id} for chat (length: {len(extracted_text)} chars)")
            
        except Exception as e:
            logger.error(f"Error storing document for chat: {e}")
            
            # Fallback to in-memory storage
            self.documents[document_id] = extracted_text
            if embedding_vector:
                self.document_embeddings[document_id] = embedding_vector
    
    def process_document_for_chat_with_embedding(self, extracted_text: str, document_id: str, embedding_vector: List[float] = None) -> None:
        """
        Process and store document in Weaviate with pre-generated embedding for summarization queries
        """
        print(f"📄 [DOCUMENT PROCESSING] Processing document with pre-generated embedding: {document_id}")
        print(f"📏 [DOCUMENT PROCESSING] Document length: {len(extracted_text)} characters")
        
        try:
            # Store in Weaviate if available
            if self.weaviate_client and self.weaviate_client.is_ready():
                print(f"🗄️ [DOCUMENT PROCESSING] Storing document in Weaviate with pre-generated embedding...")
                # Prepare document data
                document_data = {
                    "content": extracted_text,
                    "document_id": document_id,
                    "uploaded_at": "2024-01-01T00:00:00Z"  # You can make this dynamic
                }
                
                # Add to Weaviate with pre-generated embedding if available
                if embedding_vector:
                    result = self.weaviate_client.data_object.create(
                        data_object=document_data,
                        class_name="Document",
                        vector=embedding_vector
                    )
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in Weaviate with pre-generated embedding, ID: {result}")
                else:
                    result = self.weaviate_client.data_object.create(
                        data_object=document_data,
                        class_name="Document"
                    )
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in Weaviate without embedding, ID: {result}")
                
                logger.info(f"Document stored in Weaviate with ID: {result}")
                
            else:
                print(f"💾 [DOCUMENT PROCESSING] Weaviate not available, storing in memory")
                self.documents[document_id] = extracted_text
                if embedding_vector:
                    self.document_embeddings[document_id] = embedding_vector
                    print(f"✅ [DOCUMENT PROCESSING] Document and pre-generated embedding stored in memory: {document_id}")
                else:
                    print(f"✅ [DOCUMENT PROCESSING] Document stored in memory: {document_id}")
                
            logger.info(f"Stored document {document_id} for chat with pre-generated embedding (length: {len(extracted_text)} chars)")
            
        except Exception as e:
            logger.error(f"Error storing document for chat with pre-generated embedding: {e}")
            
            # Fallback to in-memory storage
            self.documents[document_id] = extracted_text
            if embedding_vector:
                self.document_embeddings[document_id] = embedding_vector
    
    def hybrid_search(self, query: str, limit: int = None, 
                     bm25_weight: float = None, vector_weight: float = None) -> List[str]:
        # Use settings if not provided
        try:
            from config.settings import settings
            if limit is None:
                limit = settings.HYBRID_SEARCH_K
            if bm25_weight is None:
                bm25_weight = settings.BM25_WEIGHT
            if vector_weight is None:
                vector_weight = settings.VECTOR_WEIGHT
        except ImportError:
            if limit is None:
                limit = 3
            if bm25_weight is None:
                bm25_weight = 0.5
            if vector_weight is None:
                vector_weight = 0.5
        print(f"🔍 [HYBRID SEARCH] Starting hybrid search for query: '{query}'")
        print(f"📊 [HYBRID SEARCH] Search limit: {limit}")
        print(f"⚖️ [HYBRID SEARCH] Weights - BM25: {bm25_weight}, Vector: {vector_weight}")
        
        try:
            # Generate query embedding if Titan is available
            query_embedding = None
            if self.titan_embedding:
                try:
                    print(f"🧠 [HYBRID SEARCH] Generating query embedding...")
                    query_embedding = self.titan_embedding.generate_single_embedding(query)
                    print(f"✅ [HYBRID SEARCH] Query embedding generated (dimensions: {len(query_embedding)})")
                except Exception as e:
                    print(f"⚠️ [HYBRID SEARCH] Failed to generate query embedding: {e}")
                    query_embedding = None
            
            # Try Weaviate hybrid search first
            if self.weaviate_client and self.weaviate_client.is_ready():
                try:
                    print(f"🔍 [HYBRID SEARCH] Performing hybrid search in Weaviate...")
                    
                    # Get all documents from Weaviate
                    response = (
                        self.weaviate_client.query
                        .get("Document", ["content", "document_id", "uploaded_at"])
                        .with_limit(50)  # Get more documents for hybrid search
                        .do()
                    )
                    
                    if response and "data" in response and "Get" in response["data"] and "Document" in response["data"]["Get"]:
                        weaviate_documents = response["data"]["Get"]["Document"]
                        print(f"📄 [HYBRID SEARCH] Retrieved {len(weaviate_documents)} documents from Weaviate")
                        
                        # Prepare documents for hybrid search
                        documents_for_search = []
                        for doc in weaviate_documents:
                            doc_data = {
                                'document_id': doc.get("document_id", "unknown"),
                                'content': doc.get("content", ""),
                                'uploaded_at': doc.get("uploaded_at", "")
                            }
                            documents_for_search.append(doc_data)
                        
                        # Perform hybrid search using Titan helper
                        if self.titan_embedding and query_embedding:
                            hybrid_results = self.titan_embedding.hybrid_search(
                                query, documents_for_search, query_embedding, 
                                bm25_weight, vector_weight, limit
                            )
                            
                            results = []
                            for i, result in enumerate(hybrid_results):
                                doc = result['document']
                                hybrid_score = result['hybrid_score']
                                bm25_score = result.get('bm25_score', 0)
                                vector_score = result.get('vector_score', 0)
                                content = doc['content']
                                doc_id = doc['document_id']
                                
                                # Extract a snippet around the most relevant part
                                best_snippet = self._extract_best_snippet(content, query.lower().split())
                                
                                results.append(f"[Document: {doc_id}] (hybrid: {hybrid_score:.3f}, BM25: {bm25_score:.3f}, Vector: {vector_score:.3f}) {best_snippet}")
                                
                                print(f"📄 [HYBRID SEARCH] Document {i+1}: {doc_id}")
                                print(f"📊 [HYBRID SEARCH] Scores - Hybrid: {hybrid_score:.3f}, BM25: {bm25_score:.3f}, Vector: {vector_score:.3f}")
                                print(f"📏 [HYBRID SEARCH] Content length: {len(content)} characters")
                                print(f"📝 [HYBRID SEARCH] Snippet: {best_snippet}")
                            
                            logger.info(f"Found {len(results)} relevant documents via Weaviate hybrid search")
                            return results
                        else:
                            print(f"⚠️ [HYBRID SEARCH] Titan embedding not available, falling back to BM25 search")
                            return self._bm25_search_fallback(query, limit, documents_for_search)
                    
                except Exception as e:
                    logger.warning(f"Weaviate hybrid search failed: {e}")
                    print(f"⚠️ [HYBRID SEARCH] Weaviate hybrid search failed, falling back to in-memory search")
            
            # Fallback to in-memory hybrid search
            if self.documents:
                print(f"🔄 [HYBRID SEARCH] Using in-memory hybrid search")
                
                # Prepare documents with embeddings for in-memory search
                documents_for_search = []
                for doc_id, content in self.documents.items():
                    doc_data = {
                        'document_id': doc_id,
                        'content': content
                    }
                    
                    # Add embedding if available
                    if doc_id in self.document_embeddings:
                        doc_data['embedding'] = self.document_embeddings[doc_id]
                    
                    documents_for_search.append(doc_data)
                
                if documents_for_search:
                    # Perform hybrid search using Titan helper
                    if self.titan_embedding and query_embedding:
                        hybrid_results = self.titan_embedding.hybrid_search(
                            query, documents_for_search, query_embedding, 
                            bm25_weight, vector_weight, limit
                        )
                        
                        results = []
                        for i, result in enumerate(hybrid_results):
                            doc = result['document']
                            hybrid_score = result['hybrid_score']
                            bm25_score = result.get('bm25_score', 0)
                            vector_score = result.get('vector_score', 0)
                            content = doc['content']
                            doc_id = doc['document_id']
                            
                            # Extract a snippet around the most relevant part
                            best_snippet = self._extract_best_snippet(content, query.lower().split())
                            
                            results.append(f"[Document: {doc_id}] (hybrid: {hybrid_score:.3f}, BM25: {bm25_score:.3f}, Vector: {vector_score:.3f}) {best_snippet}")
                            
                            print(f"📄 [HYBRID SEARCH] Document {i+1}: {doc_id}")
                            print(f"📊 [HYBRID SEARCH] Scores - Hybrid: {hybrid_score:.3f}, BM25: {bm25_score:.3f}, Vector: {vector_score:.3f}")
                            print(f"📏 [HYBRID SEARCH] Content length: {len(content)} characters")
                            print(f"📝 [HYBRID SEARCH] Snippet: {best_snippet}")
                        
                        logger.info(f"Found {len(results)} relevant documents via in-memory hybrid search")
                        return results
                    else:
                        print(f"⚠️ [HYBRID SEARCH] Titan embedding not available, falling back to BM25 search")
                        return self._bm25_search_fallback(query, limit, documents_for_search)
            
            # Final fallback to simple text search
            print(f"🔄 [HYBRID SEARCH] No documents available, falling back to simple text search")
            return self._simple_text_search_fallback(query, limit)
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return self._simple_text_search_fallback(query, limit)
    
    def _bm25_search_fallback(self, query: str, limit: int, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Fallback to BM25 search when vector search is not available
        """
        print(f"🔍 [BM25 FALLBACK] Using BM25 keyword search")
        
        try:
            if self.titan_embedding:
                bm25_results = self.titan_embedding.bm25_search(query, documents, limit)
                
                results = []
                for i, result in enumerate(bm25_results):
                    doc = result['document']
                    bm25_score = result['bm25_score']
                    content = doc['content']
                    doc_id = doc['document_id']
                    
                    # Extract a snippet around the most relevant part
                    best_snippet = self._extract_best_snippet(content, query.lower().split())
                    
                    results.append(f"[Document: {doc_id}] (BM25: {bm25_score:.3f}) {best_snippet}")
                    
                    print(f"📄 [BM25 FALLBACK] Document {i+1}: {doc_id} (BM25 score: {bm25_score:.3f})")
                    print(f"📏 [BM25 FALLBACK] Content length: {len(content)} characters")
                    print(f"📝 [BM25 FALLBACK] Snippet: {best_snippet}")
                
                logger.info(f"Found {len(results)} relevant documents via BM25 search")
                return results
            else:
                return self._simple_text_search_fallback(query, limit)
                
        except Exception as e:
            logger.error(f"Error in BM25 fallback search: {e}")
            return self._simple_text_search_fallback(query, limit)
    
    def semantic_search(self, query: str, limit: int = 3) -> List[str]:
        """
        Legacy method - now calls hybrid search
        """
        return self.hybrid_search(query, limit)
    
    def _simple_text_search_fallback(self, query: str, limit: int = 3) -> List[str]:
        """
        Fallback to simple text-based search when embeddings are not available
        """
        print(f"🔍 [TEXT SEARCH] Using simple text search fallback")
        
        try:
            # Try Weaviate text search first
            if self.weaviate_client and self.weaviate_client.is_ready():
                try:
                    print(f"🔍 [TEXT SEARCH] Searching Weaviate for query: '{query}'")
                    
                    # Get all documents and filter by relevance
                    response = (
                        self.weaviate_client.query
                        .get("Document", ["content", "document_id"])
                        .with_limit(50)  # Get more documents to filter from
                        .do()
                    )
                    
                except Exception as e:
                    logger.warning(f"Weaviate search failed: {e}")
                    response = None
                
                if response and "data" in response and "Get" in response["data"] and "Document" in response["data"]["Get"]:
                    documents = response["data"]["Get"]["Document"]
                    print(f"📄 [TEXT SEARCH] Retrieved {len(documents)} documents from Weaviate")
                    
                    # Filter documents by relevance to the query
                    relevant_documents = []
                    query_words = query.lower().split()
                    
                    for doc in documents:
                        content = doc.get("content", "")
                        doc_id = doc.get("document_id", "unknown")
                        
                        # Calculate relevance score
                        content_lower = content.lower()
                        matches = sum(1 for word in query_words if word in content_lower)
                        
                        if matches > 0:
                            # Calculate relevance score (more matches = higher score)
                            relevance_score = matches / len(query_words)
                            relevant_documents.append({
                                'doc': doc,
                                'score': relevance_score,
                                'matches': matches
                            })
                    
                    # Sort by relevance score (highest first)
                    relevant_documents.sort(key=lambda x: x['score'], reverse=True)
                    
                    print(f"📊 [TEXT SEARCH] Found {len(relevant_documents)} relevant documents")
                    
                    results = []
                    for i, item in enumerate(relevant_documents[:limit]):
                        doc = item['doc']
                        content = doc.get("content", "")
                        doc_id = doc.get("document_id", "unknown")
                        score = item['score']
                        matches = item['matches']
                        
                        # Extract a snippet around the best match
                        best_snippet = self._extract_best_snippet(content, query_words)
                        
                        results.append(f"[Document: {doc_id}] {best_snippet}")
                        
                        print(f"📄 [TEXT SEARCH] Document {i+1}: {doc_id} (score: {score:.2f}, matches: {matches})")
                        print(f"📏 [TEXT SEARCH] Content length: {len(content)} characters")
                        print(f"📝 [TEXT SEARCH] Snippet: {best_snippet}")
                    
                    logger.info(f"Found {len(results)} relevant documents via Weaviate text search")
                    return results
                else:
                    logger.info("No results from Weaviate, falling back to in-memory search")
            
            # Fallback to in-memory text search
            if not self.documents:
                print(f"❌ [TEXT SEARCH] No documents available for search")
                logger.info("No documents available for search")
                return []
            
            print(f"🔄 [TEXT SEARCH] Using in-memory text search")
            print(f"📚 [TEXT SEARCH] Available documents: {list(self.documents.keys())}")
            
            # Simple keyword matching
            query_words = query.lower().split()
            print(f"🔍 [TEXT SEARCH] Search keywords: {query_words}")
            results = []
            
            for doc_id, content in self.documents.items():
                content_lower = content.lower()
                matches = sum(1 for word in query_words if word in content_lower)
                print(f"📄 [TEXT SEARCH] Document {doc_id}: {matches} keyword matches")
                
                if matches > 0:
                    # Extract a snippet around the first match
                    for word in query_words:
                        if word in content_lower:
                            start = max(0, content_lower.find(word) - 100)
                            end = min(len(content), content_lower.find(word) + 300)
                            snippet = content[start:end]
                            results.append(f"[Document: {doc_id}] {snippet}")
                            print(f"📝 [TEXT SEARCH] Found match for '{word}' in {doc_id}")
                            print(f"📄 [TEXT SEARCH] Snippet: {snippet}")
                            break
                    
                    if len(results) >= limit:
                        break
            
            print(f"✅ [TEXT SEARCH] Found {len(results)} documents via in-memory search")
            logger.info(f"Found {len(results)} documents via in-memory search")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in text search fallback: {e}")
            return []
    
    def simple_text_search(self, query: str, limit: int = 3) -> List[str]:
        """
        Legacy method - now calls hybrid search
        """
        return self.hybrid_search(query, limit)
    
    def _extract_best_snippet(self, content: str, query_words: List[str]) -> str:
        """Extract the best snippet around the most relevant part of the content"""
        try:
            content_lower = content.lower()
            best_position = -1
            best_score = 0
            
            # Find the position with the most query word matches
            for i in range(0, len(content) - 200, 50):  # Check every 50 characters
                snippet = content_lower[i:i+400]  # 400 character window
                matches = sum(1 for word in query_words if word in snippet)
                
                if matches > best_score:
                    best_score = matches
                    best_position = i
            
            if best_position >= 0:
                # Extract snippet around the best position
                start = max(0, best_position - 100)
                end = min(len(content), best_position + 400)
                snippet = content[start:end]
                
                # Clean up the snippet
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                
                return snippet
            else:
                # Fallback to first 300 characters
                return content[:300] + "..." if len(content) > 300 else content
                
        except Exception as e:
            logger.error(f"Error extracting snippet: {e}")
            return content[:300] + "..." if len(content) > 300 else content
    
    def handle_invoice_query(self, query: str) -> Dict[str, Any]:
        """
        Handle invoice-related queries using MySQL database
        """
        logger.info(f"🔍 Processing invoice query: '{query}'")
        
        if not MYSQL_CHATBOT_AVAILABLE:
            logger.error("❌ MySQL chatbot not available")
            return {
                "success": False,
                "response": "MySQL chatbot not available. Please ensure all dependencies are installed.",
                "database": "MySQL"
            }
            
        try:
            logger.info("📞 Calling MySQL query handler...")
            # Use existing MySQL query handler
            result = mysql_query_handler(query)
            logger.info(f"📊 MySQL handler result: {result}")
            
            if "error" in result:
                logger.error(f"❌ MySQL handler returned error: {result['error']}")
                return {
                    "success": False,
                    "response": f"Error processing invoice query: {result['error']}",
                    "database": "MySQL"
                }
            
            # Format the response
            if "result" in result and "rows" in result["result"]:
                rows = result["result"]["rows"]
                if rows:
                    # Format as table-like response
                    response = "Here are the results from the invoice database:\n\n"
                    for row in rows[:10]:  # Limit to 10 rows
                        response += f"{', '.join(str(cell) for cell in row)}\n"
                    
                    if len(rows) > 10:
                        response += f"\n... and {len(rows) - 10} more records."
                else:
                    response = "No matching records found in the invoice database."
            else:
                response = "Query executed successfully, but no data was returned."
            
            return {
                "success": True,
                "response": response,
                "database": "MySQL",
                "sql": result.get("sql", ""),
                "corrected": result.get("corrected", False)
            }
            
        except Exception as e:
            logger.error(f"Error handling invoice query: {e}")
            return {
                "success": False,
                "response": f"Error processing invoice query: {str(e)}",
                "database": "MySQL"
            }
    
    def handle_summarization_query(self, query: str) -> Dict[str, Any]:
        """
        Handle summarization queries using Weaviate vector search and LLM
        """
        if not self.bedrock_client:
            return {
                "success": False,
                "response": "AWS Bedrock not available. Please check your AWS credentials and configuration.",
                "database": "Documents"
            }
            
        try:
            # Search for relevant content using Weaviate or fallback
            relevant_snippets = self.simple_text_search(query, limit=3)
            
            if not relevant_snippets:
                return {
                    "success": True,
                    "response": "I don't have enough information in the uploaded documents to answer this question. Please upload relevant documents or ask a different question.",
                    "database": "Documents",
                    "snippets_used": 0,
                    "context_length": 0
                }
            
            # Build context from relevant snippets
            context = "\n\n".join(relevant_snippets)
            print(f"🔧 [SUMMARIZATION] Built context from {len(relevant_snippets)} snippets")
            print(f"📏 [SUMMARIZATION] Context length: {len(context)} characters")
            print(f"📄 [SUMMARIZATION] Context preview (first 500 chars): {context[:500]}...")
            
            # Check if the context is actually relevant to the query
            relevance_prompt = f"""
            Analyze if the following document content is relevant to the user's question.
            
            Document Content:
            {context}
            
            User Question: {query}
            
            Determine if the document content contains information that can answer the user's question.
            Consider:
            1. Does the content mention topics related to the question?
            2. Does it contain facts, data, or explanations that address the question?
            3. Is the content specific enough to provide a meaningful answer?
            4. Are there any keywords or terms that match the question?
            
            IMPORTANT: Be generous in determining relevance. If there are ANY related terms, concepts, or information that could help answer the question, mark it as RELEVANT.
            
            Respond with only "RELEVANT" if the content is relevant, or "NOT_RELEVANT" if it's completely unrelated.
            """
            
            try:
                relevance_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [
                        {
                            "role": "user",
                            "content": relevance_prompt
                        }
                    ],
                    "max_tokens": 50,
                    "temperature": 0,
                    "top_k": 250,
                    "top_p": 1.0,
                    "stop_sequences": []
                }

                relevance_response = self.bedrock_client.invoke_model(
                    modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps(relevance_body)
                )

                relevance_result = json.loads(relevance_response['body'].read())
                relevance_text = relevance_result['content'][0]['text'].strip().upper()
                
                if "NOT_RELEVANT" in relevance_text:
                    # Double-check: if we found relevant snippets, they should be relevant
                    # This prevents false negatives from the LLM relevance check
                    if len(relevant_snippets) > 0:
                        print(f"⚠️ [SUMMARIZATION] LLM marked content as NOT_RELEVANT, but we found {len(relevant_snippets)} relevant snippets. Proceeding anyway.")
                        logger.warning(f"LLM relevance check returned NOT_RELEVANT but found {len(relevant_snippets)} relevant snippets. Proceeding with answer generation.")
                    else:
                        return {
                            "success": True,
                            "response": "I don't have enough information in the uploaded documents to answer this question. Please upload relevant documents or ask a different question.",
                            "database": "Documents",
                            "snippets_used": len(relevant_snippets),
                            "context_length": len(context)
                        }
                    
            except Exception as e:
                logger.warning(f"Relevance check failed, proceeding with answer generation: {e}")
            
            # Create prompt for Claude
            prompt = f"""
            Based on the following document context, please answer the user's question.
            
            Context:
            {context}
            
            User Question: {query}
            
            Please provide a comprehensive and accurate answer based on the context provided.
            If the context doesn't contain enough information to answer the question, respond with: "I don't have enough information in the uploaded documents to answer this question. Please upload relevant documents or ask a different question."
            """
            
            print(f"🤖 [SUMMARIZATION] Creating prompt for Claude...")
            print(f"📊 [SUMMARIZATION] Prompt length: {len(prompt)} characters")
            print(f"📝 [SUMMARIZATION] User question: {query}")
            
            # Call Claude via Bedrock for summarization (not structured extraction)
            try:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0,
                    "top_k": 250,
                    "top_p": 1.0,
                    "stop_sequences": []
                }

                response = self.bedrock_client.invoke_model(
                    modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps(body)
                )

                response_body = json.loads(response['body'].read())
                response = response_body['content'][0]['text'].strip()
                print(f"✅ [SUMMARIZATION] Claude response received")
                print(f"📏 [SUMMARIZATION] Response length: {len(response)} characters")
                print(f"📄 [SUMMARIZATION] Response preview (first 300 chars): {response[:300]}...")
                
            except Exception as e:
                print(f"❌ [SUMMARIZATION] Error calling Claude: {e}")
                logger.error(f"Error calling Claude for summarization: {e}")
                response = "Sorry, I couldn't process your request at the moment."
            
            return {
                "success": True,
                "response": response,
                "database": "Documents",
                "snippets_used": len(relevant_snippets),
                "context_length": len(context)
            }
            
        except Exception as e:
            logger.error(f"Error handling summarization query: {e}")
            return {
                "success": False,
                "response": f"Error processing summarization query: {str(e)}",
                "database": "Documents"
            }
    
    def handle_chat_query(self, message: str, database_type: str) -> Dict[str, Any]:
        """
        Main chat query handler
        """
        logger.info(f"Main chat query handler called")
        logger.info(f"Message: '{message}'")
        logger.info(f"Database type: '{database_type}'")
        
        try:
            # Add to chat history
            try:
                timestamp = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
            except RuntimeError:
                timestamp = 0
                
            self.chat_history.append({
                "message": message,
                "database_type": database_type,
                "timestamp": timestamp
            })
            
            logger.info(f"Chat history updated, total messages: {len(self.chat_history)}")
            
            # Route to appropriate handler
            if database_type.lower() == "invoice":
                logger.info("Routing to invoice query handler")
                return self.handle_invoice_query(message)
            elif database_type.lower() == "summarization":
                logger.info("Routing to summarization query handler")
                return self.handle_summarization_query(message)
            else:
                logger.error(f"Unknown database type: {database_type}")
                return {
                    "success": False,
                    "response": f"Unknown database type: {database_type}. Please select 'Invoice' or 'Summarization'.",
                    "database": "Unknown"
                }
                
        except Exception as e:
            logger.error(f"Error in chat query handler: {e}")
            return {
                "success": False,
                "response": f"An error occurred while processing your request: {str(e)}",
                "database": database_type
            }
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Get chat history
        """
        return self.chat_history.copy()
    
    def clear_chat_history(self) -> bool:
        """
        Clear chat history
        """
        try:
            self.chat_history.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            return False

# Global chat handler instance
chat_handler = SimpleChatHandler()
