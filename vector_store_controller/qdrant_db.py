from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings
from qdrant_client.http import models as rest
from Retrievers.SparseEmbeddings import sparse_embed


class QdrantDB_Sparse:
    # embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url="http://10.10.64.25:11434") 
    def __init__(self, collection_name: str = 'some_name', vector_name = 'some_random_name'):
        client = QdrantClient(url='http://localhost:6333')
        ex = client.collection_exists(collection_name=collection_name)
        
        try:
            client.create_collection(collection_name=collection_name, vectors_config={}, sparse_vectors_config={vector_name: rest.SparseVectorParams(index=rest.SparseIndexParams(on_disk=False,))},)
        except Exception as e:
            print(e)

        # print('here = ', client.client)
  
        self.vector = Qdrant(client = client, collection_name=collection_name, embeddings = sparse_embed(), vector_name=vector_name)
        
    
    def add_docs(self, docs, collection_name = 'some_name', vector_name = 'some_random_name'):
        indices = [emb['indices'] for emb in docs]
        values = [emb['values'] for emb in docs]
        # print(indices, values)
        for i, k in enumerate(docs):
            self.vector.client.upsert(
            collection_name=collection_name,
            points=[
                rest.PointStruct(
                    id=i,
                    payload={},  # Add any additional payload if necessary
                    vector={
                        vector_name: rest.SparseVector(
                            indices=indices[i], values=values[i]
                        )
                    },
                )
            ],
        )



    