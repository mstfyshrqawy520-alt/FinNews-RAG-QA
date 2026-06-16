import re
import logging
from urllib.parse import urlparse
from typing import List, Tuple

logger = logging.getLogger(__name__)

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate if a URL is properly formatted and accessible.
    Returns: (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    url = url.strip()
    
    # Check if URL starts with http/https
    if not url.startswith(('http://', 'https://')):
        return False, f"URL must start with http:// or https://: {url}"
    
    # Basic URL regex validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        return False, f"Invalid URL format: {url}"
    
    # Parse and validate
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, f"URL must have a domain: {url}"
        return True, ""
    except Exception as e:
        return False, f"URL parsing error: {str(e)}"

def validate_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate multiple URLs.
    Returns: (valid_urls, error_messages)
    """
    valid_urls = []
    errors = []
    
    for url in urls:
        is_valid, error_msg = validate_url(url)
        if is_valid:
            valid_urls.append(url.strip())
        else:
            errors.append(f"{url}: {error_msg}")
    
    return valid_urls, errors

def validate_question(question: str) -> Tuple[bool, str]:
    """
    Validate if a question is valid.
    Returns: (is_valid, error_message)
    """
    if not question or not isinstance(question, str):
        return False, "Question must be a non-empty string"
    
    question = question.strip()
    if len(question) < 3:
        return False, "Question must be at least 3 characters long"
    
    if len(question) > 1000:
        return False, "Question must be less than 1000 characters"
    
    return True, ""

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        import time
        current_time = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.window_seconds
        ]
        
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(current_time)
            return True
        
        return False
    
    def get_remaining(self, client_id: str) -> int:
        import time
        current_time = time.time()
        
        if client_id not in self.requests:
            return self.max_requests
        
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if current_time - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[client_id]))
