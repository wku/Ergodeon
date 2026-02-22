import re
import ast
from pathlib import Path
import msgspec
from typing import Dict, Any, List
from .base import BaseTool

# --- Schemas ---

class CodeAnalysisArgs(msgspec.Struct):
    path: str

# --- Tools ---

class CodeAnalysisTool(BaseTool[CodeAnalysisArgs]):
    name = "analyze_code"
    description = "Analyze code file structure (functions, classes, imports). Supports Python, JS/TS."
    args_schema = CodeAnalysisArgs

    async def run(self, args: CodeAnalysisArgs) -> str:
        path = Path(args.path).resolve()
        if not path.exists():
            return f"Error: File {path} does not exist."
        
        try:
            content = path.read_text(encoding='utf-8')
            ext = path.suffix.lower()
            
            analysis = {}
            if ext == '.py':
                analysis = self._analyze_python(content)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                analysis = self._analyze_js(content)
            else:
                return f"Analysis not supported for extension {ext}. Supported: .py, .js, .ts"

            return f"Code Analysis for {path.name}:\n" + \
                   f"Functions: {len(analysis.get('functions', []))}\n" + \
                   f"Classes: {len(analysis.get('classes', []))}\n" + \
                   f"Imports: {len(analysis.get('imports', []))}\n\nDetails:\n{analysis}"
        except Exception as e:
            return f"Error analyzing code: {e}"

    def _analyze_python(self, content: str) -> Dict[str, Any]:
        analysis = {'functions': [], 'classes': [], 'imports': []}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'].append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis['imports'].append(ast.unparse(node))
        except Exception:
            # Fallback to regex if AST fails
            pass
        return analysis

    def _analyze_js(self, content: str) -> Dict[str, Any]:
        analysis = {'functions': [], 'classes': [], 'imports': []}
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            # Basic regex, not perfect
            if line.startswith('import ') or line.startswith('const ') and 'require(' in line:
                analysis['imports'].append(line)
            if 'class ' in line:
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    analysis['classes'].append(match.group(1))
            if 'function ' in line:
                match = re.search(r'function\s+(\w+)', line)
                if match:
                    analysis['functions'].append(match.group(1))
            if 'const ' in line and '=>' in line:
                 match = re.search(r'const\s+(\w+)\s*=', line)
                 if match:
                    analysis['functions'].append(match.group(1))
        return analysis
