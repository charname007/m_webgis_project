from langchain_core.output_parsers import EmbeddingOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import OllamaEmbeddings


class embedding_LLM():
    def __init__(self, model="nomic-embed-text", openai_api_base="http://localhost:11435",):
        self.embeddings = OllamaEmbeddings(base_url=openai_api_base,model=model)

    def embed_query(self, text):
        self.embeddings.embed_query(text)
