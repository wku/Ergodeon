"""
Memory System with Vector Database
Manages context, history, and semantic search using ChromaDB
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import chromadb
from chromadb.config import Settings


class MemorySystem:
    """Vector-based memory system for semantic search and context storage"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, chromadb.Collection] = {}
        self.embedding_cache: Dict[str, List[float]] = {}
    
    async def initialize(self) -> None:
        """Initialize ChromaDB client and collections"""
        
        db_path = self.config.get('db_path', './data/chroma')
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create collections for different memory types
        await self._create_collection('contexts')
        await self._create_collection('results')
        await self._create_collection('conversations')
        await self._create_collection('code_snippets')
    
    async def _create_collection(self, name: str) -> None:
        """Create or get collection"""
        
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            self.collections[name] = collection
        except Exception as error:
            print(f"Failed to create collection {name}: {error}")
            raise
    
    async def store_context(self, agent_name: str, context: Dict[str, Any]) -> None:
        """
        Store agent context in vector database
        
        Args:
            agent_name: Name of agent
            context: Context dictionary
        """
        collection = self.collections.get('contexts')
        if not collection:
            return
        
        entry_id = self._generate_id()
        content = json.dumps(context, default=str)
        
        collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[{
                'agent': agent_name,
                'type': 'context',
                'timestamp': datetime.now().timestamp()
            }]
        )
    
    async def store_result(self, agent_name: str, result: Dict[str, Any]) -> None:
        """
        Store agent result in vector database
        
        Args:
            agent_name: Name of agent
            result: Result dictionary
        """
        collection = self.collections.get('results')
        if not collection:
            return
        
        entry_id = self._generate_id()
        content = json.dumps(result, default=str)
        
        collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[{
                'agent': agent_name,
                'type': 'result',
                'status': result.get('status', 'unknown'),
                'timestamp': datetime.now().timestamp()
            }]
        )
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        agent_response: str
    ) -> None:
        """
        Store conversation turn
        
        Args:
            user_id: User identifier
            user_message: User's message
            agent_response: Agent's response
        """
        collection = self.collections.get('conversations')
        if not collection:
            return
        
        entry_id = self._generate_id()
        content = f"User: {user_message}\nAgent: {agent_response}"
        
        collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[{
                'user_id': user_id,
                'type': 'conversation',
                'timestamp': datetime.now().timestamp()
            }]
        )
    
    async def store_code_snippet(
        self,
        file_path: str,
        code: str,
        description: str
    ) -> None:
        """
        Store code snippet for future reference
        
        Args:
            file_path: Path to file
            code: Code content
            description: Description of code
        """
        collection = self.collections.get('code_snippets')
        if not collection:
            return
        
        entry_id = self._generate_id()
        content = f"{description}\n\nFile: {file_path}\n\n{code}"
        
        collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[{
                'file_path': file_path,
                'language': self._detect_language(file_path),
                'type': 'code',
                'timestamp': datetime.now().timestamp()
            }]
        )
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across memory
        
        Args:
            query: Search query
            limit: Maximum results
            collection_name: Specific collection to search (optional)
            
        Returns:
            List of search results with content, score, metadata
        """
        collections = (
            [self.collections[collection_name]]
            if collection_name and collection_name in self.collections
            else list(self.collections.values())
        )
        
        all_results = []
        
        for collection in collections:
            if not collection:
                continue
            
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if results['documents'] and results['documents'][0]:
                for idx, doc in enumerate(results['documents'][0]):
                    all_results.append({
                        'content': doc,
                        'score': results['distances'][0][idx] if results['distances'] else 0,
                        'metadata': results['metadatas'][0][idx] if results['metadatas'] else {},
                        'id': results['ids'][0][idx]
                    })
        
        # Sort by relevance score (lower is better for cosine distance)
        all_results.sort(key=lambda x: x['score'])
        
        return all_results[:limit]
    
    async def get_recent(
        self,
        limit: int = 10,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent memory entries
        
        Args:
            limit: Maximum entries
            collection_name: Specific collection (optional)
            
        Returns:
            List of recent entries
        """
        collection = (
            self.collections.get(collection_name)
            if collection_name
            else self.collections.get('conversations')
        )
        
        if not collection:
            return []
        
        results = collection.get(limit=limit)
        return self._parse_memory_entries(results)
    
    async def get_by_agent(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get memory entries by agent
        
        Args:
            agent_name: Agent name
            limit: Maximum entries
            
        Returns:
            List of entries from agent
        """
        results = []
        
        for collection in self.collections.values():
            data = collection.get(
                where={'agent': agent_name},
                limit=limit
            )
            results.extend(self._parse_memory_entries(data))
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return results[:limit]
    
    async def clear_old_memory(self, older_than_days: int = 30) -> None:
        """
        Clear old memory entries
        
        Args:
            older_than_days: Delete entries older than this many days
        """
        cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        
        for collection in self.collections.values():
            # Get old entries
            old_entries = collection.get(
                where={'timestamp': {'$lt': cutoff_time}}
            )
            
            if old_entries['ids']:
                collection.delete(ids=old_entries['ids'])
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        
        stats = {}
        
        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {'count': count}
        
        return stats
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import random
        import string
        
        timestamp = int(datetime.now().timestamp() * 1000)
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
        
        return f"{timestamp}-{random_str}"
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        
        ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        lang_map = {
            'py': 'python',
            'ts': 'typescript',
            'tsx': 'typescript',
            'js': 'javascript',
            'jsx': 'javascript',
            'java': 'java',
            'go': 'go',
            'rs': 'rust',
            'cpp': 'cpp',
            'c': 'c'
        }
        
        return lang_map.get(ext, 'unknown')
    
    def _parse_memory_entries(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse ChromaDB results into memory entries"""
        
        if not results.get('ids'):
            return []
        
        entries = []
        for idx, entry_id in enumerate(results['ids']):
            entries.append({
                'id': entry_id,
                'agent': results['metadatas'][idx].get('agent', 'unknown') if results.get('metadatas') else 'unknown',
                'type': results['metadatas'][idx].get('type', 'unknown') if results.get('metadatas') else 'unknown',
                'content': results['documents'][idx] if results.get('documents') else '',
                'timestamp': results['metadatas'][idx].get('timestamp', 0) if results.get('metadatas') else 0,
                'metadata': results['metadatas'][idx] if results.get('metadatas') else {}
            })
        
        return entries
    
    async def shutdown(self) -> None:
        """Shutdown memory system"""
        # ChromaDB client cleanup if needed
        self.client = None
        self.collections.clear()
