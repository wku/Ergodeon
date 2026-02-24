Клиент оставил комментарии к сгенерированным документам планирования. Проанализируй комментарии и определи какие изменения нужно внести.

Комментарии клиента:
{client_comments}

Текущий чеклист:
{checklist}

Текущий walkthrough:
{walkthrough}

Текущий план имплементации:
{implementation_plan}

Для каждого комментария определи:

1. comment_type: тип комментария
   - "approve" - клиент одобряет без замечаний
   - "minor_edit" - мелкая правка, не меняет scope
   - "major_change" - существенное изменение, меняет scope или подход
   - "rejection" - клиент хочет отклонить и начать заново

2. affected_documents: какие документы затронуты (checklist, walkthrough, implementation_plan)
3. changes: конкретные изменения которые нужно внести
4. regeneration_needed: нужна ли полная перегенерация документа (устанавливай true только при major_change или rejection, иначе false)

Если комментарии противоречат друг другу, отметь это в поле conflicts.

Формат ответа строго JSON:
{{
  "comments_parsed": [
    {{
      "original_text": "строка",
      "comment_type": "approve|minor_edit|major_change|rejection",
      "affected_documents": ["строка"],
      "changes": ["строка"],
      "regeneration_needed": false
    }}
  ],
  "conflicts": ["строка"],
  "overall_status": "approved|needs_revision|rejected",
  "documents_to_regenerate": ["строка"]
}}
