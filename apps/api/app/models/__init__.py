from app.models.ai_planner import PlannerHistory, PlannerNotification, PlannerSchedule, PlannerTask
from app.models.application import (
    Application,
    ApplicationActivity,
    ApplicationDeadline,
    ApplicationDocument,
    ApplicationNote,
    ApplicationTask,
)
from app.models.chat_session import ChatSession
from app.models.document_intelligence import DocumentProcessingJob, DocumentUpload
from app.models.digital_twin import StudentDigitalTwin, TwinEvent, TwinTimelineEntry
from app.models.ingestion import IngestionJob, IngestionJobItem, IngestionSource, UniversityFingerprint
from app.models.knowledge_document import KnowledgeDocument
from app.models.profile_analysis import ProfileAnalysis
from app.models.recommendation import RecommendationHistory
from app.models.scholarship_recommendation import ScholarshipRecommendationHistory
from app.models.scholarship import Scholarship
from app.models.sop_studio import (
    SOPCollaborationSession,
    SOPComment,
    SOPDocument,
    SOPHistory,
    SOPVersion,
)
from app.models.student_profile import StudentProfile
from app.models.university import Program, University
from app.models.user import User

__all__ = [
    "User",
    "StudentProfile",
    "University",
    "Program",
    "Scholarship",
    "Application",
    "ApplicationDocument",
    "ApplicationTask",
    "ApplicationNote",
    "ApplicationActivity",
    "ApplicationDeadline",
    "DocumentUpload",
    "DocumentProcessingJob",
    "PlannerHistory",
    "PlannerTask",
    "PlannerSchedule",
    "PlannerNotification",
    "ChatSession",
    "StudentDigitalTwin",
    "TwinEvent",
    "TwinTimelineEntry",
    "IngestionSource",
    "IngestionJob",
    "IngestionJobItem",
    "UniversityFingerprint",
    "RecommendationHistory",
    "ProfileAnalysis",
    "KnowledgeDocument",
    "ScholarshipRecommendationHistory",
    "SOPDocument",
    "SOPVersion",
    "SOPComment",
    "SOPHistory",
    "SOPCollaborationSession",
]
