import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def run_faiss_demo():
    # 1. Create a dummy research document to simulate a long paper
    sample_text = (
        "Semantic Scholar is an AI-backed search engine for academic publications. "
        "It was developed by the Allen Institute for AI and released in 2015. "
        "Unlike traditional search engines, it uses natural language processing to provide summaries, "
        "extract key findings, and map relationships between papers.\n\n"
        "FAISS (Facebook AI Similarity Search) is a library that allows developers to quickly search "
        "for embeddings of multimedia documents that are similar to each other. "
        "It solves limitations of traditional query search engines that are optimized for hash-based searches, "
        "and provides more scalable vector similarity search functions."
    )
    
    with open("sample_paper.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)

    # 2. Load the document
    print("Loading document...")
    loader = TextLoader("sample_paper.txt")
    docs = loader.load()

    # 3. Chunk the document using LangChain's TextSplitter
    print("Chunking document...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,      # Small chunk size just for this demo
        chunk_overlap=20,    # 20 character overlap
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    # 4. Initialize Embeddings (Downloads a small, fast local model)
    print("Initializing embeddings (this might take a second)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 5. Load chunks into FAISS Vector Store
    print("Building FAISS index...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    # 6. Perform a Semantic Search!
    query = "Who developed Semantic Scholar?"
    print(f"\nQuerying: '{query}'")
    
    results = vector_store.similarity_search(query, k=2) # Get top 2 most relevant chunks
    
    print("\n--- Top Results ---")
    for i, res in enumerate(results):
        print(f"Result {i+1}: {res.page_content}")

if __name__ == "__main__":
    run_faiss_demo()
