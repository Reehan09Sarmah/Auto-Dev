import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

load_dotenv()


pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))


embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n---\n", "\n\n", "\n", " "]
)


def index_docs():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    all_chunks = []

    for filename in os.listdir(docs_dir):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = splitter.split_text(text)
        print(f"Number of chunks: {len(chunks)}")

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{filename}_{i}",
                "text": chunk,
                "source": filename
            })

    print(f"\nTotal chunks to index: {len(all_chunks)}")

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]

        vectors = embedder.embed_documents(texts)

        records = [
            {
                "id": ids[j], 
                "values": vectors[j], 
                "metadata": {"text": texts[j], "source": batch[j]["source"]}
            }
            for j in range(len(batch))
        ]

        index.upsert(vectors=records)
        print(f"Uploaded batch {i // batch_size + 1}")
    
    print("\nIndexing complete!")


if __name__ == "__main__":
    index_docs()