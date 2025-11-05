from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

class FaissDB:
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url="http://10.10.64.25:11434") 
    def __init__(self, index_path: str = r'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\vectorstores\faiss_index'):
        self.client = FAISS.load_local(index_path, self.embeddings)

    def add_texts(self, texts, metadatas=None):
        self.client.add_texts(texts=texts, metadatas=metadatas)