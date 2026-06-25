"""Application workspace constants."""

PROGRESS_WEIGHTS = {
    "profile_complete": 20,
    "documents_complete": 30,
    "sop_complete": 15,
    "lor_complete": 15,
    "submitted_complete": 20,
}

AUTO_TASK_TEMPLATES = [
    {
        "task_type": "upload_transcript",
        "title": "Upload official transcript",
        "description": "Upload your official academic transcript for this application.",
        "priority": "high",
        "sort_order": 1,
    },
    {
        "task_type": "generate_sop",
        "title": "Generate Statement of Purpose",
        "description": "Draft and refine your SOP tailored to this university program.",
        "priority": "high",
        "sort_order": 2,
    },
    {
        "task_type": "request_lor",
        "title": "Request recommendation letters",
        "description": "Contact referees and request 2-3 letters of recommendation.",
        "priority": "high",
        "sort_order": 3,
    },
    {
        "task_type": "pay_fee",
        "title": "Pay application fee",
        "description": "Complete the university application fee payment.",
        "priority": "medium",
        "sort_order": 4,
    },
    {
        "task_type": "submit_application",
        "title": "Submit application",
        "description": "Review all materials and submit your complete application.",
        "priority": "high",
        "sort_order": 5,
    },
    {
        "task_type": "visa_application",
        "title": "Prepare visa application",
        "description": "Begin student visa documentation after admission decision.",
        "priority": "medium",
        "sort_order": 6,
    },
]

DOCUMENT_TYPE_PROGRESS_MAP = {
    "transcript": "documents_complete",
    "cv": "documents_complete",
    "ielts": "documents_complete",
    "passport": "documents_complete",
    "financial": "documents_complete",
    "sop": "sop_complete",
    "lor": "lor_complete",
}

REQUIRED_DOCUMENT_TYPES = {"transcript", "cv", "sop", "lor"}
