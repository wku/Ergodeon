# Spec Task Execution Agent - API Documentation

## Описание

Специализированный агент для выполнения задач из спецификаций с поддержкой property-based testing. Реализует задачи из tasks.md файлов, созданных через spec workflows.

---

## API Вызова

### Метод вызова
```
invokeSubAgent
```

### Обязательные параметры

#### name
- **Тип**: `string`
- **Значение**: `"spec-task-execution"`
- **Описание**: Идентификатор агента

#### prompt
- **Тип**: `string`
- **Описание**: Полные детали задачи с контекстом
- **Формат**: Структурированное описание задачи

#### explanation
- **Тип**: `string`
- **Описание**: Краткое объяснение делегируемой задачи
- **Формат**: Одно предложение

---

## Входные данные

### Структура prompt

Prompt должен содержать:

1. **ID и текст задачи**: Например, "Task 2.1: Implement user authentication"
2. **Путь к спецификации**: Относительный путь к директории спецификации
3. **Подзадачи**: Список подзадач, если есть
4. **Контекст из спецификации**: Релевантная информация из requirements.md, design.md

### Пример входных данных

#### Пример 1: Простая задача
```json
{
  "name": "spec-task-execution",
  "prompt": "Execute task from spec at .kiro/specs/user-authentication/\n\nTask: 2. Implement login form component\n\nContext from requirements:\n- Form should have email and password fields\n- Include remember me checkbox\n- Show validation errors\n\nContext from design:\n- Use React with hooks\n- Styled with Tailwind CSS\n- Form validation with Formik",
  "explanation": "Implementing login form component from user-authentication spec"
}
```

#### Пример 2: Задача с подзадачами
```json
{
  "name": "spec-task-execution",
  "prompt": "Execute task from spec at .kiro/specs/payment-processing/\n\nTask: 3. Implement payment service\n\nSub-tasks:\n- 3.1 Create PaymentService class\n- 3.2 Implement processPayment method\n- 3.3 Add error handling\n- 3.4 Write unit tests\n\nContext from design:\n- Use Stripe API for payment processing\n- Implement retry logic for failed payments\n- Store transaction records in database",
  "explanation": "Implementing payment service with all sub-tasks"
}
```

---

## Выходные данные

### Структура ответа

Агент возвращает:

#### 1. Статус выполнения
- `success`: Задача выполнена успешно
- `failed`: Задача не выполнена
- `partial`: Частичное выполнение

#### 2. Созданные/измененные файлы
- Список файлов с путями
- Описание изменений

#### 3. Результаты тестирования
- Unit тесты: passed/failed
- Property-based тесты: passed/failed
- Coverage метрики

#### 4. Обновления статуса
- Статусы подзадач
- Статус основной задачи

### Пример выходных данных

```json
{
  "status": "success",
  "taskId": "2.1",
  "taskText": "Implement login form component",
  "filesCreated": [
    "src/components/LoginForm.jsx",
    "src/components/__tests__/LoginForm.test.jsx"
  ],
  "filesModified": [
    "src/App.jsx"
  ],
  "testResults": {
    "unit": {
      "passed": 8,
      "failed": 0,
      "total": 8
    },
    "pbt": {
      "passed": 2,
      "failed": 0,
      "total": 2
    }
  },
  "subtasksCompleted": [
    "2.1.1 Create form component",
    "2.1.2 Add validation",
    "2.1.3 Write tests"
  ]
}
```

---

## Property-Based Testing

### Что такое PBT

Property-based testing проверяет, что код соответствует формальным свойствам корректности через генерацию множества тестовых случаев.

### Интеграция с задачами

Агент автоматически:
- Идентифицирует correctness properties из спецификации
- Создает PBT тесты для этих свойств
- Запускает тесты с генерацией случайных данных
- Валидирует соответствие спецификации

### Пример PBT задачи

**Задача**: "Implement sorting function with property: sorted array maintains all original elements"

**Агент создаст**:
```javascript
// Property test
test('sorting preserves all elements', () => {
  fc.assert(
    fc.property(fc.array(fc.integer()), (arr) => {
      const sorted = sortArray(arr);
      return sorted.length === arr.length &&
             sorted.every(el => arr.includes(el));
    })
  );
});
```

---

## Когда использовать

### ✅ Используйте spec-task-execution когда:

- Выполняете задачу из tasks.md файла спецификации
- Работаете в рамках формальной спецификации
- Нужна поддержка property-based testing
- Требуется автоматическое обновление статусов задач
- Выполняете "run all tasks" для спецификации

### ❌ НЕ используйте spec-task-execution когда:

- Задача не связана со спецификацией (используйте general-task-execution)
- Нужен только анализ без реализации (используйте context-gatherer)
- Создаете новую спецификацию (используйте feature/bugfix workflow агенты)

---

