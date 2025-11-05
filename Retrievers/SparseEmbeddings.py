from langchain_core.embeddings.embeddings import Embeddings
from fastembed import SparseTextEmbedding
from langchain_core.documents import Document
from qdrant_client.http.models import SparseVector
from qdrant_client.http import models as rest


class sparse_embed(Embeddings):
    embeddings_sparsed = SparseTextEmbedding(model_name="Qdrant/bm25")
    def embed_documents(self, texts):
        embeds = list(self.embeddings_sparsed.embed(texts))
        return [
            {"indices": e.indices.tolist(), "values": e.values.tolist()}
            for e in embeds
        ]
    def embed_query(self, text):
        e = list(self.embeddings_sparsed.embed(text))[0]
        # print({"values":e.values.tolist(), "indices":e.indices.tolist()})
        return rest.NamedSparseVector(
                                    name="text",
                                    vector=rest.SparseVector(
                                    indices=e.indices.tolist(),
                                    values=e.values.tolist(),
                                ),
                            )
