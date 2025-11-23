from langchain_redis import RedisVectorStore, RedisConfig
from langchain_ollama import OllamaEmbeddings

class RedisDB:
    config = RedisConfig(
        index_name="default_name",
        redis_url="redis://127.0.0.1:6379",
        indexing_algorithm="HNSW",  # Enables ANN search
        distance_metric="COSINE",
        vector_datatype="FLOAT32",
        metadata_schema=[
            {"name": "source", "type": "tag"},
            {"name": "page", "type": "numeric"}
        ]
    )
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest", base_url="http://10.10.64.25:11434") 
    def __init__(self, index_name = 'default_name'):
        self.config.index_name = index_name
        self.vector_store = RedisVectorStore(redis_url="http://127.0.0.1:6379", embeddings=self.embeddings, config=self.config)
        #testing22
        #print('ran')