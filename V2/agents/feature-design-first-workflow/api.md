# Feature Design-First Workflow Agent - API Documentation

## Описание

Специализированный агент для создания спецификаций новых функций по методологии "дизайн → требования → задачи". Подход, где технический дизайн определяется первым, а требования выводятся из него.

---

## API Вызова

### Метод вызова
```
invokeSubAgent
```

### Обязательные параметры

#### name
- **Тип**: `string`
- **Значение**: `"feature-design-first-workflow"`
- **Описание**: Идентификатор агента

#### prompt
- **Тип**: `string`
- **Описание**: Исходный запрос пользователя с техническим видением
- **Формат**: Описание технического решения

#### explanation
- **Тип**: `string`
- **Описание**: Причина вызова агента
- **Формат**: Краткое объяснение

#### preset
- **Тип**: `string`
- **Значение**: `"design"` | `"requirements"` | `"tasks"`
- **Описание**: Фаза workflow для выполнения

---

## Входные данные

### Структура prompt

#### Для фазы "design"
```
Техническое видение от пользователя + контекст:
- Архитектурный подход
- Технологии и инструменты
- Компоненты и модули
- Имя функции (feature_name в kebab-case)
- Опции дизайна: High-Level, Low-Level, или оба
```

#### Для фазы "requirements"
```
Ссылка на созданный design.md + запрос на вывод требований
```

#### Для фазы "tasks"
```
Ссылки на design.md и requirements.md + запрос на создание плана
```

### Опции дизайна

#### High-Level Design
- Диаграммы системы
- Архитектурные компоненты
- Модели данных
- Взаимодействие компонентов

#### Low-Level Design
- Код и псевдокод
- Алгоритмы
- Сигнатуры функций
- Детальная реализация

### Примеры входных данных

#### Пример 1: Design фаза с обеими опциями
```json
{
  "name": "feature-design-first-workflow",
  "preset": "design",
  "prompt": "Реализовать microservices архитектуру с event sourcing для order processing системы. Использовать Kafka для event bus, PostgreSQL для read models, Event Store для events. Включить High-Level и Low-Level дизайн. Feature name: event-sourced-orders",
  "explanation": "Создание полного технического дизайна для event sourcing архитектуры"
}
```

#### Пример 2: Design фаза только High-Level
```json
{
  "name": "feature-design-first-workflow",
  "preset": "design",
  "prompt": "Добавить caching layer с использованием Redis для улучшения производительности API. Включить только High-Level дизайн с архитектурными диаграммами. Feature name: redis-caching",
  "explanation": "Создание архитектурного дизайна для caching layer"
}
```

---

## Выходные данные

### Фаза "design"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/design.md`
- `.kiro/specs/{feature_name}/.config.kiro`

#### Содержание design.md

**При High-Level Design**:
1. Architecture Overview
2. System Diagrams
3. Component Design
4. Data Models
5. Integration Points

**При Low-Level Design**:
1. Detailed Algorithms
2. Function Signatures
3. Pseudocode/Code Examples
4. Implementation Details
5. Code Structure

#### Пример выхода
```markdown
Создан технический дизайн для event-sourced-orders:

High-Level Design:
- Архитектура: CQRS с Event Sourcing
- Компоненты: Command Service, Query Service, Event Store, Read Models
- Диаграммы: Sequence diagrams для order flow
- Модели: Order, OrderEvent, OrderReadModel

Low-Level Design:
- Алгоритмы обработки событий
- Сигнатуры методов для Command и Query handlers
- Псевдокод для event replay
- Структура классов и интерфейсов

Файл: .kiro/specs/event-sourced-orders/design.md
```

---

### Фаза "requirements"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/requirements.md`

#### Содержание requirements.md
Требования, выведенные из технического дизайна:
1. Функциональные требования
2. User stories (если применимо)
3. Acceptance criteria
4. Correctness properties
5. Non-functional requirements

#### Пример выхода
```markdown
Созданы требования на основе дизайна event-sourced-orders:
- 8 функциональных требований
- 6 user stories
- 15 acceptance criteria
- 5 correctness properties для event sourcing
- NFR: eventual consistency, high availability

Файл: .kiro/specs/event-sourced-orders/requirements.md
```

