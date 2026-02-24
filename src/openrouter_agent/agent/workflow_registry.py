"""
WorkflowRegistry - реестр воркфлоу.

Каждый воркфлоу определяет набор фаз, которые выполняются последовательно.
План (конкретные шаги) генерируется LLM под каждый запрос.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass
class Phase:
    name: str
    description: str
    skippable: bool = False
    requires_llm: bool = False
    requires_tools: bool = False
    artifacts: List[str] = field(default_factory=list)


@dataclass
class WorkflowDef:
    name: str
    description: str
    phases: List[Phase]
    creates_stage: bool = True
    artifacts_produced: List[str] = field(default_factory=list)


# --- Определения воркфлоу ---

BUILD = WorkflowDef(
    name="build",
    description="Создание нового проекта или крупной фичи с полным циклом планирования",
    phases=[
        Phase("parse_request", "Разбор запроса на цели, действия, ограничения", requires_llm=True,
              artifacts=["parsed_request.yaml"]),
        Phase("scan_project", "Сканирование структуры и файлов проекта", requires_tools=True,
              skippable=True, artifacts=["scan_results.yaml"]),
        Phase("generate_digest", "Создание дайджеста проекта", requires_llm=True,
              artifacts=["project_digest.yaml"]),
        Phase("generate_checklist", "Генерация атомарных задач с зависимостями", requires_llm=True,
              artifacts=["checklist.yaml", "checklist.md"]),
        Phase("generate_walkthrough", "Описание изменений по блокам", requires_llm=True,
              artifacts=["walkthrough.yaml", "walkthrough.md"]),
        Phase("generate_plan", "Шаги имплементации привязанные к чеклисту", requires_llm=True,
              artifacts=["implementation_plan.yaml", "implementation_plan.md"]),
        Phase("review", "Ожидание обратной связи от пользователя", skippable=True),
        Phase("implement", "Последовательное выполнение шагов плана", requires_tools=True),
        Phase("verify", "Проверка результатов и подсчёт статистики"),
    ],
    artifacts_produced=[
        "parsed_request.yaml", "project_digest.yaml",
        "checklist.yaml", "walkthrough.yaml", "implementation_plan.yaml",
    ],
)

MODIFY = WorkflowDef(
    name="modify",
    description="Точечная доработка существующего кода без масштабного планирования",
    phases=[
        Phase("parse_request", "Разбор запроса", requires_llm=True,
              artifacts=["parsed_request.yaml"]),
        Phase("scan_affected", "Сканирование затронутых файлов", requires_tools=True,
              artifacts=["affected_files.yaml"]),
        Phase("generate_plan", "Короткий план изменений", requires_llm=True,
              artifacts=["change_plan.yaml", "change_plan.md"]),
        Phase("implement", "Выполнение шагов", requires_tools=True),
        Phase("verify", "Проверка результата"),
    ],
    artifacts_produced=["parsed_request.yaml", "affected_files.yaml", "change_plan.yaml"],
)

FIX = WorkflowDef(
    name="fix",
    description="Исправление бага или ошибки с поиском root cause",
    phases=[
        Phase("parse_request", "Разбор описания проблемы", requires_llm=True,
              artifacts=["parsed_request.yaml"]),
        Phase("investigate", "Поиск причины, анализ затронутых модулей", requires_llm=True,
              requires_tools=True, artifacts=["investigation.yaml", "investigation.md"]),
        Phase("generate_plan", "План исправления", requires_llm=True,
              artifacts=["fix_plan.yaml", "fix_plan.md"]),
        Phase("implement", "Применение фикса", requires_tools=True),
        Phase("verify", "Проверка что баг устранён"),
    ],
    artifacts_produced=["parsed_request.yaml", "investigation.yaml", "fix_plan.yaml"],
)

ANALYZE = WorkflowDef(
    name="analyze",
    description="Анализ проекта или его части без внесения изменений",
    phases=[
        Phase("parse_request", "Определение области и глубины анализа", requires_llm=True,
              artifacts=["parsed_request.yaml"]),
        Phase("scan_project", "Сканирование проекта", requires_tools=True,
              artifacts=["scan_results.yaml"]),
        Phase("analyze", "Глубокий анализ с использованием инструментов", requires_llm=True,
              requires_tools=True),
        Phase("generate_report", "Формирование отчёта", requires_llm=True,
              artifacts=["analysis_report.md"]),
    ],
    artifacts_produced=["parsed_request.yaml", "scan_results.yaml", "analysis_report.md"],
)

RESEARCH = WorkflowDef(
    name="research",
    description="Исследование темы или технологии со сбором информации",
    phases=[
        Phase("parse_request", "Определение темы и критериев", requires_llm=True,
              artifacts=["parsed_request.yaml"]),
        Phase("research", "Сбор информации из веб-источников и документации",
              requires_llm=True, requires_tools=True, artifacts=["sources.yaml"]),
        Phase("synthesize", "Анализ и сравнение найденной информации", requires_llm=True),
        Phase("generate_report", "Формирование отчёта с рекомендациями", requires_llm=True,
              artifacts=["research_report.md"]),
    ],
    artifacts_produced=["parsed_request.yaml", "sources.yaml", "research_report.md"],
)

CHAT = WorkflowDef(
    name="chat",
    description="Простой вопрос-ответ без планирования и файловых операций",
    phases=[
        Phase("respond", "Прямой ответ", requires_llm=True),
    ],
    creates_stage=False,
)

RESUME = WorkflowDef(
    name="resume",
    description="Возобновление прерванного стейджа",
    phases=[
        Phase("load_previous", "Чтение прерванного стейджа"),
        Phase("recalculate", "Пересчёт оставшихся шагов"),
        Phase("implement", "Продолжение выполнения с точки остановки", requires_tools=True),
        Phase("verify", "Проверка финального результата"),
    ],
    creates_stage=False,
)


class WorkflowRegistry:
    def __init__(self):
        self._workflows: Dict[str, WorkflowDef] = {}
        for wf in (BUILD, MODIFY, FIX, ANALYZE, RESEARCH, CHAT, RESUME):
            self._workflows[wf.name] = wf

    def get(self, name: str) -> Optional[WorkflowDef]:
        return self._workflows.get(name)

    def list_names(self) -> List[str]:
        return list(self._workflows.keys())

    def get_descriptions_for_llm(self) -> str:
        lines = []
        for name, wf in self._workflows.items():
            if name in ("chat", "resume"):
                continue
            lines.append(f"- {name}: {wf.description}")
        return "\n".join(lines)
