from question_app.services.tutor.prompts.socratic_tutor import build_instance_a_prompt


def test_build_instance_a_prompt_uses_compact_instance_a_rules():
    prompt = build_instance_a_prompt()

    assert "=== INSTANCE A RESPONSE STYLE ===" in prompt
    assert "=== INSTANCE A TEACHING FLOW ===" in prompt
    assert "=== INSTANCE A MISCONCEPTIONS ===" in prompt
    assert "=== HOW TO TEACH (INTRODUCTION PHASE) ===" not in prompt
    assert "=== WHEN THE STUDENT SAYS SOMETHING WRONG ===" not in prompt
    assert "Example 1 — Misconception during introduction:" not in prompt
    assert "=== EXAMPLES OF GOOD TUTORING ===" not in prompt


def test_build_instance_a_prompt_includes_context_blocks_when_present():
    prompt = build_instance_a_prompt(
        knowledge_context="SC 1.1.1 Non-text Content",
        student_context="Student level: beginner",
    )

    assert "Student level: beginner" in prompt
    assert "KNOWLEDGE BASE CONTEXT:\nSC 1.1.1 Non-text Content" in prompt
    assert "cite specific success criterion naturally" in prompt