---

### Фаза "tasks"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/tasks.md`

#### Содержание tasks.md
Аналогично requirements-first workflow

---

## Процесс работы

### Полный цикл workflow

```
1. Design Phase
   ↓
   [Пользователь одобряет design.md]
   ↓
2. Requirements Phase (выведены из дизайна)
   ↓
   [Пользователь одобряет requirements.md]
   ↓
3. Tasks Phase
   ↓
   [Готов к реализации]
```

### Ключевое отличие от requirements-first

- Начинается с технического решения
- Requirements выводятся из дизайна (не наоборот)
- Подходит для технически-ориентированных проектов

---

## Когда использовать

### ✅ Используйте design-first когда:

- Технический подход уже ясен
- Рефакторинг существующей системы
- Документирование legacy кода
- Технические ограничения определяют решение
- Proof of concept или прототип
- Архитектурные решения уже приняты
- Работаете с техническими стейкхолдерами

### ❌ НЕ используйте design-first когда:

- Бизнес-требования должны определять решение (используйте requirements-first)
- Исправляете баг (используйте bugfix-workflow)
- Технический подход неясен
- Нужна валидация бизнес-требований перед дизайном

---

## Примеры использования

### Пример 1: Рефакторинг архитектуры

**Сценарий**: Переход от монолита к микросервисам

**Шаг 1 - Design**:
```javascript
invokeSubAgent({
  name: "feature-design-first-workflow",
  preset: "design",
  prompt: "Разбить монолитное приложение на микросервисы. Выделить сервисы: User Service, Product Service, Order Service, Payment Service. Использовать API Gateway, service mesh с Istio, PostgreSQL per service. Включить High-Level и Low-Level дизайн. Feature name: microservices-migration",
  explanation: "Проектирование миграции на микросервисную архитектуру"
})
```

**Шаг 2 - Requirements**:
```javascript
invokeSubAgent({
  name: "feature-design-first-workflow",
  preset: "requirements",
  prompt: "Design для microservices-migration одобрен. Выведи формальные требования из дизайна.",
  explanation: "Формализация требований на основе архитектурного дизайна"
})
```

**Шаг 3 - Tasks**:
```javascript
invokeSubAgent({
  name: "feature-design-first-workflow",
  preset: "tasks",
  prompt: "Создай план реализации microservices-migration.",
  explanation: "Планирование поэтапной миграции на микросервисы"
})
```

---

### Пример 2: Документирование существующей системы

**Сценарий**: Legacy код без документации

**Workflow**:
```javascript
// Сначала используем context-gatherer
invokeSubAgent({
  name: "context-gatherer",
  prompt: "Проанализируй существующую систему аутентификации в legacy коде",
  explanation: "Сбор информации о legacy системе аутентификации"
})

// Затем design-first для документирования
invokeSubAgent({
  name: "feature-design-first-workflow",
  preset: "design",
  prompt: "На основе анализа legacy кода, создай технический дизайн документ для существующей системы аутентификации. Feature name: auth-system-documentation",
  explanation: "Документирование существующей архитектуры аутентификации"
})
```

---

## Конфигурация

### Файл .config.kiro

Создается автоматически:
```json
{
  "specType": "feature",
  "workflowType": "design-first",
  "featureName": "feature-name",
  "designOptions": {
    "highLevel": true,
    "lowLevel": true
  }
}
```

### Использование конфигурации

- Сохраняет выбранный workflow
- Определяет опции дизайна
- Используется для продолжения workflow
- Позволяет обновлять существующие спецификации

---

## Best Practices

### Качество дизайна

1. **Детальность**: Достаточно деталей для реализации
2. **Ясность**: Понятные диаграммы и описания
3. **Полнота**: Покрытие всех аспектов системы
4. **Реалистичность**: Учет технических ограничений

### Вывод requirements из дизайна

- Requirements должны отражать дизайн решения
- Включать технические ограничения как требования
- Документировать архитектурные решения
- Определять correctness properties на основе дизайна

### Итеративность

- Дизайн может требовать нескольких итераций
- Пользователь может запросить изменения
- Агент адаптирует дизайн на основе фидбека
