from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TeachingPlanArtifact:
    objective_text: str
    plan: Any
    display_plan: str = ""
    extracted_concepts: Optional[List[Dict[str, str]]] = None


@dataclass(frozen=True)
class RetrievalRunArtifact:
    objective_text: str
    teaching_plan: Any
    results: List[Dict[str, Any]] = field(default_factory=list)
    coverage: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeachingContentArtifact:
    objective_text: str
    teaching_plan: Any
    teaching_content: str
    display_content: str
    retrieval_bundle: Dict[str, Any]
    extracted_concepts: Optional[List[Dict[str, str]]] = None


@dataclass(frozen=True)
class TurnAnalysisArtifact:
    analysis: Dict[str, Any]
    display_analysis: str = ""


@dataclass(frozen=True)
class GuidedSessionStateArtifact:
    session_id: str
    objective_id: str
    objective_text: str
    teaching_plan: Any
    teaching_content: str
    retrieval_bundle: Dict[str, Any]
    lesson_state: Optional[Dict[str, Any]] = None
    pacing_state: Optional[Dict[str, Any]] = None
    misconception_state: Optional[Dict[str, Any]] = None
    student_context: str = ""
    bundle: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GuidedTurnResult:
    metadata: Dict[str, Any]
    final_text: str = ""
    final_stage: str = ""
    stage_advanced: bool = False
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)

