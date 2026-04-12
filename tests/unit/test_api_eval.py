from question_app.api.eval import _build_rag_sample_analysis


def test_build_rag_sample_analysis_surfaces_instance_a_eval_signals():
    analysis = _build_rag_sample_analysis(
        {
            "id": "sample-123",
            "query": "What makes alt text effective?",
            "response": "Under WCAG 1.1.1, effective alt text describes the purpose of the image.",
            "eval_metrics_by_name": {
                "retrieval_context_count": {"value": 3.0, "details": {}},
                "retrieval_query_overlap": {"value": 0.75, "details": {}},
                "wcag_context_used": {"value": 1.0, "details": {}},
                "response_wcag_citation_present": {"value": 1.0, "details": {}},
                "response_wcag_citation_grounded": {"value": 1.0, "details": {"grounded_refs": ["1.1.1"]}},
            },
        }
    )

    assert analysis["sample"]["id"] == "sample-123"
    assert analysis["signals"]["retrieval_context_count"]["value"] == 3.0
    assert analysis["signals"]["retrieval_query_overlap"]["value"] == 0.75
    assert analysis["signals"]["response_wcag_citation_grounded"]["details"]["grounded_refs"] == ["1.1.1"]
