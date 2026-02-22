import os
import logging
from typing import Dict, List, Tuple
from openrouter_agent.agent.config import PipelineConfig

log = logging.getLogger(__name__)

FILE_CATEGORIES = {
    "config": ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
               "go.mod", "Gemfile", "tsconfig.json", "Makefile", ".env.example",
               "docker-compose.yml", "docker-compose.yaml", "Dockerfile"],
    "entry_point": ["main.py", "app.py", "index.py", "launcher.py", "server.py",
                    "main.ts", "index.ts", "app.ts", "main.js", "index.js", "app.js"],
    "routing": ["routes", "router", "urls", "endpoints", "api"],
    "model": ["models", "schemas", "entities", "types"],
    "test": ["test_", "_test.", ".test.", ".spec.", "tests/"],
}


class ProjectScanner:
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()

    def scan(self, project_dir: str) -> List[Dict]:
        files = []
        for root, dirs, filenames in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in self.config.ignored_directories
                       and not d.endswith(".egg-info")]
            for f in filenames:
                ext = os.path.splitext(f)[1].lower()
                if ext in self.config.ignored_extensions:
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, project_dir)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                files.append({"path": rel, "full_path": full, "size": size, "ext": ext, "name": f})
        log.info(f"scanned {len(files)} files in {project_dir}")
        return files

    def classify_file(self, file_info: Dict) -> str:
        name = file_info["name"].lower()
        path = file_info["path"].lower()
        for cat, patterns in FILE_CATEGORIES.items():
            for p in patterns:
                if name == p or p in path:
                    return cat
        return "other"

    def prioritize(self, files: List[Dict], parsed_request: str = "") -> List[Dict]:
        priority_names = {p.lower() for p in self.config.priority_files}
        req_words = set(parsed_request.lower().split()) if parsed_request else set()

        def score(f):
            s = 0
            if f["name"].lower() in priority_names:
                s += 100
            cat = self.classify_file(f)
            cat_scores = {"config": 90, "entry_point": 80, "routing": 70, "model": 60, "test": 20}
            s += cat_scores.get(cat, 10)
            if req_words:
                path_words = set(f["path"].lower().replace("/", " ").replace("_", " ").replace(".", " ").split())
                overlap = len(req_words & path_words)
                s += overlap * 15
            return s

        return sorted(files, key=score, reverse=True)

    def read_files(self, files: List[Dict], max_count: int = None) -> Dict[str, str]:
        limit = max_count or self.config.max_files_to_read
        contents = {}
        for f in files[:limit]:
            try:
                if f["size"] > self.config.max_file_size_bytes:
                    with open(f["full_path"], "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read(self.config.max_file_size_bytes)
                    contents[f["path"]] = text + "\n... (truncated)"
                else:
                    with open(f["full_path"], "r", encoding="utf-8", errors="replace") as fh:
                        contents[f["path"]] = fh.read()
            except Exception as e:
                log.warning(f"cannot read {f['path']}: {e}")
                contents[f["path"]] = f"[error reading file: {e}]"
        log.info(f"read {len(contents)} files")
        return contents

    def get_file_tree(self, files: List[Dict]) -> str:
        lines = []
        for f in sorted(files, key=lambda x: x["path"]):
            cat = self.classify_file(f)
            lines.append(f"{f['path']} [{cat}] ({f['size']}b)")
        return "\n".join(lines)
