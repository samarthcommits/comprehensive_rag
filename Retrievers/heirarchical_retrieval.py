from vector_store_controller.chroma_db import ChromaDB, ChromaDB_Heirarchy
import os
if "CO_API_KEY" not in os.environ:
    os.environ["CO_API_KEY"] = 'zf6XEllXJAVKyHmUY0QP6OQmpSlwAFXvSBjKFJYS'
from chunking.recursive_char import RecursiveChunker, RecursiveCharacterTextSplitter
from Retrievers.reranking_retrieval import Rerank
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_core.documents import Document
from vector_store_controller.milvus_db import MilvusDB
from uuid import uuid4



class Parent_retrieval:
    def __init__(self, path = r'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\vectorstores', collection_name = 'collect_chroma1', username = 'default', auto_id = False): 
        # self.dense = ChromaDB_Heirarchy(collection_name=collection_name, persist_directory=path)
        self.dense = MilvusDB(collection_name=collection_name, user_name=username, auto_id=auto_id)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap = 5)
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 50)

        # self.retriever = self.dense.client.as_retriever()

    def chunk(self, text, chunking_strategy = None):
        # ch = RecursiveChunker()
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=20, chunk_overlap = 5)
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap = 50)

        # return ch.create_chunks_basic(text)
    
    def get_retriever(self, raw_text = '', chunking_strategy = None, rerank = False):
        self.chunk(text=raw_text)
        store = InMemoryStore()
        self.retriever = ParentDocumentRetriever(
                    vectorstore=self.dense.client,
                    docstore=store,
                    child_splitter=self.child_splitter,
                    parent_splitter=self.parent_splitter
                )
        if rerank:
            rr = Rerank(self.retriever)
            self.retriever = rr.reranking_retreiver()
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        doc = Document(raw_text)
        doc.metadata['pk'] = '34'
        doc.id = str('1')
        doc.metadata['pages'] = '[]'
        doc.metadata['pdf_name'] = ''
        # doc.metadata['pk']
        self.retriever.add_documents(documents=[Document(page_content=raw_text)])


        return self.retriever


