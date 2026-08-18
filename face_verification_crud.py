from datetime import datetime, timezone

from pymongo import ReturnDocument

from app.database.mongodb import db

from app.models.face_verification_model import (
    face_verification_document
)


# ==========================================================
# GET FACE VERIFICATION RECORD
# ==========================================================


def get_face_verification(
    student_id: str
):

    return db.face_verifications.find_one(

        {
            "student_id":
                student_id
        }
    )


# ==========================================================
# CREATE FACE VERIFICATION RECORD
# ==========================================================


def create_face_verification(
    data: dict
):

    document = face_verification_document(
        data
    )

    result = db.face_verifications.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# GET OR CREATE FACE VERIFICATION RECORD
# ==========================================================


def get_or_create_face_verification(
    student_id: str
):

    existing = get_face_verification(
        student_id
    )

    if existing:

        return existing

    return create_face_verification({

        "student_id":
            student_id,

        "enrolled":
            False,

        "verified":
            False,

        "face_embedding":
            None,

        "last_verified_at":
            None,

        "verification_attempts":
            0,

        "failed_verifications":
            0
    })


# ==========================================================
# ENROLL FACE
# ==========================================================
#
# At this stage this function only stores the face
# representation supplied by the future face-verification
# engine.
#
# The actual embedding generation will be implemented later.
# ==========================================================


def enroll_face(
    student_id: str,
    face_embedding
):

    now = datetime.now(
        timezone.utc
    )

    result = db.face_verifications.find_one_and_update(

        {
            "student_id":
                student_id
        },

        {
            "$set": {

                "enrolled":
                    True,

                "verified":
                    False,

                "face_embedding":
                    face_embedding,

                "last_verified_at":
                    None,

                "verification_attempts":
                    0,

                "failed_verifications":
                    0,

                "updated_at":
                    now
            }
        },

        upsert=True,

        return_document=
            ReturnDocument.AFTER
    )

    return result


# ==========================================================
# MARK FACE VERIFIED
# ==========================================================


def mark_face_verified(
    student_id: str
):

    now = datetime.now(
        timezone.utc
    )

    result = db.face_verifications.find_one_and_update(

        {
            "student_id":
                student_id
        },

        {
            "$set": {

                "verified":
                    True,

                "last_verified_at":
                    now,

                "updated_at":
                    now
            },

            "$inc": {

                "verification_attempts":
                    1
            }
        },

        return_document=
            ReturnDocument.AFTER
    )

    return result


# ==========================================================
# MARK FACE VERIFICATION FAILED
# ==========================================================


def mark_face_verification_failed(
    student_id: str
):

    now = datetime.now(
        timezone.utc
    )

    result = db.face_verifications.find_one_and_update(

        {
            "student_id":
                student_id
        },

        {
            "$set": {

                "verified":
                    False,

                "updated_at":
                    now
            },

            "$inc": {

                "verification_attempts":
                    1,

                "failed_verifications":
                    1
            }
        },

        return_document=
            ReturnDocument.AFTER
    )

    return result


# ==========================================================
# RESET VERIFICATION
# ==========================================================
#
# Used when a new assessment session starts.
#
# The student's enrolled face remains.
#
# Only the current verification state is reset.
# ==========================================================


def reset_face_verification(
    student_id: str
):

    now = datetime.now(
        timezone.utc
    )

    result = db.face_verifications.find_one_and_update(

        {
            "student_id":
                student_id
        },

        {
            "$set": {

                "verified":
                    False,

                "updated_at":
                    now
            }
        },

        return_document=
            ReturnDocument.AFTER
    )

    return result