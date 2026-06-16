import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables (.env file should contain GOOGLE_API_KEY)
load_dotenv()

def main():
    # 1. Specify the path to your PDF file
    pdf_path = "sample_resume.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: Please place a PDF file named '{pdf_path}' in the current directory.")
        # Create a dummy file or exit
        return

    print("1. Data Ingestion: Loading PDF using PyPDFLoader...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from the PDF.")

    print("2. Text Splitter: Chunking the document...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("3. Embedding Model & Vector DB: Saving to Chroma...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Save chunks into ChromaDB (Persisted locally in 'chroma_db_data' directory)
    persist_directory = "./chroma_db_data"
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print(f"Chunks saved successfully to Chroma Vector DB at {persist_directory}.")

    print("4. RetrievalQA: Setting up the QA Chain...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Please set the GOOGLE_API_KEY environment variable.")
        return

    # Using the same LLM setup you have in your backend
    llm = ChatOpenAI(
        model="google/gemini-3.5-flash",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=500,
        temperature=0.2
    )

    # Initialize RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    # 5. Query the system
    question = "What are the main skills and experiences mentioned in this document?"
    print(f"\nUser Question: {question}")
    
    print("Processing... (Embedding question -> Semantic Search -> Retrieve Chunks -> Prompt -> LLM)\n")
    response = qa_chain.invoke({"query": question})
    
    print("--- Final Grounded Output ---")
    print(response['result'])
    print("-----------------------------\n")
    print("Sources (Chunks retrieved):")
    for doc in response['source_documents']:
        print(f"- Page: {doc.metadata.get('page', 'Unknown') + 1}")

if __name__ == "__main__":
    main()