## Режимы работы

### Режим одной задачи

**Активация**: Пользователь запрашивает "execute task 2" или "start task 1.3"

**Процесс**:
1. Оркестратор читает спецификацию
2. Оркестратор обновляет статус задачи на `in_progress`
3. Оркестратор делегирует spec-task-execution
4. Агент реализует задачу
5. Агент запускает тесты
6. Агент возвращает результат
7. Оркестратор обновляет статус на `completed`

### Режим всех задач

**Активация**: Пользователь запрашивает "run all tasks"

**Процесс**:
1. Оркестратор читает tasks.md
2. Оркестратор помечает все незавершенные обязательные задачи как `queued`
3. Для каждой задачи последовательно:
   - Обновление статуса на `in_progress`
   - Делегирование spec-task-execution
   - Ожидание завершения
   - Обновление статуса на `completed`
4. Отчет о прогрессе после каждой задачи

---

## Формат задач

### Синтаксис checkbox

```markdown
- [ ] Не начата (обязательная задача)
- [x] Завершена
- [-] В процессе
- [~] В очереди
- [ ]* Опциональная задача (пропускается в "run all tasks")
```

### Иерархия задач

```markdown
- [ ] 1. Основная задача
  - [ ] 1.1 Подзадача первая
  - [ ] 1.2 Подзадача вторая
- [ ] 2. Другая основная задача
```

Агент обрабатывает подзадачи перед основной задачей.

---

## Обработка ошибок

### Ошибки тестирования

**Unit тесты упали**:
- Агент анализирует ошибки
- Пытается исправить код
- Перезапускает тесты
- Максимум 3 попытки

**PBT тесты упали**:
- Агент анализирует counterexample
- Исправляет логику
- Перезапускает с тем же seed
- Документирует найденные edge cases

### Ошибки компиляции

- Агент использует getDiagnostics
- Исправляет синтаксические ошибки
- Проверяет типы (TypeScript)
- Валидирует перед завершением

### Ошибки зависимостей

- Агент идентифицирует отсутствующие пакеты
- Устанавливает через npm/yarn
- Обновляет package.json
- Проверяет совместимость версий

---

## Специальные случаи

### Bugfix Workflow - Exploration Tests

**Task 1 в bugfix спецификациях**: "Write bug condition exploration property test"

**Особенность**: Тест ДОЛЖЕН упасть на багованном коде

**Ожидаемое поведение**:
- Тест падает → SUCCESS (баг подтвержден)
- Тест проходит → UNEXPECTED (баг не обнаружен)

**При unexpected pass**:
1. Агент использует updatePBTStatus с status='unexpected_pass'
2. Агент выводит детальный анализ
3. Агент запрашивает выбор пользователя:
   - "Continue anyway" - продолжить реализацию
   - "Re-investigate" - пересмотреть root cause

---

## Best Practices

### Подготовка к выполнению

1. Убедитесь, что спецификация полная (requirements + design)
2. Проверьте, что задачи четко сформулированы
3. Убедитесь, что зависимости установлены

### Мониторинг выполнения

- Следите за статусами задач в tasks.md
- Проверяйте результаты тестов
- Анализируйте ошибки при возникновении

### После выполнения

- Проверьте созданный код
- Запустите полный test suite
- Проверьте интеграцию с остальной системой

---

## Примеры реальных сценариев

### Сценарий 1: Выполнение одной задачи

**Контекст**: Спецификация user-authentication, задача 3

**Команда пользователя**: "execute task 3"

**Процесс**:
```
1. Оркестратор читает .kiro/specs/user-authentication/tasks.md
2. Находит Task 3: "Implement JWT token generation"
3. Обновляет статус на in_progress
4. Делегирует spec-task-execution с контекстом
5. Агент создает src/auth/tokenService.js
6. Агент пишет тесты
7. Агент запускает тесты (все проходят)
8. Оркестратор обновляет статус на completed
```

### Сценарий 2: Run all tasks

**Контекст**: Спецификация payment-processing с 5 задачами

**Команда пользователя**: "run all tasks"

**Процесс**:
```
1. Оркестратор читает tasks.md
2. Находит 5 незавершенных обязательных задач
3. Помечает все как queued
4. Последовательно для каждой:
   - Обновление на in_progress
   - Делегирование spec-task-execution
   - Ожидание завершения
   - Обновление на completed
5. Финальный отчет о выполнении всех задач
```

### Сценарий 3: Задача с PBT

**Контекст**: Задача требует correctness property

**Задача**: "Implement merge function with property: merged array is sorted"

**Процесс**:
```
1. Агент реализует merge функцию
2. Агент создает unit тесты
3. Агент создает PBT тест для свойства сортировки
4. Запускает PBT с 100 случайными входами
5. Все тесты проходят
6. Задача помечена как completed
```
