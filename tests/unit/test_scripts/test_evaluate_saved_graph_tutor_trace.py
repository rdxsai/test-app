import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "evaluate_saved_graph_tutor_trace.py"
)
SPEC = importlib.util.spec_from_file_location("evaluate_saved_graph_tutor_trace", SCRIPT_PATH)
evaluator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evaluator)


def test_compact_trace_keeps_graph_and_analysis_signals():
    compacted = evaluator.compact_trace(
        {
            "run_id": "run-1",
            "objective_id": "obj-1",
            "objective_text": "Teach alt text.",
            "models": {"tutor": "gpt-5.4"},
            "turns": [
                {
                    "turn": 1,
                    "student_message": "I think every image needs long alt text.",
                    "tutor_response": "Decorative images can be ignored.",
                    "stage_before": "introduction",
                    "stage_after": "concept",
                    "ws_events": [
                        {"type": "token", "text": "x"},
                        {
                            "type": "turn_analysis",
                            "analysis": {"stage_action": "stay"},
                        },
                    ],
                    "graph_decision": {"graph_action": "stay"},
                    "graph_state_after": {"active_node_id": "purpose"},
                    "trace": {
                        "events": [{"name": "turn_analyzer"}],
                        "timings": {"turn_analyzer": 1.2},
                    },
                }
            ],
        }
    )

    turn = compacted["turns"][0]
    assert turn["turn_analysis"] == {"stage_action": "stay"}
    assert turn["graph_decision"] == {"graph_action": "stay"}
    assert turn["graph_state_after"] == {"active_node_id": "purpose"}
    assert turn["trace_event_names"] == ["turn_analyzer"]


def test_evaluator_prompt_preserves_fix_constraints():
    prompt = evaluator.build_evaluator_prompt({"turns": []})

    assert "model/prompt/agent behavior failures" in prompt
    assert "information-source gaps" in prompt
    assert "wrong parameter" in prompt
    assert "do not propose deterministic backend-driven instructional rules" in prompt
    assert "evaluator-optimizer" in prompt


def test_render_markdown_contains_key_sections(tmp_path):
    report = {
        "overall_score": 7.5,
        "verdict": "Useful with pacing issues.",
        "teaching_sufficiency": {"rationale": "Enough examples for review."},
        "model_or_prompt_failures": [
            {
                "severity": "medium",
                "turns": [2],
                "summary": "Advanced early.",
                "evidence": "Turn 2 decision.",
            }
        ],
        "mcp_source_gaps": [],
        "tool_call_failures": [],
        "prompt_or_agent_fixes": [
            {
                "priority": "high",
                "target": "analyzer",
                "change": "Tighten closure contract.",
                "expected_effect": "Fewer early advances.",
            }
        ],
        "per_turn_notes": [
            {
                "turn": 1,
                "orchestrator": "Stayed.",
                "analyzer": "Consistent.",
                "tutor": "Clear.",
                "student_learning_value": "High.",
            }
        ],
    }

    markdown = evaluator.render_markdown(report, tmp_path / "trace.json", tmp_path / "out.json")

    assert "# Saved Graph Tutor Trace Evaluation" in markdown
    assert "## Model Or Prompt Failures" in markdown
    assert "## MCP Source Gaps" in markdown
    assert "Tighten closure contract." in markdown
