"""
Context Gatherer Agent
Analyzes codebase to gather relevant context
"""

from typing import Any, Dict, List
from ...core.base_agent import BaseAgent
from ...models.agent import AgentContext, AgentResult, AgentResultStatus


class ContextGathererAgent(BaseAgent):
    """Agent for gathering codebase context"""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute context gathering"""
        
        self.update_progress(10, "Analyzing query")
        
        # Analyze what user wants to understand
        query_analysis = await self._analyze_query(context.request)
        
        self.update_progress(30, "Searching codebase")
        
        # Search for relevant files
        relevant_files = await self._find_relevant_files(query_analysis)
        
        self.update_progress(50, "Analyzing files")
        
        # Analyze found files
        file_analysis = await self._analyze_files(relevant_files)
        
        self.update_progress(70, "Building context map")
        
        # Build context map
        context_map = await self._build_context_map(file_analysis, query_analysis)
        
        self.update_progress(90, "Generating summary")
        
        # Generate summary
        summary = await self._generate_summary(context_map, query_analysis)
        
        self.update_progress(100, "Context gathered")
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            output=summary,
            result={
                'context_map': context_map,
                'relevant_files': relevant_files,
                'analysis': file_analysis
            }
        )
    
    async def validate(self, context: AgentContext) -> bool:
        """Validate context"""
        return context.request is not None and len(context.request) > 0
    
    def process_result(self, result: Any) -> AgentResult:
        """Process result"""
        if isinstance(result, AgentResult):
            return result
        
        return AgentResult(
            status=AgentResultStatus.SUCCESS,
            agent_name=self.config.name,
            result=result
        )
    
    async def _analyze_query(self, request: str) -> Dict[str, Any]:
        """Analyze user query to understand what they want"""
        
        request_lower = request.lower()
        
        query_type = 'general'
        if 'how' in request_lower:
            query_type = 'how'
        elif 'where' in request_lower:
            query_type = 'where'
        elif 'what' in request_lower:
            query_type = 'what'
        elif 'why' in request_lower:
            query_type = 'why'
        
        # Extract keywords
        keywords = self._extract_keywords(request)
        
        return {
            'type': query_type,
            'keywords': keywords,
            'request': request
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        
        words = text.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'how', 'where', 'what', 'why', 'is', 'are'}
        
        return [w for w in words if len(w) > 3 and w not in stop_words]
    
    async def _find_relevant_files(self, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find files relevant to the query"""
        
        relevant_files = []
        
        # Search by keywords
        for keyword in query_analysis['keywords'][:5]:  # Limit to 5 keywords
            # Search in file content
            search_results = await self.use_tool("grepSearch", {
                "query": keyword,
                "caseSensitive": False
            })
            
            for result in search_results[:10]:  # Limit results
                if result not in relevant_files:
                    relevant_files.append(result)
            
            # Search in file names
            file_results = await self.use_tool("fileSearch", {
                "query": keyword
            })
            
            for file_path in file_results[:5]:
                if not any(f.get('file') == file_path for f in relevant_files):
                    relevant_files.append({'file': file_path, 'line': 0})
        
        return relevant_files[:20]  # Limit to 20 files
    
    async def _analyze_files(self, relevant_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze relevant files"""
        
        file_analysis = {}
        
        for file_info in relevant_files[:10]:  # Analyze top 10 files
            file_path = file_info.get('file', file_info)
            
            try:
                # Read file
                content = await self.use_tool("readFile", {
                    "path": file_path
                })
                
                # Analyze file structure
                analysis = {
                    'path': file_path,
                    'size': len(content),
                    'lines': len(content.split('\n')),
                    'type': self._determine_file_type(file_path),
                    'imports': self._extract_imports(content),
                    'exports': self._extract_exports(content),
                    'functions': self._extract_functions(content),
                    'classes': self._extract_classes(content)
                }
                
                file_analysis[file_path] = analysis
                
            except Exception as e:
                # Skip files that can't be read
                continue
        
        return file_analysis
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type from path"""
        
        if file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith(('.ts', '.tsx')):
            return 'typescript'
        elif file_path.endswith(('.js', '.jsx')):
            return 'javascript'
        elif file_path.endswith('.md'):
            return 'markdown'
        else:
            return 'unknown'
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract imports from file"""
        
        imports = []
        lines = content.split('\n')
        
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract exports from file"""
        
        exports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if 'export ' in line:
                exports.append(line)
        
        return exports[:10]  # Limit to 10
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names from file"""
        
        functions = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('def ') or line.startswith('function ') or line.startswith('async def '):
                # Extract function name
                parts = line.split('(')[0].split()
                if len(parts) >= 2:
                    functions.append(parts[-1])
        
        return functions[:20]  # Limit to 20
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names from file"""
        
        classes = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('class '):
                # Extract class name
                parts = line.split('(')[0].split(':')[0].split()
                if len(parts) >= 2:
                    classes.append(parts[1])
        
        return classes[:10]  # Limit to 10
    
    async def _build_context_map(
        self,
        file_analysis: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build context map from analysis"""
        
        context_map = {
            'query': query_analysis['request'],
            'files': {},
            'relationships': [],
            'key_components': []
        }
        
        # Organize files by type
        for file_path, analysis in file_analysis.items():
            file_type = analysis['type']
            
            if file_type not in context_map['files']:
                context_map['files'][file_type] = []
            
            context_map['files'][file_type].append({
                'path': file_path,
                'functions': analysis['functions'],
                'classes': analysis['classes']
            })
        
        # Identify key components
        for file_path, analysis in file_analysis.items():
            if len(analysis['functions']) > 5 or len(analysis['classes']) > 2:
                context_map['key_components'].append(file_path)
        
        return context_map
    
    async def _generate_summary(
        self,
        context_map: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> str:
        """Generate human-readable summary"""
        
        summary_parts = []
        
        summary_parts.append(f"# Context Analysis: {query_analysis['request']}\n")
        
        # File summary
        total_files = sum(len(files) for files in context_map['files'].values())
        summary_parts.append(f"## Found {total_files} relevant files\n")
        
        for file_type, files in context_map['files'].items():
            summary_parts.append(f"### {file_type.capitalize()} files ({len(files)})")
            for file_info in files[:5]:  # Show top 5
                summary_parts.append(f"- {file_info['path']}")
                if file_info['classes']:
                    summary_parts.append(f"  - Classes: {', '.join(file_info['classes'][:3])}")
                if file_info['functions']:
                    summary_parts.append(f"  - Functions: {', '.join(file_info['functions'][:3])}")
            summary_parts.append("")
        
        # Key components
        if context_map['key_components']:
            summary_parts.append("## Key Components")
            for component in context_map['key_components'][:5]:
                summary_parts.append(f"- {component}")
            summary_parts.append("")
        
        return '\n'.join(summary_parts)
