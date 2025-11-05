from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank

compressor = CohereRerank(model="rerank-english-v3.0", top_n=2)



class Rerank:
    def __init__(self, retriever):
        self.retriever = retriever

    def reranking_retreiver(self):
        compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=self.retriever
            )
        return compression_retriever