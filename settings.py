# import os
# from pathlib import Path
# from dotenv import load_dotenv

# # Load environment variables from a .env file if present
# load_dotenv()

# # Cache directory path where processed document chunks will be stored
# CACHE_DIR = os.getenv("CACHE_DIR", "data/cache")

# # Cache expiration time in days after which cached files are invalid
# CACHE_EXPIRE_DAYS = int(os.getenv("CACHE_EXPIRE_DAYS", 7))

# # Chroma DB persistence directory
# CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db")

# # Vector search number of results to retrieve
# VECTOR_SEARCH_K = int(os.getenv("VECTOR_SEARCH_K", 5))

# # Weights for hybrid retriever components (BM25, Vector)
# # Sum should ideally be 1.0
# HYBRID_RETRIEVER_WEIGHTS = {
#     "BM25Retriever": 0.4,
#     "VectorRetriever": 0.6,
# }



# # Server host and port for deployment (used in app.py)
# SERVER_NAME = os.getenv("SERVER_NAME", "127.0.0.1")
# SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))


# # You can add other relevant settings as needed
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

class Settings:
    # Cache directory path where processed document chunks will be stored
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "data/cache"))

    # Cache expiration time in days after which cached files are invalid
    CACHE_EXPIRE_DAYS: int = int(os.getenv("CACHE_EXPIRE_DAYS", "7"))

    # Chroma DB persistence directory for vector store
    CHROMA_DB_PATH: Path = Path(os.getenv("CHROMA_DB_PATH", "data/chroma_db"))

    # Hybrid search configuration
    HYBRID_SEARCH_K: int = int(os.getenv("HYBRID_SEARCH_K", "5"))
    
    # Weights for hybrid search components (BM25, Vector)
    # Sum should ideally be 1.0
    BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.5"))
    VECTOR_WEIGHT: float = float(os.getenv("VECTOR_WEIGHT", "0.5"))
    
    # BM25 search parameters
    BM25_K1: float = float(os.getenv("BM25_K1", "1.2"))
    BM25_B: float = float(os.getenv("BM25_B", "0.75"))

    # AWS Bedrock timeout configuration
    BEDROCK_READ_TIMEOUT: int = int(os.getenv("BEDROCK_READ_TIMEOUT", "300"))  # 5 minutes
    BEDROCK_CONNECT_TIMEOUT: int = int(os.getenv("BEDROCK_CONNECT_TIMEOUT", "60"))  # 1 minute
    BEDROCK_MAX_RETRIES: int = int(os.getenv("BEDROCK_MAX_RETRIES", "3"))
    
    # Titan embedding timeout configuration
    TITAN_READ_TIMEOUT: int = int(os.getenv("TITAN_READ_TIMEOUT", "120"))  # 2 minutes
    TITAN_CONNECT_TIMEOUT: int = int(os.getenv("TITAN_CONNECT_TIMEOUT", "30"))  # 30 seconds
    TITAN_MAX_RETRIES: int = int(os.getenv("TITAN_MAX_RETRIES", "2"))

    # Server host and port for deployment (used in app.py)
    SERVER_NAME: str = os.getenv("SERVER_NAME", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "9000"))

    OCR_DPI = 200  # Balance between speed and accuracy
    MAX_OCR_PAGES = 10  # Don't attempt OCR on large scanned documents
    ENABLE_TABLE_EXTRACTION = True  # Can disable if tables aren't needed

    # Email Configuration
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'uniwareaitest@gmail.com',
        'sender_password': 'ywem uvbk fvbg yqzr',
        'recipient_email': 'srimathi.s@uniware.net'
    }
    


# Create a singleton settings instance
settings = Settings()
