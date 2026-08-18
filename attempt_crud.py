from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.database.mongodb import db

from app.models.attempt_model import (
    attempt_document
)


# ==========================================================
# CREATE ATTEMPT
# ==========================================================

def create_attempt(
    attempt: dict
):

    document = attempt_document(
        attempt
    )

    result = db.attempts.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# GET ATTEMPT BY ID
# ==========================================================

def get_attempt_by_id(
    attempt_id: str
):

    try:

        return db.attempts.find_one(

            {
                "_id":
                    ObjectId(
                        attempt_id
                    )
            }
        )

    except Exception:

        return None


# ==========================================================
# GET STUDENT ATTEMPT FOR ASSESSMENT
# ==========================================================

def get_student_attempt(
    student_id: str,
    assessment_id: str
):

    return db.attempts.find_one(

        {
            "student_id":
                student_id,

            "assessment_id":
                assessment_id
        }
    )


# ==========================================================
# GET STUDENT ATTEMPTS
# ==========================================================

def get_student_attempts(
    student_id: str
):

    return list(

        db.attempts.find(

            {
                "student_id":
                    student_id
            }

        ).sort(

            "created_at",
            -1
        )
    )


# ==========================================================
# UPDATE ATTEMPT
# ==========================================================

def update_attempt(
    attempt_id: str,
    updates: dict
):

    if not updates:

        return get_attempt_by_id(
            attempt_id
        )

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    try:

        result = db.attempts.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        attempt_id
                    )
            },

            {
                "$set":
                    updates
            },

            return_document=
                ReturnDocument.AFTER
        )

        return result

    except Exception:

        return None


# ==========================================================
# COMPLETE ATTEMPT
# ==========================================================

def complete_attempt(
    attempt_id: str,
    completion_reason: str
):

    now = datetime.now(
        timezone.utc
    )

    try:

        result = db.attempts.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        attempt_id
                    ),

                "completed":
                    False
            },

            {
                "$set": {

                    "completed":
                        True,

                    "submitted_at":
                        now,

                    "completion_reason":
                        completion_reason,

                    "updated_at":
                        now
                }
            },

            return_document=
                ReturnDocument.AFTER
        )

        return result

    except Exception:

        return None