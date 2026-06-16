import os
from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import logging
import json
from datetime import datetime
from config import (
    VECTORSTORE_PATH, HISTORY_FILE, GOOGLE_API_KEY,
    LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to hold our vector store
vector_store = None
_embeddings_instance = None
ingest_history = []
chat_histories = {}

def load_history():
    """Load ingestion history from file"""
    global ingest_history
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                ingest_history = json.load(f)
            logger.info(f"Loaded {len(ingest_history)} history records")
        except Exception as e:
            logger.warning(f"Could not load history: {e}")
            ingest_history = []
    else:
        ingest_history = []

def save_history():
    """Save ingestion history to file"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(ingest_history, f, indent=2)
        logger.info(f"Saved {len(ingest_history)} history records")
    except Exception as e:
        logger.error(f"Error saving history: {e}")

def get_embeddings():
    """Get embeddings model"""
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info(f"Loading embeddings model: {EMBEDDING_MODEL}")
        _embeddings_instance = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    else:
        logger.debug("Using cached embeddings model")
    return _embeddings_instance

def get_llm():
    """Get LLM instance"""
    api_key = GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    logger.info(f"Initializing LLM: {LLM_MODEL}")
    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE
    )

def load_vectorstore():
    """Load vectorstore from disk"""
    global vector_store
    
    if VECTORSTORE_PATH.exists():
        try:
            logger.info(f"Loading vectorstore from {VECTORSTORE_PATH}")
            embeddings = get_embeddings()
            vector_store = FAISS.load_local(
                str(VECTORSTORE_PATH),
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vectorstore loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Could not load vectorstore: {e}")
            vector_store = None
            return False
    else:
        logger.info("No existing vectorstore found")
        vector_store = None
        return False

def save_vectorstore():
    """Save vectorstore to disk"""
    global vector_store
    
    if vector_store is None:
        logger.warning("No vectorstore to save")
        return False
    
    try:
        VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving vectorstore to {VECTORSTORE_PATH}")
        vector_store.save_local(str(VECTORSTORE_PATH))
        logger.info("Vectorstore saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving vectorstore: {e}")
        return False

def ingest_documents(documents: List[Document]):
    """Ingest documents into the vector store"""
    global vector_store, ingest_history
    
    if not documents:
        raise ValueError("No documents to ingest")
    
    # Filter out already ingested URLs
    ingested_urls = set()
    for entry in ingest_history:
        if "urls" in entry:
            ingested_urls.update(entry["urls"])
            
    filtered_documents = [doc for doc in documents if doc.metadata.get('source', 'unknown') not in ingested_urls]
    
    if not filtered_documents:
        logger.info("All documents have already been ingested. Skipping.")
        return
        
    logger.info(f"Filtered out {len(documents) - len(filtered_documents)} already ingested documents.")
    documents = filtered_documents
    
    try:
        logger.info(f"Processing {len(documents)} documents...")
        
        # Split documents into chunks
        logger.info(f"Splitting documents (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(documents)
        logger.info(f"Created {len(splits)} chunks from {len(documents)} documents")
        
        # Get embeddings
        logger.info("Creating embeddings...")
        embeddings = get_embeddings()
        
        # Create or add to vector store
        if vector_store is None:
            logger.info("Creating new vectorstore...")
            vector_store = FAISS.from_documents(splits, embeddings)
        else:
            logger.info("Adding documents to existing vectorstore...")
            vector_store.add_documents(splits)
        
        # Extract URLs from metadata
        urls = list(set([doc.metadata.get('source', 'unknown') for doc in documents]))
        
        # Save vectorstore to disk
        save_vectorstore()
        
        # Record in history
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "documents_count": len(documents),
            "chunks_count": len(splits),
            "urls": urls
        }
        ingest_history.append(history_entry)
        save_history()
        
        logger.info(f"Ingestion complete. Total documents in store: {vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 'unknown'}")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise

def answer_question(question: str, session_id: str = "default") -> Dict:
    """Answer a question based on ingested documents"""
    global vector_store, chat_histories
    
    if vector_store is None:
        # Try to load from disk
        if not load_vectorstore():
            raise ValueError("No documents ingested yet. Please ingest some URLs first.")
    
    try:
        logger.info(f"Processing question: {question[:100]}...")
        
        # Get LLM
        # Get LLM
        llm = get_llm()
        
        # Semantic Search (Vector DB) -> Retrieve Chunks
        retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})
        retrieved_docs = retriever.invoke(question)
        
        # Combine retrieved chunks into context
        context_str = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Get chat history
        history = chat_histories.get(session_id, [])
        history_str = ""
        if history:
            history_str = "Previous Conversation History:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-6:]]) + "\n\n"
            
        # Prompt Template
        system_prompt = (
            "You are an expert financial analyst assistant. Use the provided context "
            "to answer the user's question accurately and concisely. "
            "If the provided context does not contain the answer, reply EXACTLY with the phrase 'FALLBACK_NEEDED'. "
            "Structure your response with key points and relevant details.\n\n"
            f"{history_str}"
            "Context: {context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        formatted_prompt = prompt.format_messages(context=context_str, input=question)
        
        # LLM -> Final Grounded Output
        llm_response = llm.invoke(formatted_prompt)
        answer = llm_response.content
        
        sources = []
        for doc in retrieved_docs:
            if hasattr(doc, "metadata") and "source" in doc.metadata:
                sources.append(doc.metadata["source"])
        sources = list(set(sources))
        
        if answer.strip() == "FALLBACK_NEEDED":
            logger.info("Local context insufficient. Falling back to web search...")
            search_tool = DuckDuckGoSearchRun()
            web_results = search_tool.invoke(question)
            
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are an expert financial analyst assistant. Use the following web search results to answer the user's question accurately. Explicitly mention that the answer was found using a live web search.\n\n{history_str}Web Search Results:\n{{context}}"),
                ("human", "{input}"),
            ])
            
            fallback_chain = fallback_prompt | llm
            fallback_response = fallback_chain.invoke({"context": web_results, "input": question})
            answer = fallback_response.content
            sources = ["Web Search: DuckDuckGo"]
            logger.info("Question answered successfully using web fallback")
        else:
            logger.info("Question answered successfully using local context")
            
        # Save to history
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        chat_histories[session_id].append({"role": "Human", "content": question})
        chat_histories[session_id].append({"role": "Assistant", "content": answer})
            
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise

def get_vectorstore_status() -> Dict:
    """Get the current status of the vectorstore"""
    global vector_store
    
    if vector_store is None:
        # Try to load from disk
        load_vectorstore()
    
    if vector_store is None:
        return {
            "loaded": False,
            "count": 0
        }
    
    try:
        # Get count from FAISS index
        count = vector_store.index.ntotal if hasattr(vector_store.index, 'ntotal') else 0
        return {
            "loaded": True,
            "count": count
        }
    except:
        return {
            "loaded": True,
            "count": 0
        }

def clear_vectorstore():
    """Clear the vectorstore"""
    global vector_store
    
    logger.info("Clearing vectorstore...")
    vector_store = None
    
    # Delete files from disk
    if VECTORSTORE_PATH.exists():
        import shutil
        try:
            shutil.rmtree(VECTORSTORE_PATH)
            logger.info("Vectorstore files deleted")
        except Exception as e:
            logger.error(f"Error deleting vectorstore files: {e}")
    
    logger.info("Vectorstore cleared")

# Load history and vectorstore on startup
load_history()
load_vectorstore()
