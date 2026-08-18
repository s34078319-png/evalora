from datetime import datetime, timezone


# ==========================================================
# DEFAULT ANSWER EVALUATION CONFIGURATION
# ==========================================================
#
# These values are controlled by Evalora.
#
# Teachers do NOT provide them.
# ==========================================================

DEFAULT_KEYWORD_MATCHING_WEIGHT = 0.40

DEFAULT_SEMANTIC_SIMILARITY_WEIGHT = 0.60


# ==========================================================
# ASSESSMENT DOCUMENT
# ==========================================================

def assessment_document(
    assessment: dict
) -> dict:

    now = datetime.now(
        timezone.utc
    )

    document = {

        # --------------------------------------------------
        # TEACHER
        # --------------------------------------------------

        "teacher_id":
            assessment["teacher_id"],

        # --------------------------------------------------
        # BASIC INFORMATION
        # --------------------------------------------------

        "title":
            assessment["title"],

        "description":
            assessment.get(
                "description"
            ),

        # --------------------------------------------------
        # TARGET STUDENTS
        # --------------------------------------------------

        "branch":
            assessment["branch"],

        "semester":
            assessment["semester"],

        # --------------------------------------------------
        # TIMING
        # --------------------------------------------------

        "opening_time":
            assessment["opening_time"],

        "closing_time":
            assessment["closing_time"],

        "duration_minutes":
            assessment["duration_minutes"],

        # --------------------------------------------------
        # PDF UPLOAD DURATION
        # --------------------------------------------------

        "pdf_upload_duration_minutes":
            assessment.get(
                "pdf_upload_duration_minutes",
                0
            ),

        # --------------------------------------------------
        # PROCTORING
        # --------------------------------------------------

        "max_proctoring_flags":
            assessment["max_proctoring_flags"],

        # --------------------------------------------------
        # ANSWER EVALUATION
        # --------------------------------------------------

        "keyword_matching_weight":
            DEFAULT_KEYWORD_MATCHING_WEIGHT,

        "semantic_similarity_weight":
            DEFAULT_SEMANTIC_SIMILARITY_WEIGHT,

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        "status":
            "DRAFT",

        # --------------------------------------------------
        # TIMESTAMPS
        # --------------------------------------------------

        "created_at":
            now,

        "updated_at":
            now,

        "published_at":
            None
    }

    return document