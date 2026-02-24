"""
WorkflowClassifier - двухэтапная классификация запросов.

Этап 1: быстрая эвристика по ключевым словам и паттернам.
Этап 2: LLM классификация с контекстом проекта (если эвристика не дала уверенного результата).
"""

import os
import json
import logging
from typing import Optional, Tuple
from openai import AsyncOpenAI
from openrouter_agent.utils import find_balanced_json
from openrouter_agent.agent.workflow_registry import WorkflowRegistry

log = logging.getLogger(__name__)

_RESUME_KW = (
    "продолжи", "возобнови", "resume", "продолжить выполнение",
    "продолжи с того", "доделай", "continue",
)

_RESET_KW = ("reset", "сброс", "сбросить")

_ANALYZE_KW = (
    "проанализируй", "анализ", "analyze", "ревью кода", "code review",
    "изучи", "опиши архитектуру", "найди слабые места", "аудит",
    "что здесь не так", "покажи структуру",
)

_RESEARCH_KW = (
    "исследуй", "research", "сравни", "compare", "изучи тему",
    "какие есть варианты", "как лучше реализовать", "обзор технологий",
)

_FIX_KW = (
    "исправь", "fix", "баг", "bug", "ошибка", "error", "не работает",
    "сломалось", "broken", "crash", "падает", "фикс",
)

_BUILD_KW = (
    "создай", "create", "сделай проект", "build", "new project",
    "разработай", "реализуй с нуля", "напиши приложение",
    "сгенерируй проект", "scaffold",
)


class ClassificationResult:
    def __init__(self, workflow: str, confidence: float, reasoning: str = ""):
        self.workflow = workflow
        self.confidence = confidence
        self.reasoning = reasoning


class WorkflowClassifier:
    def __init__(self):
        self.registry = WorkflowRegistry()

    def classify_heuristic(self, text: str) -> Optional[ClassificationResult]:
        lower = text.lower().strip()

        if any(kw in lower for kw in _RESET_KW) and len(lower.split()) <= 3:
            return ClassificationResult("reset", 1.0, "команда сброса")

        if any(kw in lower for kw in _RESUME_KW):
            return ClassificationResult("resume", 0.95, "ключевое слово resume")

        if self._extract_path(text) and len(text.split()) <= 4:
            return ClassificationResult("serve_project", 0.85, "путь к директории")

        if any(kw in lower for kw in _FIX_KW):
            return ClassificationResult("fix", 0.8, "ключевые слова fix/bug")

        if any(kw in lower for kw in _ANALYZE_KW):
            return ClassificationResult("analyze", 0.8, "ключевые слова анализа")

        if any(kw in lower for kw in _RESEARCH_KW):
            return ClassificationResult("research", 0.8, "ключевые слова исследования")

        if any(kw in lower for kw in _BUILD_KW):
            return ClassificationResult("build", 0.75, "ключевые слова создания")

        return None

    async def classify(self, text: str, project_context: str,
                       client: AsyncOpenAI, model: str) -> ClassificationResult:
        heuristic = self.classify_heuristic(text)
        if heuristic and heuristic.confidence >= 0.8:
            log.info(f"heuristic classification: {heuristic.workflow} ({heuristic.confidence})")
            return heuristic

        llm_result = await self._classify_llm(text, project_context, client, model)

        if heuristic and llm_result.confidence < heuristic.confidence:
            return heuristic

        return llm_result

    async def _classify_llm(self, text: str, project_context: str,
                            client: AsyncOpenAI, model: str) -> ClassificationResult:
        workflows_desc = self.registry.get_descriptions_for_llm()

        ctx_block = f"\nКонтекст проекта:\n{project_context}\n" if project_context else ""

        prompt = (
            "Ты классификатор запросов. Определи какой workflow подходит для запроса пользователя.\n\n"
            f"Доступные workflow:\n{workflows_desc}\n"
            "- chat: простой вопрос/ответ, не требующий инструментов или изменений в файлах\n"
            f"{ctx_block}\n"
            f"Запрос пользователя: {text}\n\n"
            "Верни ТОЛЬКО JSON:\n"
            '{"workflow": "build|modify|fix|analyze|research|chat", '
            '"confidence": 0.0-1.0, '
            '"reasoning": "краткое обоснование"}'
        )

        try:
            r = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            raw = r.choices[0].message.content or ""
            js = find_balanced_json(raw)
            if not js:
                log.warning(f"llm classifier returned no json: {raw[:200]}")
                return ClassificationResult("chat", 0.5, "llm не вернул json")

            data = json.loads(js)
            workflow = data.get("workflow", "chat")
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")

            if workflow not in self.registry.list_names():
                log.warning(f"llm returned unknown workflow: {workflow}")
                workflow = "chat"
                confidence = 0.4

            log.info(f"llm classification: {workflow} ({confidence}) - {reasoning}")
            return ClassificationResult(workflow, confidence, reasoning)

        except Exception as e:
            log.error(f"llm classification error: {e}")
            return ClassificationResult("chat", 0.3, f"ошибка классификации: {e}")

    @staticmethod
    def _extract_path(text: str) -> Optional[str]:
        for token in text.split():
            if token.startswith(("/", "./", "~/")):
                expanded = os.path.expanduser(token)
                if os.path.exists(expanded):
                    return os.path.abspath(expanded)
        return None

    @staticmethod
    def extract_path(text: str) -> Optional[str]:
        """Публичный метод для извлечения пути из текста."""
        return WorkflowClassifier._extract_path(text)
