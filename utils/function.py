from sentence_transformers import SentenceTransformer   #HuggingFace Model 

def embedding_model():
    model = SentenceTransformer('paraphrase-mpnet-base-v2')
    return model