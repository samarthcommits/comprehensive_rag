# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-classification", model="amberoad/bert-multilingual-passage-reranking-msmarco")

print(pipe(('fruit','bus truck bike motorcycle'), padding = True))
# Load model directly
# from transformers import AutoTokenizer, AutoModelForSequenceClassification

# tokenizer = AutoTokenizer.from_pretrained("amberoad/bert-multilingual-passage-reranking-msmarco")
# model = AutoModelForSequenceClassification.from_pretrained("amberoad/bert-multilingual-passage-reranking-msmarco")
