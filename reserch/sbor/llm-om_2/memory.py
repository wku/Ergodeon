import re
import logging
from typing import Optional, Dict, Any, List
from config import EPISODES_FILE
from utils import load_json, save_json

log = logging.getLogger(__name__)


class EpisodeMemory:
    def __init__(self, path=EPISODES_FILE):
        self.path = path
        self.episodes = load_json(self.path, [])

    def save(self):
        save_json(self.path, self.episodes)

    def add(self, episode: Dict[str, Any]):
        self.episodes.append(episode)
        self.save()

    def recent(self, n=5) -> List[Dict[str, Any]]:
        return self.episodes[-n:]

    def find_similar(self, goal: str, cutoff=0.6) -> Optional[Dict[str, Any]]:
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
