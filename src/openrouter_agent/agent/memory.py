import re
import logging
from typing import Optional, Dict, Any, List
from openrouter_agent.utils import load_json, save_json

log = logging.getLogger(__name__)

DEFAULT_MEMORY_PATH = "memory/episodes.json"


class EpisodeMemory:
    def __init__(self, path: str = DEFAULT_MEMORY_PATH):
        self.path = path
        self.episodes: List[Dict[str, Any]] = load_json(self.path, [])
        log.info(f"memory loaded: {len(self.episodes)} episodes from {self.path}")

    def save(self) -> None:
        save_json(self.path, self.episodes)

    def add(self, episode: Dict[str, Any]) -> None:
        self.episodes.append(episode)
        self.save()
        log.info(f"episode saved, total: {len(self.episodes)}")

    def recent(self, n: int = 5) -> List[Dict[str, Any]]:
        return self.episodes[-n:]

    def find_similar(self, goal: str, cutoff: float = 0.6) -> Optional[Dict[str, Any]]:
        goal_tokens = set(re.findall(r"[a-zA-Z0-9]+", goal.lower()))
        best, best_score = None, 0.0
        for ep in self.episodes:
            tokens2 = set(re.findall(r"[a-zA-Z0-9]+", ep.get("goal", "").lower()))
            if not tokens2:
                continue
            score = len(goal_tokens & tokens2) / max(1, len(goal_tokens | tokens2))
            if score > best_score:
                best_score = score
                best = ep
        return best if best_score >= cutoff else None
