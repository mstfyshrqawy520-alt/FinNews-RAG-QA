from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
import logging
from config import REQUEST_TIMEOUT
from urllib.error import URLError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_urls(urls: List[str]) -> List[Document]:
    """
    Scrapes content from the provided URLs using LangChain's WebBaseLoader.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        List of Document objects extracted from the URLs
        
    Raises:
        ValueError: If no URLs are provided or all URLs fail to scrape
    """
    if not urls:
        raise ValueError("No URLs provided for scraping")
    
    logger.info(f"Starting to scrape {len(urls)} URLs with {REQUEST_TIMEOUT}s timeout")
    
    try:
        # Create loader with timeout and skip SSL verification for problematic sites
        loader = WebBaseLoader(urls)
        loader.requests_kwargs = {
            'verify': False,
            'timeout': REQUEST_TIMEOUT
        }
        
        # Add headers to avoid blocking
        loader.requests_kwargs['headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Loading content from URLs...")
        docs = loader.load()
        
        if not docs:
            logger.warning("No content could be extracted from any of the URLs")
            raise ValueError("No content could be extracted from the provided URLs")
        
        logger.info(f"Successfully scraped {len(docs)} documents from {len(urls)} URLs")
        
        # Log metadata for debugging
        for i, doc in enumerate(docs):
            logger.debug(f"Document {i+1}: {len(doc.page_content)} characters from {doc.metadata.get('source', 'unknown')}")
        
        return docs
        
    except URLError as e:
        logger.error(f"URL error during scraping: {e}")
        raise ValueError(f"Failed to connect to URL: {str(e)}")
    except TimeoutError as e:
        logger.error(f"Timeout error during scraping: {e}")
        raise ValueError(f"Request timed out (>{REQUEST_TIMEOUT}s): {str(e)}")
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        raise ValueError(f"Error scraping URLs: {str(e)}")
