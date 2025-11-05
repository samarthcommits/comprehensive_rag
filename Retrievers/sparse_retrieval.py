from langchain_community.retrievers import (
    QdrantSparseVectorRetriever,
)
from pymilvus import db, connections, utility
from qdrant_client.http import models as rest
import os
import ast
from langchain_core.documents import Document
from langchain_milvus.utils.sparse import BM25SparseEmbedding
from vector_store_controller.milvus_db import Milvus, MilvusDB, MilvusDB_ANN, MilvusDB_Sparse
from langchain_milvus.utils.sparse import BM25SparseEmbedding
import random
from Retrievers.SparseEmbeddings import sparse_embed
from qdrant_client import models
from langchain_qdrant import FastEmbedSparse
from vector_store_controller.qdrant_db import QdrantDB_Sparse
from chunking.recursive_char import RecursiveChunker, TokenTextSplitter
class SparseRetriever:
    def __init__(self, collection_name: str = "some_name", raw_text = '', user_name = 'some_random_name'):
        self.collection_name = collection_name
        self.qdrant = QdrantDB_Sparse(collection_name=collection_name, vector_name=user_name)
        self.vector_name = user_name
        path_store = rf'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\data\sparse_qdrant\{self.collection_name}.txt'
        if os.path.exists(path_store):
            all_lis = '[]'
            with open(path_store) as f:
                full = f.read()
             
            self.docs = list(set(ast.literal_eval(full) + ast.literal_eval(all_lis)))

        
    def add_documents_to_db(self, raw_text):
        vectordb = self.qdrant.vector
        docs = RecursiveChunker().create_chunks_basic(texts=[raw_text])
        texts = [doc.page_content for doc in docs]
        # se = sparse_embed()
        se = sparse_embed().embed_documents(texts=texts)
        # print(se)
        self.docs = [doc.page_content for doc in docs]
        all_text = '[]'
        path_store = rf'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\data\sparse_qdrant\{self.collection_name}.txt'
        if os.path.exists(path_store):
            with open(path_store, 'r') as f:
                all_text = f.read()
        all_list = list(set(ast.literal_eval(all_text)+texts))
        try:
            with open(path_store, 'w') as f:
                f.write(str(all_list))
        except:
            with open(path_store, 'w', encoding='utf-8') as f:
                f.write(str(all_list))
        self.qdrant.add_docs(docs=se, collection_name=self.collection_name, vector_name=self.vector_name)    


    def invoke_sparse(self, query):
        get_em = sparse_embed()
        client = self.qdrant.vector.client
        query_vec = get_em.embed_query(query)
        q_ind = query_vec.vector.indices
        q_val = query_vec.vector.values
        result = client.search(
        collection_name=self.collection_name,
        query_vector=rest.NamedSparseVector(
            name=self.vector_name,
            vector=rest.SparseVector(
                indices=q_ind,
                values=q_val,
            ),
        ),
        with_vectors=True,
        score_threshold=-999999,
        limit=3
        )
        res_final = []
        # print('here ----->\n')
        for i in result:
            self.docs[i.id] = Document(page_content=self.docs[i.id])
            self.docs[i.id].metadata['score'] = i.score
            self.docs[i.id].metadata['id'] = i.id
            res_final.append(self.docs[i.id])
        return res_final
    
class SparseRetriever_milvus:
    def __init__(self, collection_name: str = "some_name", raw_text = '', user_name = 'some_random_name', existing = False):
        self.collection_name = collection_name
        self.qdrant = MilvusDB_Sparse(collection_name=collection_name, user_name=user_name)
        self.vector_name = user_name
        path_store = rf'C:\Users\samarth.srivastava\Desktop\RAG_comprehensive\data\sparse_qdrant\{self.collection_name}.txt'
        if os.path.exists(path_store):
            all_lis = '[]'
            with open(path_store) as f:
                full = f.read()
            self.docs = list(set(ast.literal_eval(full) + ast.literal_eval(all_lis)))

        
    def add_documents_to_db(self, raw_text, pdf = None, docs = None):
        if not docs:
            docs = RecursiveChunker().create_chunks_basic(texts=[raw_text], pdf=pdf)
        self.qdrant.add_text_docs(texts=docs)    


    def invoke_sparse(self, query):
        retriever = self.qdrant.client.as_retriever(search_kwargs = {'k':3})
        return retriever.invoke(query)