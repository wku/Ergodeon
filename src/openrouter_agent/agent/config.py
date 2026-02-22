import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class PipelineConfig:
    max_review_iterations: int = 3
    max_retry_per_step: int = 3
    failed_tasks_threshold_percent: int = 30
    snapshot_strategy: str = "directory_copy"
    output_language: str = "ru"

    temperature_analysis: float = 0.1
    temperature_generation: float = 0.3
    temperature_code: float = 0.1
    max_tokens_per_call: int = 4096

    max_file_size_bytes: int = 100000
    max_files_to_read: int = 50

    ignored_directories: List[str] = field(default_factory=lambda: [
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", ".nuxt", "coverage", ".mypy_cache",
        ".pytest_cache", ".ruff_cache", "egg-info",
    ])

    ignored_extensions: List[str] = field(default_factory=lambda: [
        ".pyc", ".pyo", ".so", ".dylib",
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
        ".woff", ".woff2", ".ttf", ".eot",
        ".mp3", ".mp4", ".avi", ".mov",
        ".zip", ".tar", ".gz", ".bz2",
    ])

    priority_files: List[str] = field(default_factory=lambda: [
        "package.json", "requirements.txt", "pyproject.toml",
        "Cargo.toml", "go.mod", "Gemfile",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "Makefile", ".env.example", "tsconfig.json",
        "README.md", "README.rst",
    ])

    docs_dir_name: str = "project_docs"
    projects_dir: str = "projects"

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        cfg = cls()
        cfg.max_review_iterations = int(os.getenv("PIPELINE_MAX_REVIEW", str(cfg.max_review_iterations)))
        cfg.max_retry_per_step = int(os.getenv("PIPELINE_MAX_RETRY", str(cfg.max_retry_per_step)))
        cfg.output_language = os.getenv("PIPELINE_LANG", cfg.output_language)
        return cfg
