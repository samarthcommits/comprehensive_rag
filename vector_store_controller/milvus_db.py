from pymilvus import connections, db, utility, Collection
from langchain_milvus import Milvus, BaseMilvusBuiltInFunction, BM25BuiltInFunction
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from uuid import uuid4
def check_collection_size(collection_name = '', user_name = ''):
    try:
        connections.connect(host="127.0.0.1", port=19530, db_name=user_name)

        collection = Collection(collection_name)
        collection.load()

        # Query for count
        result = collection.query(
            expr="",  # Empty expression matches all
            output_fields=["count(*)"]
        )
        # json.loads(r/)
        return int(result[0]['count(*)'])
    except Exception as e:
        print(e)
        return 0

class MilvusDB:
    def __init__(self, collection_name = 'default', user_name = 'default', embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url='http://10.10.64.25:11434')):
        URI = "http://localhost:19530"
        conn = connections.connect(host="127.0.0.1", port=19530)

        database_list = db.list_database()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        
        conn = connections.connect(host="127.0.0.1", port=19530, db_name=user_name)
        if utility.has_collection(collection_name=collection_name):
            self.client = Milvus(
                    embedding_function = embeddings,
                    collection_name=collection_name,
                    connection_args={"uri": URI, 'db_name':user_name},
                )
        else:
            documents = Document(
                                page_content='init',
                                metadata={}
                            )
            for i, doc in enumerate([documents]):
                doc.id = str(i)
                doc.metadata['pages'] = '[]'
                doc.metadata['pdf_name'] = ''
            self.client = Milvus.from_documents(
                documents=[documents],
                embedding=embeddings,
                collection_name=collection_name,
                connection_args={"uri": URI, 'db_name':user_name},
            )
        print('collection inserted', collection_name)
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)

    def add_text_docs(self, texts, metadatas=None):
        

        uuids = [str(i+self.collect_num+2) for i in range(len(texts))]
        # if len(texts
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)
    
    def add_text_docs_sparse(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        uuids = [str(i+self.collect_num+2) for i in range(len(texts))]
        self.client.add_documents(documents=texts, ids = uuids)
        

class MilvusDB_Sparse:
    def __init__(self, collection_name = 'default', user_name = 'default'):
        URI = "http://localhost:19530"
        conn = connections.connect(host="127.0.0.1", port=19530)

        database_list = db.list_database()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        conn = connections.connect(host="127.0.0.1", port=19530, db_name=user_name)

        if utility.has_collection(collection_name=collection_name):
            self.client = Milvus(
                            collection_name = collection_name,
                            embedding_function = None,
                            builtin_function=BM25BuiltInFunction(
                                                input_field_names="text", output_field_names="sparse"
                                            ),
                            text_field="text",  # `text` is the input field name of BM25BuiltInFunction
                            # `sparse` is the output field name of BM25BuiltInFunction, and `dense1` and `dense2` are the output field names of embedding1 and embedding2
                            vector_field=["sparse"],
                            connection_args={
                                "uri": URI, "db_name": user_name
                            },
                            auto_id=False,
                        )
        else:
            documents = Document(
                                page_content='init',
                                metadata={}
                            )
            for i, doc in enumerate([documents]):
                doc.id = str(i)
                doc.metadata['pages'] = '[]'
                doc.metadata['pdf_name'] = ''
            self.client = Milvus.from_documents(
                        documents=[documents],
                        embedding=None,
                        builtin_function=BM25BuiltInFunction(
                            input_field_names="text", output_field_names="sparse"
                        ),
                        text_field="text",  # `text` is the input field name of BM25BuiltInFunction
                        # `sparse` is the output field name of BM25BuiltInFunction, and `dense1` and `dense2` are the output field names of embedding1 and embedding2
                        vector_field=["sparse"],
                        connection_args={
                            "uri": URI, "db_name": user_name
                        },
                        drop_old=False,
                        collection_name = collection_name,
                    )
        print('client created!')
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)
        
    def add_text_docs(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        print(self.collect_num, 'here collect num sparse')
        uuids = [str(i+self.collect_num+2) for i in range(len(texts))]
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)
        

class MilvusDB_ANN:
    def __init__(self, collection_name = 'default', user_name = 'default', embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url="http://10.10.64.25:11434")):
        URI = "http://localhost:19530"
        conn = connections.connect(host="127.0.0.1", port=19530)

        database_list = db.list_database()
        if user_name not in database_list:
            db.create_database(db_name=user_name)
        conn = connections.connect(host="127.0.0.1", port=19530, db_name=user_name)
        documents = Document(
                            page_content='init',
                            metadata={}
                        )
        
        for i, doc in enumerate([documents]):
            doc.id = str(i)
            doc.metadata['pages'] = '[]'
            doc.metadata['pdf_name'] = ''
        self.client = Milvus.from_documents(
            documents=[documents],
            embedding=embeddings,
            collection_name=collection_name,
            connection_args={"uri": URI, 'db_name':user_name},
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",            # or "L2", "IP"
                "params": {"M": 32, "efConstruction": 200}
            },
            search_params={
                "metric_type": "COSINE",
                "params": {"ef": 64}                # efSearch; keep ≥ top_k
            },
            drop_old = False
        )
        self.collect_num = check_collection_size(user_name=user_name, collection_name=collection_name)
    def add_text_docs(self, texts, metadatas=None):
        # uuids = [str(uuid4()) for _ in range(len(texts))]
        uuids = [str(i+self.collect_num+2) for i in range(len(texts))]
        if len(texts)!=0:
            self.client.add_documents(documents=texts, ids = uuids)

# vector_store_saved.add_documents(documents = [Document(page_content="Third document", metadata={"source": "doc3"}),
#     Document(page_content="Fourth document", metadata={"source": "doc4"})])