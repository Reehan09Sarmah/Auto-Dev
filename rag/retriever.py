import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone


load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


def retrieve(query:str, top_k:int = 3) -> str:
    query_vec = embedder.embed_query(query)

    results = index.query(
        vector=query_vec,
        top_k=top_k,
        include_metadata=True
    )

    if not results["matches"]:
        return ""

    chunks = [match["metadata"]["text"] for match in results["matches"]]
    return "\n\n---\n\n".join(chunks)