from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import logging
import json
from datetime import datetime
import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from scraper import scrape_urls
from rag import ingest_documents, answer_question, get_vectorstore_status, clear_vectorstore
from utils import validate_urls, validate_question, RateLimiter
from config import (
    API_HOST, API_PORT, API_RELOAD, CORS_ORIGINS,
    RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD, LOG_LEVEL
)

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Financial News QA API",
    description="Advanced Q&A system for financial news articles",
    version="1.0.0"
)

# Add CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD)

# Request models
class IngestRequest(BaseModel):
    urls: List[str] = Field(..., description="List of article URLs to ingest")

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="Question to ask about the ingested articles")
    session_id: str = Field(default="default", description="Session identifier")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

class StatusResponse(BaseModel):
    status: str
    vectorstore_loaded: bool
    documents_count: int
    timestamp: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check if the API is running"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Status endpoint
@app.get("/api/status", response_model=StatusResponse, tags=["System"])
async def get_status():
    """Get the current status of the system"""
    logger.info("Status check requested")
    status = get_vectorstore_status()
    return {
        "status": "ready",
        "vectorstore_loaded": status["loaded"],
        "documents_count": status["count"],
        "timestamp": datetime.now().isoformat()
    }

# Ingest URLs endpoint
@app.post("/api/ingest", tags=["Data Management"])
async def ingest_urls_endpoint(request: IngestRequest, req: Request):
    """Ingest financial news articles from URLs"""
    client_ip = req.client.host if req.client else "unknown"
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining(client_ip)
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again later. Attempts remaining: {remaining}"
        )
    
    if not request.urls:
        logger.warning("Empty URLs list provided")
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    # Validate URLs
    valid_urls, errors = validate_urls(request.urls)
    
    if errors:
        logger.warning(f"Invalid URLs detected: {errors}")
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Some URLs are invalid",
                "valid_count": len(valid_urls),
                "invalid_urls": errors
            }
        )
    
    if not valid_urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")
    
    # Check URL limit
    from config import MAX_URLS_PER_REQUEST
    if len(valid_urls) > MAX_URLS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many URLs. Maximum {MAX_URLS_PER_REQUEST} URLs per request"
        )
    
    try:
        logger.info(f"Starting to ingest {len(valid_urls)} URLs from {client_ip}")
        # Scrape content from URLs
        documents = scrape_urls(valid_urls)
        
        if not documents:
            logger.warning("No documents were scraped from the provided URLs")
            raise HTTPException(status_code=400, detail="Could not extract content from URLs")
        
        # Ingest documents into Vector Store
        ingest_documents(documents)
        
        logger.info(f"Successfully ingested {len(documents)} documents")
        return {
            "status": "success",
            "message": f"Successfully ingested content from {len(valid_urls)} URLs",
            "documents_count": len(documents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error during ingest: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error processing URLs",
                "error": str(e)
            }
        )

# Upload document endpoint
@app.post("/api/upload", tags=["Data Management"])
async def upload_document_endpoint(file: UploadFile = File(...)):
    """Upload a PDF or TXT document and ingest it"""
    try:
        # Create a temporary directory if it doesn't exist
        os.makedirs("temp_uploads", exist_ok=True)
        
        file_path = f"temp_uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Processing uploaded file: {file.filename}")
        
        documents = []
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif file.filename.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()
        else:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
            
        if not documents:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Could not extract content from the file")
            
        # Add metadata source
        for doc in documents:
            doc.metadata["source"] = f"Uploaded File: {file.filename}"
            
        # Ingest documents
        ingest_documents(documents)
        
        # Cleanup
        os.remove(file_path)
        
        logger.info(f"Successfully ingested {len(documents)} document chunks from {file.filename}")
        return {
            "status": "success",
            "message": f"Successfully ingested {file.filename}",
            "documents_count": len(documents),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}", exc_info=True)
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error processing uploaded file",
                "error": str(e)
            }
        )

# Ask question endpoint
@app.post("/api/ask", tags=["Query"])
async def ask_question_endpoint(request: QuestionRequest, req: Request):
    """Ask a question about the ingested articles"""
    client_ip = req.client.host if req.client else "unknown"
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining(client_ip)
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded",
                "remaining_attempts": remaining
            }
        )
    
    # Validate question
    is_valid, error_msg = validate_question(request.question)
    if not is_valid:
        logger.warning(f"Invalid question from {client_ip}: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        logger.info(f"Processing question from {client_ip}: {request.question[:50]}...")
        result = answer_question(request.question, request.session_id)
        answer = result["answer"]
        sources = result.get("sources", [])
        
        logger.info(f"Question answered successfully for {client_ip}")
        return {
            "status": "success",
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error processing question",
                "error": str(e)
            }
        )

# Clear vectorstore endpoint (admin)
@app.post("/api/admin/clear", tags=["Admin"])
async def clear_store():
    """Clear the vectorstore (admin endpoint)"""
    try:
        logger.info("Clearing vectorstore")
        clear_vectorstore()
        return {
            "status": "success",
            "message": "Vectorstore cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing vectorstore: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    )
