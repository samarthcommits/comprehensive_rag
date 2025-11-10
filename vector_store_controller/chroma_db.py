from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from uuid import uuid4
import os

class ChromaDB:
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url=f"{os.environ.get('OLLAMA_API_ADDRESS')}") 
    def __init__(self, persist_directory: str = rf"{os.environ.get('PATH_TO_CHROMA_VEC_STORE')}", collection_name: str = "default_collection"):
        self.client = Chroma(embedding_function=self.embeddings, persist_directory=persist_directory+rf'\{collection_name}', collection_name=collection_name)
    
    def add_text_docs(self, texts, metadatas=None):
        uuids = [str(uuid4()) for _ in range(len(texts))]

        self.client.add_documents(documents=texts, ids = uuids)
    
class ChromaDB_Heirarchy(ChromaDB):
    def __init__(self, collection_name = 'default_name', persist_directory: str = rf"{os.environ.get('PATH_TO_CHROMA_VEC_STORE')}"):
        self.client = Chroma(embedding_function=self.embeddings, collection_name=collection_name, persist_directory=persist_directory+rf'{collection_name}')
        # pass