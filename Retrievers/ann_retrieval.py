from vector_store_controller.redis_db import RedisDB
from chunking.recursive_char import RecursiveChunker
from vector_store_controller.milvus_db import MilvusDB_ANN

class ANN:
    def __init__(self, index_name = 'default_name', database = 'milvus', user_name = 'common', existing = False):
        if database=='milvus':
            self.redis = MilvusDB_ANN(collection_name=index_name, user_name=user_name)
        else:    
            self.redis = RedisDB(index_name=index_name)
        self.database = database
    
    def add_documents(self, raw_text = '', chunking_strategy = None, pdf = None, docs = None):
        if not docs:
            chunks = RecursiveChunker().create_chunks_basic(texts=[raw_text], pdf=pdf)
        else:
            chunks = docs
        if self.database!='milvus':
            texts = [i.page_content for i in chunks]
            metadatas = [i.metadata for i in chunks]
            self.redis.vector_store.add_texts(
            texts=texts,
            metadatas=metadatas
            )
            self.retriever = self.redis.vector_store.as_retriever()
        else:
            self.redis.add_text_docs(chunks)
            self.retriever = self.redis.client.as_retriever()
    
    def get_retriever(self):
        if self.database!='milvus':
            try:
                if not self.redis.vector_store.similarity_search('empty', k=1):
                    print('here-->', self.redis.vector_store.similarity_search('empty', k=1))
                    return 'nope'
                else:
                    self.retriever = self.redis.vector_store.as_retriever()
                    return self

            except:
                raise Exception("No documents to retrieve, add documents first, use method ANN().add_documents('pass the whole raw text here, we'll chunk it for you')")
        else:
            self.retriever = self.redis.client.as_retriever()
            return self
        
    
    def invoke(self, query = ''):
        return self.retriever.invoke(query)[:2]
    
    


    