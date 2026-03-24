"""
Unit tests for the eval JSON parser.

Tests extraction of structured evaluation data from Instance B LLM responses.
The LLM outputs conversational text followed by a ```json block.
"""

import pytest
from question_app.services.tutor.hybrid_system import HybridCrewAISocraticSystem


# Use the static method directly
parse = HybridCrewAISocraticSystem._parse_eval_json


class TestCleanExtraction:

    def test_valid_response_with_eval(self):
        response = '''I can see you're thinking about this the right way. Let me ask you: what would happen if a screen reader encountered that image?

```json
{
  "detected_state": "INCORRECT_APPLICATION",
  "response_mode": "RECTIFICATION",
  "stage_recommendation": "stay",
  "mastery_evidence": "Student understands alt text exists but applies incorrectly",
  "mastery_level_change": "no_change",
  "misconceptions_detected": ["All images need descriptive alt text"],
  "stage_summary": null,
  "confidence": 0.85
}
```'''
        text, eval_data = parse(response)
        assert "screen reader" in text
        assert "```json" not in text
        assert eval_data is not None
        assert eval_data["detected_state"] == "INCORRECT_APPLICATION"
        assert eval_data["response_mode"] == "RECTIFICATION"
        assert eval_data["confidence"] == 0.85
        assert len(eval_data["misconceptions_detected"]) == 1

    def test_advance_recommendation(self):
        response = '''Great work! You clearly understand this concept.

```json
{
  "detected_state": "CORRECT",
  "response_mode": "SUMMARIZATION",
  "stage_recommendation": "advance_to_mini_assessment",
  "mastery_evidence": "Student correctly explained decorative vs informative images",
  "mastery_level_change": "in_progress→partial",
  "misconceptions_detected": [],
  "stage_summary": "Student explored alt text through 5 exchanges, resolved decorative image misconception",
  "confidence": 0.92
}
```'''
        text, eval_data = parse(response)
        assert eval_data["stage_recommendation"] == "advance_to_mini_assessment"
        assert eval_data["mastery_level_change"] == "in_progress→partial"
        assert eval_data["stage_summary"] is not None
        assert eval_data["misconceptions_detected"] == []


class TestEdgeCases:

    def test_no_json_block(self):
        response = "Here's a simple explanation about alt text. Use empty alt for decorative images."
        text, eval_data = parse(response)
        assert text == response
        assert eval_data is None

    def test_malformed_json(self):
        response = '''Good question!

```json
{this is not valid json}
```'''
        text, eval_data = parse(response)
        assert "Good question" in text
        assert eval_data is None

    def test_empty_response(self):
        text, eval_data = parse("")
        assert text == ""
        assert eval_data is None

    def test_json_with_extra_whitespace(self):
        response = '''Response text here.

```json

{
  "detected_state": "CORRECT",
  "response_mode": "SUMMARIZATION",
  "stage_recommendation": "stay",
  "confidence": 0.9
}

```'''
        text, eval_data = parse(response)
        assert eval_data is not None
        assert eval_data["detected_state"] == "CORRECT"

    def test_partial_eval_keys(self):
        """Missing some keys should still return partial data."""
        response = '''Text.

```json
{
  "detected_state": "CORRECT",
  "response_mode": "SUMMARIZATION",
  "stage_recommendation": "stay",
  "confidence": 0.8
}
```'''
        text, eval_data = parse(response)
        assert eval_data is not None
        assert eval_data["detected_state"] == "CORRECT"
        # These optional keys are missing but that's fine
        assert "misconceptions_detected" not in eval_data

    def test_response_with_code_blocks_before_json(self):
        """Ensure we match the json block, not other code blocks."""
        response = '''Here's an example:

```html
<img src="logo.png" alt="Company logo">
```

That's how you add alt text.

```json
{
  "detected_state": "CORRECT",
  "response_mode": "GUIDANCE",
  "stage_recommendation": "stay",
  "confidence": 0.7
}
```'''
        text, eval_data = parse(response)
        assert eval_data is not None
        assert eval_data["response_mode"] == "GUIDANCE"
        assert "```html" in text  # HTML code block stays in conversational text
        assert "```json" not in text

    def test_conversational_text_preserved_clean(self):
        """Verify no trailing whitespace or artifacts in the conversational text."""
        response = '''Let me explain **SC 1.1.1**: Non-text content needs text alternatives.

- Informative images: describe the content
- Decorative images: use `alt=""`

```json
{"detected_state": "MISSING_PREREQUISITES", "response_mode": "GUIDANCE", "stage_recommendation": "stay", "confidence": 0.6}
```'''
        text, eval_data = parse(response)
        assert text.endswith('use `alt=""`')
        assert eval_data["detected_state"] == "MISSING_PREREQUISITES"
