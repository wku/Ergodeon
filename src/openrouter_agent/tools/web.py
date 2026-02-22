import requests
import msgspec
from typing import Dict, Any, Optional
from .base import BaseTool

# --- Schemas ---

class WebFetchArgs(msgspec.Struct):
    url: str
    extract_text: bool = True

class WebAPIArgs(msgspec.Struct):
    url: str
    method: str = "GET"
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30

# --- Tools ---

class WebFetchTool(BaseTool[WebFetchArgs]):
    name = "web_fetch"
    description = "Fetch content from a URL. Can extract text from HTML."
    args_schema = WebFetchArgs

    async def run(self, args: WebFetchArgs) -> str:
        try:
            # Mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(args.url, headers=headers, timeout=30)
            response.raise_for_status()

            if args.extract_text and 'text/html' in response.headers.get('Content-Type', ''):
                # Basic text extraction (removing tags)
                import re
                text = response.text
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return f"URL: {args.url}\n\nContent:\n{text[:10000]}..." if len(text) > 10000 else f"URL: {args.url}\n\nContent:\n{text}"
            
            return response.text[:20000] # Limit raw content
        except Exception as e:
            return f"Error fetching URL: {e}"

class WebAPITool(BaseTool[WebAPIArgs]):
    name = "web_api"
    description = "Make a generic HTTP API request (GET, POST, etc)."
    args_schema = WebAPIArgs

    async def run(self, args: WebAPIArgs) -> str:
        try:
            response = requests.request(
                method=args.method,
                url=args.url,
                json=args.data,
                headers=args.headers,
                timeout=args.timeout
            )
            
            try:
                return f"Status: {response.status_code}\nResponse: {response.json()}"
            except:
                return f"Status: {response.status_code}\nResponse: {response.text[:5000]}"
        except Exception as e:
            return f"Error making API request: {e}"
