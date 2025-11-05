from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_core.documents import Document
import json
class RecursiveChunker:
    def __init__(self):
        pass

    def create_chunks_basic(self, texts, pdf = None):
        text_splitter = TokenTextSplitter(
            chunk_size=200,
            chunk_overlap=20,
        )
        
        if texts and not pdf:
            texts_em = text_splitter.create_documents(texts=texts)
            for i, k in enumerate(texts_em):
                k.id = i
                k.metadata['pages'] = '[]'
                chunk.metadata['pk'] = f'{i+245}'
            return texts_em
        
        elif pdf:
            all_chunks = []
            page_texts = []
            page_numbers = []
            
            # Extract text from each page
            try:
                p = pdf.pages
            except:
                p = pdf
            for page_num, page in enumerate(pdf, start=1):
                try:
                    text = page.extract_text()
                except:
                    text = page.get_text()
                if text:
                    page_texts.append(text)
                    page_numbers.append(page_num)
            
            # Create chunks with page tracking
            for page_num, text in zip(page_numbers, page_texts):
                chunks = text_splitter.split_text(text)
                
                for chunk in chunks:
                    doc = text_splitter.create_documents([chunk])[0]
                    doc.metadata['pages'] = [page_num]
                    all_chunks.append(doc)
            
            # Handle overlaps across pages
            for i in range(1, len(all_chunks)):
                prev_chunk = all_chunks[i-1]
                curr_chunk = all_chunks[i]
                
                # Check if chunks might span pages
                if prev_chunk.metadata['pages'][-1] < curr_chunk.metadata['pages'][0]:
                    # Potential boundary - check for actual overlap
                    prev_end = prev_chunk.page_content[-20:]  # overlap size
                    curr_start = curr_chunk.page_content[:20]
                    
                    if any(word in curr_start for word in prev_end.split()[-3:]):
                        curr_chunk.metadata['pages'] = [
                            prev_chunk.metadata['pages'][-1],
                            curr_chunk.metadata['pages'][0]
                        ]
            
            # Assign IDs
            for i, chunk in enumerate(all_chunks):
                chunk.id = i
                chunk.metadata['pk'] = f'{i+245}'
                chunk.metadata['pages'] = json.dumps(chunk.metadata['pages']) 
            
            return all_chunks


# sp = RecursiveChunker()
# print(sp.create_chunks())

        