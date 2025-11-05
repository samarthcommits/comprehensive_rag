import os

if "CO_API_KEY" not in os.environ:
    os.environ["CO_API_KEY"] = 'zf6XEllXJAVKyHmUY0QP6OQmpSlwAFXvSBjKFJYS'
from vector_store_controller.chroma_db import ChromaDB
from vector_store_controller.milvus_db import MilvusDB, MilvusDB_ANN
from chunking.recursive_char import RecursiveChunker
from Retrievers.reranking_retrieval import Rerank

class DenseRetrieval:
    
    def __init__(self, path = r'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\vectorstores', collection_name = 'collect_chroma1', database = 'milvus', user_name = 'default', existing = False): 
        if database=='milvus':
            self.dense = MilvusDB(collection_name=collection_name, user_name=user_name)
        else:
            self.dense = ChromaDB(collection_name=collection_name, persist_directory=path)
        self.retriever = self.dense.client.as_retriever(search_kwargs = {'k':3})
        

    def chunk(self, text, chunking_strategy = None, pdf = None):
        ch = RecursiveChunker()
        return ch.create_chunks_basic(texts=text, pdf=pdf)

    
    def get_retriever(self, raw_text = '', chunking_strategy = None, rerank = False, pdf = None, docs = None):
        # if raw_text!='' or pdf:
        if not docs:
            self.dense.add_text_docs(self.chunk([raw_text], pdf=pdf))
        else:
            self.dense.add_text_docs(docs)
        if rerank:
            rr = Rerank(self.retriever)
            self.retriever = rr.reranking_retreiver()
        return self.retriever


    