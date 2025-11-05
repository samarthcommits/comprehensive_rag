from abc import ABC, abstractmethod
from typing import List, Optional

class vector_stores:
    def __init__(self):
        pass
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None, vectorstore_type: Optional[str] = None) -> None:
        """Add texts to the vector store with optional metadata."""

        if not texts:
            return
        
        if vectorstore_type is None:
            vectorstore_type = "default"
        elif vectorstore_type=='chroma':
            
        raise NotImplementedError("This method should be overridden by subclasses.")
