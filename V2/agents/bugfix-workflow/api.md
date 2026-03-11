# Bugfix Workflow Agent - API Documentation

## Описание

Специализированный агент для систематического исправления багов с использованием методологии bug condition. Следует процессу: определение условия бага → дизайн исправления → реализация с проверками.

---

## API Вызова

### Метод вызова
```
invokeSubAgent
```

### Обязательные параметры

#### name
- **Тип**: `string`
- **Значение**: `"bugfix-workflow"`
- **Описание**: Идентификатор агента

#### prompt
- **Тип**: `string`
- **Описание**: Описание бага с контекстом
- **Формат**: Симптомы, воспроизведение, ожидаемое поведение

#### explanation
- **Тип**: `string`
- **Описание**: Причина вызова агента
- **Формат**: Краткое объяснение

#### preset
- **Тип**: `string`
- **Значение**: `"requirements"` | `"design"` | `"tasks"`
- **Описание**: Фаза bugfix workflow

---

## Входные данные

### Структура prompt

#### Для фазы "requirements"
```
Описание бага:
- Симптомы и проявления
- Шаги для воспроизведения
- Ожидаемое vs фактическое поведение
- Контекст возникновения
- Feature name в kebab-case
```

#### Для фазы "design"
```
Ссылка на bugfix.md + запрос на план исправления
```

#### Для фазы "tasks"
```
Ссылки на bugfix.md и design.md + запрос на задачи
```

### Примеры входных данных

#### Пример 1: Requirements фаза
```json
{
  "name": "bugfix-workflow",
  "preset": "requirements",
  "prompt": "Приложение падает с ошибкой 'Division by zero' когда пользователь вводит количество 0 в форме заказа. Ожидается: показ сообщения об ошибке валидации. Фактически: crash приложения. Feature name: quantity-zero-crash",
  "explanation": "Начало bugfix workflow для crash при нулевом количестве"
}
```

#### Пример 2: Design фаза
```json
{
  "name": "bugfix-workflow",
  "preset": "design",
  "prompt": "Bug condition для quantity-zero-crash определено и одобрено. Создай план исправления.",
  "explanation": "Проектирование решения для исправления бага"
}
```

---

## Выходные данные

### Фаза "requirements"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/bugfix.md`
- `.kiro/specs/{feature_name}/.config.kiro`

#### Содержание bugfix.md
1. **Bug Description**: Детальное описание бага
2. **Reproduction Steps**: Шаги воспроизведения
3. **Root Cause Analysis**: Анализ первопричины
4. **Bug Condition C(X)**: Формальное условие, определяющее баг
5. **Expected Behavior**: Ожидаемое поведение
6. **Impact Assessment**: Оценка влияния бага

#### Пример выхода
```markdown
Создан bugfix документ для quantity-zero-crash:

Bug Condition C(X): quantity === 0 AND calculateTotal() вызывается
Root Cause: Отсутствует проверка на ноль перед делением
Impact: Critical - приложение падает для всех пользователей
Affected Code: src/utils/orderCalculations.js:45

Файл: .kiro/specs/quantity-zero-crash/bugfix.md
```

---

### Фаза "design"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/design.md`

#### Содержание design.md
1. **Fix Strategy**: Стратегия исправления
2. **Code Changes**: Планируемые изменения кода
3. **Preservation Checking**: Как проверить, что исправление не ломает существующую функциональность
4. **Fix Checking**: Как проверить, что баг исправлен
5. **Testing Strategy**: Стратегия тестирования

#### Пример выхода
```markdown
Создан план исправления для quantity-zero-crash:

Fix Strategy: Добавить валидацию quantity перед расчетами
Code Changes: 
- Добавить проверку в calculateTotal()
- Показывать ошибку валидации в UI
Preservation: Unit тесты для существующих сценариев
Fix Checking: Exploration test должен пройти после исправления

Файл: .kiro/specs/quantity-zero-crash/design.md
```

---

### Фаза "tasks"

#### Создаваемые файлы
- `.kiro/specs/{feature_name}/tasks.md`

#### Содержание tasks.md

Специальная структура для bugfix:

```markdown
- [ ] 1. Write bug condition exploration property test
  - Тест должен УПАСТЬ на багованном коде
  - Подтверждает наличие бага
  
- [ ] 2. Implement fix
  - Исправление кода
  
- [ ] 3. Preservation checking
  - Проверка, что существующая функциональность не сломана
  
- [ ] 4. Fix checking  
  - Проверка, что exploration test теперь проходит
```

