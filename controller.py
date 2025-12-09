from Retrievers.ann_retrieval import ANN, MilvusDB_ANN
from Retrievers.dense_retrieval import DenseRetrieval
from Retrievers.heirarchical_retrieval import Parent_retrieval
from Retrievers.query_expansion_retrieval import QExpansion_retriever
from Retrievers.reranking_retrieval import Rerank
from Retrievers.sparse_retrieval import SparseRetriever, SparseRetriever_milvus
from sentence_transformers import CrossEncoder
from pymilvus import connections, db, utility, Collection

import ast
import time
from database import CollectionDatabase
db_handler = CollectionDatabase()
from chunking.recursive_char import RecursiveChunker
chunker = RecursiveChunker()

class Control:
    def __init__(self):
        self.reranker = CrossEncoder('models1/reranker')
        # pass

    def check_collection_size(self, collection_name = '', user_name = ''):
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
    
    def create_retriever(self, database = 'MilvusDB', chunking = 'recursive', retriever = 'dense', raw_text = '', collect_name = '', user_name = 'default', pdf = None, chunks = None, pdf_full = None):

        options1={
            '1':    "sparse",
            '2':    "dense",
            '3':    "rerank",
            '4':    "query",
            '5':    "ann"
        }
        pdf_name = ''
        num = 0
        # try:
        for i in list(options1.values()):
            try:
                num = max(num, self.check_collection_size(collection_name=f'{collect_name}_{i}', user_name=user_name))
            except Exception as e:
                print(e)
                continue
        # except:
        #     num = num
        if pdf_full:
            pdf_name = pdf_full.name
        if not chunks:
            docments = chunker.create_chunks_basic(pdf=pdf, texts=[raw_text], pdf_name=pdf_name, num=num)
        else:
            docments = chunks
        print(f'chunks - {docments[:2]}')
        collection_name = collect_name
      
        if retriever==options1['1']:
            self.tech_name = 'sparse'
            full_collect = f'{collect_name}_sparse'
            self.tech = SparseRetriever_milvus(collection_name=full_collect, user_name=user_name)
            # if raw_text!='':
            self.tech.add_documents_to_db(raw_text=raw_text, pdf=pdf, docs=docments)
            self.collect_name = collection_name
            # print(f"returning sparse retriever {self.tech.invoke_sparse(query='self attention')}")
            return self
        
        if retriever==options1['2']:
            self.tech_name = 'dense'
            full_collect = f'{collect_name}_dense'
            self.tech = DenseRetrieval(collection_name=full_collect, user_name=user_name)
            self.ret = self.tech.get_retriever(raw_text=raw_text, pdf=pdf, docs=docments)
            
            self.collect_name = collection_name
            # print(f'returning dense retriever {self.ret}')
            return self.ret
        
        if retriever==options1['3']:
            self.tech_name = 'rerank'
            full_collect = f'{collect_name}_rerank'
            self.tech = DenseRetrieval(collection_name=full_collect, user_name=user_name)
            self.ret = self.tech.get_retriever(raw_text=raw_text, rerank=True, docs=docments)
            self.collect_name = collection_name
            # print(f'returning reranked retriever {self.ret}')
            return self.ret
        
        if retriever==options1['5']:
            self.tech_name = 'ann'
            full_collect = f'{collect_name}_ann'
            self.tech = ANN(user_name=user_name, index_name=full_collect)
            # if raw_text!='':
            self.tech.add_documents(raw_text=raw_text, pdf=pdf, docs=docments)
            self.ret = self.tech.get_retriever()
            self.collect_name = collection_name
            # print(f'returning ann retriever {self}')
            return self

    def get_relevant_documents(self, query, type1 = ''):
        if type1!='':
            self.tech_name = type1
        if self.tech_name=='sparse':
            print('problem source 0')
            return self.tech.invoke_sparse(query=query)
        if self.tech_name=='dense':
            print('problem source 1')
            return self.ret.invoke(input=query)[:2]
        if self.tech_name=='ann':
            print('problem source 2')
            return self.tech.invoke(query=query)
        if self.tech_name=='rerank':
            print('problem source 3')
            return self.ret.invoke(input=query)[:2]
        return

    def hybrid(self, database = 'MilvusDB', chunking = 'recursive', retriever = ['Sparse Retrieval', 'ANN Retrieval', 'Dense Retrieval'], raw_text = '', collect_name = '', user_name = 'default', pdf = None, query = '', pdf_full = None):
        all_docs = []
        p = 0
        doc_map = {}
        docs = []
        retrievers = []
        pdf_name = ''
        options1={
                '1':    "sparse",
                '2':    "dense",
                '3':    "rerank",
                '4':    "query",
                '5':    "ann"
            }
        if pdf_full:
            pdf_name = pdf_full.name
        if len(raw_text)!=0 or pdf is not None:
            num = 0
            for i in list(options1.values()):
                try:
                    num = max(num, self.check_collection_size(collection_name=f'{collect_name}_{i}', user_name=user_name))
                except Exception as e:
                    print(e)
                    continue
            chunks = chunker.create_chunks_basic(pdf=pdf, texts=[raw_text], pdf_name=pdf_name, num=num)
        else:
            chunks = []
        options1={
            '1':    "Sparse Retrieval",
            '2':    "Dense Retrieval",
            '3':    "Reranked Retrieval",
            '4':    "Query Expansion Retrieval",
            '5':    "ANN Retrieval"
        }
        
        for i in retriever:
            type1 = ''
            if options1['1']==i:
                type1 = 'sparse'
            if options1['2']==i:
                type1 = 'dense'
            if options1['3']==i:
                type1 = 'rerank'
            if options1['5']==i:
                type1 = 'ann'
            if not db_handler.get_collection_info(user_name=user_name, collection_name=f'{collect_name}_{type1}'):
                    
                db_handler.insert_collection(
                    collection_name=f'{collect_name}_{type1}',
                    user_name=user_name,
                    retrieval_technique=i,
                    database_type=database,
                    chunking_strategy=chunking, 
                    parent_name=collect_name,
                    pdf_name=pdf_name
                )
            print(f'Creating {i} retriever')
            # try:
            r = Control()
            retr = r.create_retriever(user_name=user_name, collect_name=collect_name, retriever=type1, pdf=pdf, chunks = chunks, raw_text='')
            # except:
            #     print(type1)
            #     retr = None
            retrievers.append((retr, type1))
            # print(retr)
            # print('here look =>', retr.get_relevant_documents('some')[:2])
        self.retrievers = retrievers
        return self

    def get_all_results(self, query, rerank = False): 
        all_docs = []
        p = 0
        doc_map = {}
        docs = []   
        # print(self.retrievers, '...................> here')
        # print('here----llll>', self.retrievers[0].get_relevant_documents(query = 'some'))
        # print('done')
        p = 0
        for i, type1 in self.retrievers:
            print(f'in {i} retriever')
            # try:
            p+=1
            docs = i.get_relevant_documents(query=query, type1 = type1)
            # print(f'done with {docs} \n\nfor {p}')
            # except:
            #     continue
            for ind, j in enumerate(docs):
                # print('j ka h--->', j)
                
                if j.metadata['pk'] not in doc_map:
                    doc_map[j.metadata['pk']] = [ind]
                else:
                    doc_map[j.metadata['pk']].append(ind)
            # break

        final_ranks = {}
        rank = 0
        print('mapping docs', doc_map, docs)
    
        for i in doc_map:
            rank = 0
            for j in doc_map[i]:
                rank+=(1/(60+j))
            # print(f'rank = {rank}')
            final_ranks[i] = rank
        ranks = dict(sorted(final_ranks.items(), key=lambda item: item[1], reverse=True))
        rank_keys = [i for i in list(ranks.keys())]
        print('returning docs')
        result = [i for i in docs if i.metadata['pk'] in rank_keys]
        print(f'rank keys = {rank_keys}')
        for i in docs:
            # print(i, 'bef')
            if i.metadata['pk'] in rank_keys:
                result.append(i)
                # print(i, 'aft')
                print('check')
        
        # print(result)
        m2 = CrossEncoder('models1/reranker')
        for i in result:
            i.metadata['re_score'] = 0.5
        if rerank:
            m2 = self.reranker
            passages = result
            for i in passages:
                scores = m2.predict([(query, i.page_content)]) 
                i.metadata['re_score'] = scores[0]
            return sorted(passages, key = lambda document: document.metadata['re_score'], reverse = True)[:3]
        return result[:4]



        # for i in ranks
                
                

            

