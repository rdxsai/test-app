"""Shared model exports for the application."""

# Import the new, correct models from models/question.py
from .question import (
    AnswerUpdate,
    QuestionUpdate,
    NewAnswer,
    NewQuestion
)

from .tutor import (
    StudentProfile,
    KnowledgeLevel,
    SessionPhase,
    LearningObjective,
    Question,
    Answer
)

# This __all__ list tells Python what names to "export"
# from this package. This is what will fix your ImportError.
__all__ = [
    # From models/question.py
    "AnswerUpdate",
    "QuestionUpdate",
    "NewAnswer",
    "NewQuestion",
    
    # From models/tutor.py
    "StudentProfile",
    "KnowledgeLevel",
    "SessionPhase",
    "LearningObjective",
    "Question",
    "Answer"
]
