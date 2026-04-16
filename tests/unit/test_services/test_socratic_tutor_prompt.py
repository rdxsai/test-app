from question_app.services.tutor.prompts.socratic_tutor import (
    FIRST_TURN_INSTRUCTION,
    TUTOR_SYSTEM_PROMPT,
    build_instance_a_prompt,
    build_instance_b_prompt,
)


def test_build_instance_a_prompt_uses_compact_instance_a_rules():
    prompt = build_instance_a_prompt()

    assert "You are a web accessibility tutor focused on clear, practical teaching for beginners." in prompt
    assert "=== INSTANCE A RESPONSE STYLE ===" in prompt
    assert "=== INSTANCE A TEACHING FLOW ===" in prompt
    assert "=== INSTANCE A MISCONCEPTIONS ===" in prompt
    assert "You are a warm, patient tutor teaching web accessibility (WCAG 2.2)." not in prompt
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
    assert "Adapt vocabulary and examples to the student context above." in prompt
    assert "Cite specific WCAG criteria when available." in prompt


# ----------------------------------------------------------------------
# Anti-echo discipline for new-concept introductions (Instance B).
# These are regression guards for the bug where the tutor would name two
# options ("button vs div") and ask the learner to pick which is which.
# ----------------------------------------------------------------------

def test_first_turn_instruction_defaults_to_anchor_first_and_bans_echo_questions():
    text = FIRST_TURN_INSTRUCTION
    # Anchor-first is the default, with a concrete template.
    assert "ANCHOR-FIRST" in text
    assert "<button>" in text and "<div>" in text  # template uses real HTML examples
    # Hard anti-rules name the specific bad-pattern shape that triggered the rewrite.
    assert "Name both options and then ask the learner to pick which is which" in text or \
           "Name both options" in text
    assert "Include the answer in the question text" in text
    assert "restate, label, or recall a fact you just gave" in text
    # End-cleanly escape hatch is preserved.
    assert "end the turn cleanly" in text.lower() or "end the turn on the explanation" in text.lower()


def test_tutor_system_prompt_carries_new_concept_probe_guide():
    text = TUTOR_SYSTEM_PROMPT
    # New section header present.
    assert "INTRODUCING A NEW CONCEPT" in text
    # Forbidden shapes section names the specific bad pattern.
    assert "Naming both candidates" in text
    assert "Including the answer in the question text" in text
    assert "repeat or restate a label, definition, or fact" in text
    # Acceptable shapes give actionable templates.
    assert "Apply to a FRESH example" in text
    assert "Predict a consequence" in text
    assert "Spot the failure" in text


def test_build_instance_b_prompt_propagates_new_concept_probe_guide():
    """The assembled tutor prompt must carry the anti-echo guidance —
    if it ever stops appearing, the model will start producing the old
    "A button is X; a div is not. Which one ..." pattern again."""
    prompt = build_instance_b_prompt(
        knowledge_context="ev pack",
        student_context="lvl 1",
    )
    assert "INTRODUCING A NEW CONCEPT" in prompt
    assert "Naming both candidates" in prompt
    assert "Apply to a FRESH example" in prompt
