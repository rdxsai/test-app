import json
import re
import unicodedata
from pathlib import Path

root = Path('/Users/rfentres/projects/Merged-App-1')
combined_path = root / 'resources/deep/chat_attachments_combined/questions_combined_from_chat_attachments.json'
quiz_path = root / 'data/quiz_questions.json'

combined = json.loads(combined_path.read_text(encoding='utf-8'))['questions']
quiz = json.loads(quiz_path.read_text(encoding='utf-8'))

combined_ids = {
    q.get('question_canvas_id')
    for q in combined
    if q.get('question_canvas_id') is not None
}
quiz_ids = {q.get('id') for q in quiz if q.get('id') is not None}
missing_ids = sorted(quiz_ids - combined_ids)


def norm(text: str) -> str:
    text = unicodedata.normalize('NFKC', text or '')
    text = text.replace('\u00a0', ' ')
    text = re.sub(r'\s+', ' ', text).strip().casefold()
    return text

combined_texts = {norm(q.get('question_text_markdown', '')) for q in combined}
missing_by_text = [
    q for q in quiz
    if norm(q.get('question_text', '')) not in combined_texts
]

missing_id_rows = [
    {
        'id': q.get('id'),
        'assessment_question_id': q.get('assessment_question_id'),
        'question_text': q.get('question_text'),
    }
    for q in quiz
    if q.get('id') in set(missing_ids)
]

print('combined_count', len(combined))
print('quiz_count', len(quiz))
print('missing_by_id_count', len(missing_ids))
print('missing_by_text_count', len(missing_by_text))
print('missing_by_id_rows', json.dumps(missing_id_rows, ensure_ascii=False))
print(
    'missing_by_text_rows',
    json.dumps(
        [
            {
                'id': q.get('id'),
                'assessment_question_id': q.get('assessment_question_id'),
                'question_text': q.get('question_text'),
            }
            for q in missing_by_text
        ],
        ensure_ascii=False,
    ),
)