---

## Ключевые концепции

### Bug Condition C(X)

Формальное условие, которое определяет, когда баг проявляется.

**Формат**: `C(X) = [условие на входные данные X]`

**Примеры**:
- `C(quantity) = quantity === 0`
- `C(email) = email.includes('@') === false`
- `C(array) = array.length > 1000`

### Exploration Test

Специальный property-based тест для Task 1.

**Цель**: Подтвердить наличие бага

**Ожидаемое поведение**:
- На багованном коде: ДОЛЖЕН УПАСТЬ ✅
- После исправления: ДОЛЖЕН ПРОЙТИ ✅

**Unexpected Pass**: Если тест проходит на багованном коде
- Означает: тест не обнаруживает баг
- Действие: Агент запрашивает выбор пользователя
  - "Continue anyway" - продолжить реализацию
  - "Re-investigate" - пересмотреть root cause

### Preservation Checking

Проверка, что исправление не нарушает существующую функциональность.

**Методы**:
- Запуск существующих unit тестов
- Regression тесты
- Integration тесты

### Fix Checking

Проверка, что баг действительно исправлен.

**Методы**:
- Exploration test теперь проходит
- Ручное тестирование сценария
- Проверка bug condition C(X)

---

## Когда использовать

### ✅ Используйте bugfix-workflow когда:

- Что-то сломано или падает
- Существующее поведение некорректно
- Обнаружена регрессия
- Нужно систематическое исправление
- Важна формальная проверка корректности
- Баг критичный и требует документирования

### ❌ НЕ используйте bugfix-workflow когда:

- Добавляете новую функцию (используйте feature workflows)
- Делаете рефакторинг без бага
- Баг тривиальный (опечатка) - используйте general-task-execution
- Нужна только быстрая правка

---

## Примеры использования

### Пример 1: Crash баг

**Сценарий**: Приложение падает при определенном вводе

**Полный workflow**:
```javascript
// Фаза 1 - Requirements
invokeSubAgent({
  name: "bugfix-workflow",
  preset: "requirements",
  prompt: "Приложение падает с 'Cannot read property of undefined' когда пользователь кликает на notification без message field. Происходит в NotificationList компоненте. Feature name: notification-undefined-crash",
  explanation: "Определение bug condition для crash в notifications"
})

// Результат: bugfix.md с C(notification) = notification.message === undefined

// Фаза 2 - Design
invokeSubAgent({
  name: "bugfix-workflow",
  preset: "design",
  prompt: "Bug condition определено. Создай план исправления для notification-undefined-crash.",
  explanation: "Проектирование исправления для notification crash"
})

// Результат: design.md с планом добавления null checks

// Фаза 3 - Tasks
invokeSubAgent({
  name: "bugfix-workflow",
  preset: "tasks",
  prompt: "Создай задачи для исправления notification-undefined-crash.",
  explanation: "Создание плана реализации исправления"
})

// Результат: tasks.md с exploration test, fix, и проверками
```

---

### Пример 2: Logic баг

**Сценарий**: Неправильный расчет скидки

**Workflow**:
```javascript
invokeSubAgent({
  name: "bugfix-workflow",
  preset: "requirements",
  "prompt": "Функция calculateDiscount возвращает неправильный результат когда применяется несколько скидок одновременно. Ожидается: скидки применяются последовательно. Фактически: скидки суммируются, что дает неправильный итог. Feature name: discount-calculation-bug",
  explanation: "Анализ бага в логике расчета скидок"
})
```

---

## Специальная обработка Task 1

### Exploration Test - Критическое поведение

Task 1 всегда: "Write bug condition exploration property test"

**Нормальный случай (тест падает)**:
```
1. Агент создает exploration test
2. Тест запускается на багованном коде
3. Тест ПАДАЕТ (находит counterexample)
4. Агент использует updatePBTStatus с status='passed'
5. Документирует counterexample
6. Переходит к Task 2
```

**Проблемный случай (тест проходит)**:
```
1. Агент создает exploration test
2. Тест запускается на багованном коде
3. Тест ПРОХОДИТ (не находит баг)
4. Агент использует updatePBTStatus с status='unexpected_pass'
5. Агент выводит детальный анализ
6. Агент запрашивает выбор пользователя
7. ОСТАНАВЛИВАЕТСЯ до получения ответа
```

---

## Интеграция с другими агентами

### Типичная последовательность

