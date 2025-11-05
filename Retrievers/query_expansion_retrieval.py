from langchain_ollama import ChatOllama
from Retrievers.dense_retrieval import DenseRetrieval


class QExpansion_retriever(DenseRetrieval):
    model = ChatOllama(model = 'qwen2.5:14b', base_url='http://10.10.64.25:11434/')
    def __init__(self, collection_name = 'default_name'):
        super().__init__(collection_name=collection_name)

    def create_retreiver(self, raw_text = ''):
        self.ret = self.get_retriever(raw_text=raw_text)
        return self.ret

    def get_result(self, query = ''):
        if not self.dense.client.similarity_search('empty', k=1):
            raise Exception('Empty vector store. Create and add documents using QExpansion_retriever().create_retriever() by just passing the raw text')
        original_result = self.ret.invoke(query)[0].page_content
        query = self.model.invoke(
            f'''Expand the following query by adding similar tokens from the context given below: 
                Query : {query}
                context : {original_result}
                **Only return the updated query and nothing else**
            '''
        ).content
        print('new query - >', query)

        return self.ret.invoke(query)
