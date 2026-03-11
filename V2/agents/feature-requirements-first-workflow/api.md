# Feature Requirements-First Workflow Agent - API Documentation

## Описание

Специализированный агент для создания спецификаций новых функций по методологии "требования → дизайн → задачи". Традиционный подход, где бизнес-требования определяют технический дизайн.

---

## API Вызова

### Метод вызова
```
invokeSubAgent
```

### Обязательные параметры

#### name
- **Тип**: `string`
- **Значение**: `"feature-requirements-first-workflow"`
- **Описание**: Идентификатор агента

#### prompt
- **Тип**: `string`
- **Описание**: Исходный запрос пользователя с контекстом
- **Формат**: Описание функции, которую нужно реализовать

#### explanation
- **Тип**: `string`
- **Описание**: Причина вызова агента
- **Формат**: Краткое объяснение делегирования

#### preset
- **Тип**: `string`
- **Значение**: `"requirements"` | `"design"` | `"tasks"`
- **Описание**: Фаза workflow для выполнения

---

## Входные данные

### Структура prompt

#### Для фазы "requirements"
```
Описание функции от пользователя + контекст:
- Что должна делать функция
- Для кого предназначена
- Какие проблемы решает
- Имя функции (feature_name в kebab-case)
```

#### Для фазы "design"
```
Ссылка на созданный requirements.md + запрос на создание дизайна
```

#### Для фазы "tasks"
```
Ссылки на requirements.md и design.md + запрос на создание плана реализации
```

### Примеры входных данных

#### Пример 1: Начало workflow (requirements фаза)
```json
{
  "name": "feature-requirements-first-workflow",
  "preset": "requirements",
  "prompt": "Пользователь хочет добавить систему уведомлений в приложение. Пользователи должны получать уведомления о важных событиях: новые сообщения, обновления заказов, системные оповещения. Feature name: notification-system",
  "explanation": "Начало requirements-first workflow для системы уведомлений"
}
```

#### Пример 2: Продолжение на design фазу
```json
{
  "name": "feature-requirements-first-workflow",
  "preset": "design",
  "prompt": "Requirements документ для notification-system завершен и одобрен пользователем. Создай технический дизайн на основе этих требований.",
  "explanation": "Переход к фазе дизайна после утверждения требований"
}
```

#### Пример 3: Создание tasks
```json
{
  "name": "feature-requirements-first-workflow",
  "preset": "tasks",
  "prompt": "Requirements и design документы для notification-system завершены. Создай детальный план реализации с задачами.",
  "explanation": "Создание плана реализации на основе требований и дизайна"
}
```

---

## Выходные данные

### Фаза "requirements"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/requirements.md`
- `.kiro/specs/{feature_name}/.config.kiro`

#### Содержание requirements.md
1. **Overview**: Общее описание функции
2. **User Stories**: Пользовательские истории
3. **Acceptance Criteria**: Критерии приемки
4. **Correctness Properties**: Формальные свойства корректности для PBT
5. **Non-Functional Requirements**: Производительность, безопасность, и т.д.

#### Пример выхода
```markdown
Создан документ требований для notification-system:
- 5 пользовательских историй
- 12 критериев приемки
- 4 correctness properties для тестирования
- Нефункциональные требования определены

Файл: .kiro/specs/notification-system/requirements.md
```

---

### Фаза "design"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/design.md`

#### Содержание design.md
1. **Architecture Overview**: Общая архитектура решения
2. **Component Design**: Дизайн компонентов и модулей
3. **Data Models**: Модели данных и схемы
4. **API Design**: Дизайн API endpoints (если применимо)
5. **Integration Points**: Точки интеграции с существующей системой
6. **Technology Stack**: Выбранные технологии и библиотеки

#### Пример выхода
```markdown
Создан технический дизайн для notification-system:
- Архитектура: Event-driven с message queue
- Компоненты: NotificationService, NotificationStore, UI components
- Модели данных: Notification, NotificationPreference
- API: REST endpoints для управления уведомлениями
- Интеграция: WebSocket для real-time, Push API для мобильных
- Stack: Node.js, Redis, Socket.io, React

Файл: .kiro/specs/notification-system/design.md
```

---

### Фаза "tasks"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/tasks.md`

#### Содержание tasks.md
1. **Иерархический список задач**: Основные задачи и подзадачи
2. **Checkbox статусы**: `[ ]` для отслеживания прогресса
3. **Описания задач**: Четкие инструкции для каждой задачи
4. **Зависимости**: Порядок выполнения задач
5. **PBT задачи**: Задачи для property-based тестирования