```
context-gatherer (опционально) → bugfix-workflow → spec-task-execution
```

### Пример полного процесса

```javascript
// 1. Сбор контекста (если баг сложный)
invokeSubAgent({
  name: "context-gatherer",
  prompt: "Найди все файлы, связанные с discount calculation",
  explanation: "Поиск кода для расследования бага"
})

// 2. Создание bugfix спецификации
invokeSubAgent({
  name: "bugfix-workflow",
  preset: "requirements",
  prompt: "Баг в discount calculation...",
  explanation: "Документирование бага"
})

// 3. Выполнение исправления
// После создания tasks.md через bugfix-workflow
invokeSubAgent({
  name: "spec-task-execution",
  prompt: "Execute task 1 from .kiro/specs/discount-calculation-bug/",
  explanation: "Создание exploration test"
})
```


## Best Practices

### Определение Bug Condition

✅ **Хорошо**:
```
C(input) = input.quantity === 0 AND calculatePrice вызывается
```

❌ **Плохо**:
```
"Баг происходит иногда"
```

### Root Cause Analysis

1. Воспроизведите баг надежно
2. Найдите точное место в коде
3. Определите первопричину (не симптом)
4. Сформулируйте формальное условие C(X)

### Exploration Test Design

Тест должен:
- Генерировать входы, удовлетворяющие C(X)
- Проверять, что баг проявляется
- Быть детерминированным (с seed)
- Документировать counterexamples

---

## Примеры реальных багов

### Пример 1: Null pointer crash

**Bug Condition**: `C(user) = user.profile === null`

**Exploration Test**:
```javascript
test('crash on null profile', () => {
  fc.assert(
    fc.property(fc.record({ profile: fc.constant(null) }), (user) => {
      expect(() => displayUserName(user)).toThrow();
    })
  );
});
```

### Пример 2: Off-by-one error

**Bug Condition**: `C(array) = array.length > 0 AND index === array.length`

**Exploration Test**:
```javascript
test('index out of bounds', () => {
  fc.assert(
    fc.property(fc.array(fc.integer(), { minLength: 1 }), (arr) => {
      expect(() => getElement(arr, arr.length)).toThrow();
    })
  );
});
```

### Пример 3: Race condition

**Bug Condition**: `C(requests) = requests.length > 1 AND concurrent === true`

**Exploration Test**:
```javascript
test('race condition on concurrent requests', async () => {
  const requests = [updateUser(1), updateUser(1)];
  const results = await Promise.all(requests);
  // Проверка на data corruption
});
```

---

## Ограничения

### Применимость

- Подходит для воспроизводимых багов
- Требует четкого понимания симптомов
- Может быть избыточным для тривиальных багов

### Сложность

- Требует формализации bug condition
- Exploration test может быть сложным для некоторых багов
- Не все баги легко выразить через C(X)

---

## Конфигурация

### Файл .config.kiro

```json
{
  "specType": "bugfix",
  "workflowType": "requirements-first",
  "featureName": "bug-name"
}
```

Bugfix всегда использует requirements-first подход.

---

## Сравнение с Feature Workflows

| Аспект | Bugfix Workflow | Feature Workflow |
|--------|----------------|------------------|
| Цель | Исправить сломанное | Создать новое |
| Документ требований | bugfix.md | requirements.md |
| Фокус | Bug condition C(X) | User stories |
| Task 1 | Exploration test (должен упасть) | Обычная реализация |
| Проверки | Preservation + Fix | Acceptance criteria |

---

## Интеграция с CI/CD

### Regression Prevention

После исправления:
1. Exploration test добавляется в test suite
2. Становится regression test
3. Предотвращает повторное появление бага
4. Документирует edge case

### Continuous Monitoring

- Exploration tests запускаются в CI
- Мониторинг на production
- Алерты при регрессии

---

## Troubleshooting

### Проблема: Не могу воспроизвести баг

**Решение**:
- Соберите больше информации от пользователей
- Проверьте логи и error reports
- Используйте context-gatherer для анализа
- Попробуйте разные окружения

### Проблема: Exploration test проходит

**Решение**:
- Пересмотрите bug condition C(X)
- Проверьте, что баг еще существует
- Уточните root cause analysis
- Используйте опцию "Re-investigate"

### Проблема: Fix ломает другую функциональность

**Решение**:
- Запустите полный test suite
- Проверьте preservation tests
- Пересмотрите стратегию исправления
- Рассмотрите альтернативные подходы
