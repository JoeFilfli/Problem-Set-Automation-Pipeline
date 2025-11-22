"""
Vector store management using ChromaDB for RAG.
"""
from typing import Any, Dict, List
from openai import OpenAI
import chromadb
from dotenv import load_dotenv
from models import Chunk

# Load environment variables
load_dotenv(override=True)


class RAGVectorStore:
    """Manages embedding generation and vector storage using ChromaDB."""
    
    def __init__(self, db_path="rag_db"):
        self.client = OpenAI()
        
        # Initialize ChromaDB with automatic fallback to in-memory on corruption
        import os
        
        # Check for environment variable to force in-memory mode
        use_memory = os.environ.get("CHROMA_USE_MEMORY", "false").lower() == "true"
        
        if use_memory:
            print("   [INFO] Using in-memory ChromaDB (CHROMA_USE_MEMORY=true)")
            print("   [NOTE] Data will not persist between server restarts")
            self.chroma = chromadb.Client()
        else:
            # Try persistent client with error handling
            # Note: Rust panics cannot be caught, but ChromaDB converts them to ValueError
            abs_db_path = os.path.abspath(db_path)
            os.makedirs(abs_db_path, exist_ok=True)
            
            try:
                self.chroma = chromadb.PersistentClient(path=abs_db_path)
                # Test it works
                _ = self.chroma.list_collections()
            except (ValueError, AttributeError) as e:
                # ChromaDB converted panic to ValueError - switch to in-memory
                error_str = str(e).lower()
                if any(kw in error_str for kw in ["tenant", "bindings", "could not connect", "does not exist"]):
                    print("   [WARNING] Persistent database failed, automatically using in-memory mode")
                    print(f"   [ERROR] {str(e)[:150]}")
                    self.chroma = chromadb.Client()
                else:
                    raise
            except Exception as e:
                # Any other error - also try in-memory as fallback
                error_str = str(e).lower()
                if "panic" in error_str or "range" in error_str:
                    print("   [WARNING] Database corruption detected, using in-memory mode")
                    self.chroma = chromadb.Client()
                else:
                    raise
        
        self.collection = self.chroma.get_or_create_collection(
            name="course_materials",
            metadata={"hnsw:space": "cosine"},
        )

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI's text-embedding-3-large model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        print(f"   [OpenAI] Embedding request ({len(text)} chars)...")
        res = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        print(f"   [OpenAI] Embedding received (dim={len(res.data[0].embedding)})")
        return res.data[0].embedding

    def add_chunk(self, chunk: Chunk, doc_id: str, chunk_id: str):
        """
        Add a chunk to the vector store.
        
        Args:
            chunk: The Chunk object to store
            doc_id: Document identifier (e.g., filename)
            chunk_id: Unique identifier for this chunk
        """
        print(f"   [VectorDB] Adding {chunk_id}...")
        emb = self.embed(chunk.formatted)
        
        # Convert topics list to comma-separated string for ChromaDB metadata
        topics_str = ", ".join(chunk.topics) if chunk.topics else ""
        
        self.collection.add(
            ids=[chunk_id],
            embeddings=[emb],
            metadatas=[{
                "doc_id": doc_id,
                "summary": chunk.summary,
                "topics": topics_str,
                "start": chunk.start,
                "end": chunk.end,
            }],
            documents=[chunk.formatted]
        )
        print(f"   [VectorDB] Stored {chunk_id}")

    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document has already been ingested.
        
        Args:
            doc_id: Document identifier to check
            
        Returns:
            True if document exists, False otherwise
        """
        results = self.collection.get(
            where={"doc_id": doc_id},
            limit=1
        )
        return len(results["ids"]) > 0

    def delete_document(self, doc_id: str) -> None:
        """
        Remove all chunks associated with a document.
        
        Args:
            doc_id: Document identifier to delete
        """
        self.collection.delete(where={"doc_id": doc_id})

    def get_chunks_for_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieve all stored chunks for a document.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Raw ChromaDB get() response containing ids, documents, and metadata
        """
        return self.collection.get(where={"doc_id": doc_id})

    def query_by_document(self, query: str, doc_id: str, top_k=4):
        """
        Query the vector store for relevant chunks from a specific document.
        
        Args:
            query: The search query
            doc_id: Document identifier to filter by
            top_k: Number of results to return
            
        Returns:
            Query results from ChromaDB filtered by document
        """
        emb = self.embed(query)
        return self.collection.query(
            query_embeddings=[emb],
            n_results=top_k,
            where={"doc_id": doc_id}
        )
    
    def get_all_documents(self):
        """
        Get list of all unique document IDs in the vector store.
        
        Returns:
            List of unique document identifiers
        """
        all_items = self.collection.get()
        doc_ids = set([meta["doc_id"] for meta in all_items["metadatas"]])
        return sorted(list(doc_ids))

    def query(self, query: str, top_k=4):
        """
        Query the vector store for relevant chunks.
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            Query results from ChromaDB
        """
        emb = self.embed(query)
        return self.collection.query(query_embeddings=[emb], n_results=top_k)
