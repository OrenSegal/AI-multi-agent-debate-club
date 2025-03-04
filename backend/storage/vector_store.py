import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class ChromaVectorStore:
    """Utility class for storing and retrieving vector embeddings using Chroma."""
    
    def __init__(self, collection_name: str = "debates"):
        """Initialize the Chroma vector store.
        
        Args:
            collection_name: Name of the Chroma collection to use
        """
        self.collection_name = collection_name
        self.persist_directory = os.getenv("VECTOR_DB_PATH", "data/vectordb")
        
        # Ensure the directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        try:
            # Import Chroma and initialize embeddings
            from langchain.vectorstores import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            # Initialize embeddings using OpenRouter
            openai_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenRouter API key not found. Vector store cannot be initialized.")
                
            # Get model name from environment or use default
            model_name = os.getenv("OPENROUTER_MODEL_2", "openrouter/openai/text-embedding-ada-002")
            
            self.embeddings = OpenAIEmbeddings(
                base_url="https://openrouter.ai/api/v1",
                api_key=openai_api_key,
                model_name=model_name
            )
            
            # Initialize or load the vector database
            self.db = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"ChromaDB initialized with collection: {collection_name}")
        except ImportError:
            raise ImportError("Required dependencies not available. Please install chromadb package.")
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to the vector store."""
        if not texts:
            return []
        
        if not ids:
            from uuid import uuid4
            ids = [str(uuid4()) for _ in texts]
            
        if not metadatas:
            metadatas = [{} for _ in texts]
            
        try:
            self.db.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            self.db.persist()
            return ids
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            return []
    
    def search(self, query: str, n_results: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector store."""
        try:
            if filter:
                results = self.db.similarity_search_with_score(query=query, k=n_results, filter=filter)
            else:
                results = self.db.similarity_search_with_score(query=query, k=n_results)
                
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
                
            return formatted_results
        except Exception as e:
            print(f"Error searching in vector store: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.db._collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def delete_collection(self) -> bool:
        """Delete the entire collection."""
        try:
            self.db.delete_collection()
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