#### Пример выхода
```markdown
Создан план реализации для notification-system:

- [ ] 1. Setup infrastructure
  - [ ] 1.1 Configure Redis
  - [ ] 1.2 Setup message queue
- [ ] 2. Implement backend service
  - [ ] 2.1 Create NotificationService
  - [ ] 2.2 Implement event handlers
  - [ ] 2.3 Add PBT for notification delivery property
- [ ] 3. Implement frontend
  - [ ] 3.1 Create UI components
  - [ ] 3.2 Setup WebSocket connection
- [ ] 4. Integration testing

Файл: .kiro/specs/notification-system/tasks.md
```

---

## Процесс работы

### Полный цикл workflow

```
1. Requirements Phase
   ↓
   [Пользователь одобряет requirements.md]
   ↓
2. Design Phase
   ↓
   [Пользователь одобряет design.md]
   ↓
3. Tasks Phase
   ↓
   [Готов к реализации через spec-task-execution]
```

### Итеративность

На каждой фазе:
1. Агент создает документ
2. Представляет пользователю на ревью
3. Ожидает одобрения или фидбека
4. Итерирует при необходимости
5. Переходит к следующей фазе после одобрения

---

## Когда использовать

### ✅ Используйте requirements-first когда:

- Есть четкие бизнес-требования
- Технический подход еще не определен
- Нужно документировать требования стейкхолдеров
- Compliance или регуляторные требования важны
- Традиционный waterfall-подобный процесс
- Работаете с product managers или бизнес-аналитиками

### ❌ НЕ используйте requirements-first когда:

- Технический подход уже ясен (используйте design-first)
- Исправляете баг (используйте bugfix-workflow)
- Рефакторите существующий код (используйте design-first)
- Нужна быстрая реализация без формальных требований

---

## Примеры использования

### Пример 1: E-commerce функция

**Сценарий**: Добавление системы отзывов на товары

**Шаг 1 - Requirements**:
```javascript
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "requirements",
  prompt: "Добавить систему отзывов на товары в e-commerce приложение. Пользователи должны оставлять рейтинг (1-5 звезд), текстовый отзыв, загружать фото. Модерация отзывов администраторами. Feature name: product-reviews",
  explanation: "Создание requirements для системы отзывов на товары"
})
```

**Результат**: Создан requirements.md с user stories, acceptance criteria, correctness properties

**Шаг 2 - Design**:
```javascript
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "design",
  prompt: "Requirements для product-reviews одобрены. Создай технический дизайн.",
  explanation: "Создание технического дизайна на основе утвержденных требований"
})
```

**Результат**: Создан design.md с архитектурой, компонентами, API, моделями данных

**Шаг 3 - Tasks**:
```javascript
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "tasks",
  prompt: "Requirements и design для product-reviews готовы. Создай план реализации.",
  explanation: "Создание детального плана реализации"
})
```

**Результат**: Создан tasks.md с иерархическим списком задач

---

### Пример 2: SaaS функция

**Сценарий**: Добавление multi-tenancy в SaaS приложение

**Полный workflow**:
```javascript
// Фаза 1
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "requirements",
  prompt: "Реализовать multi-tenancy для SaaS приложения. Каждый tenant должен иметь изолированные данные, собственные настройки, и биллинг. Поддержка tenant switching для admin пользователей. Feature name: multi-tenancy",
  explanation: "Документирование требований для multi-tenancy функциональности"
})

// После одобрения requirements.md

// Фаза 2
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "design",
  prompt: "Requirements для multi-tenancy одобрены. Создай технический дизайн с учетом изоляции данных и производительности.",
  explanation: "Проектирование архитектуры multi-tenancy"
})

// После одобрения design.md

// Фаза 3
invokeSubAgent({
  name: "feature-requirements-first-workflow",
  preset: "tasks",
  prompt: "Создай план реализации multi-tenancy на основе requirements и design.",
  explanation: "Планирование реализации multi-tenancy"
})
```

---

## Валидация и проверки

### Автоматические проверки

Агент выполняет:
- Проверку существования feature directory
- Валидацию формата feature_name (kebab-case)
- Проверку наличия предыдущих фаз перед переходом к следующей
- Валидацию структуры документов

### Предварительные условия

**Для design фазы**:
- Должен существовать requirements.md
- Requirements должен быть одобрен пользователем

**Для tasks фазы**:
- Должны существовать requirements.md И design.md
- Оба документа должны быть одобрены

---

## Best Practices

### Качество requirements

1. **Специфичность**: Четкие, измеримые требования
2. **Полнота**: Покрытие всех аспектов функции
3. **Тестируемость**: Каждое требование должно быть проверяемым
4. **Correctness properties**: Формальные свойства для PBT

### Переход между фазами

1. Дождитесь явного одобрения пользователя
2. Не переходите автоматически к следующей фазе
3. Итерируйте на текущей фазе при необходимости
4. Убедитесь, что документ полный перед переходом

### Работа с пользователем

- Представляйте документы на ревью
- Запрашивайте фидбек
- Итерируйте на основе комментариев
- Подтверждайте понимание требований
