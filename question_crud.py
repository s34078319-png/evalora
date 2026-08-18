from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.database.mongodb import db

from app.models.question_model import (
    question_document
)


# ==========================================================
# GET NEXT QUESTION ORDER
# ==========================================================

def get_next_question_order(
    section_id: str
) -> int:

    last_question = db.questions.find_one(

        {
            "section_id":
                section_id
        },

        sort=[
            (
                "order",
                -1
            )
        ]
    )

    if not last_question:

        return 1

    return (
        last_question["order"]
        + 1
    )


# ==========================================================
# CREATE QUESTION
# ==========================================================

def create_question(
    question: dict
):

    document = question_document(
        question
    )

    result = db.questions.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# GET QUESTION BY ID
# ==========================================================

def get_question_by_id(
    question_id: str
):

    try:

        return db.questions.find_one(

            {
                "_id":
                    ObjectId(
                        question_id
                    )
            }
        )

    except Exception:

        return None


# ==========================================================
# GET QUESTIONS FOR SECTION
# ==========================================================

def get_section_questions(
    section_id: str
):

    return list(

        db.questions.find(

            {
                "section_id":
                    section_id
            }

        ).sort(

            "order",
            1
        )
    )


# ==========================================================
# UPDATE QUESTION
# ==========================================================

def update_question(
    question_id: str,
    section_id: str,
    updates: dict
):

    if not updates:

        return get_question_by_id(
            question_id
        )

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    try:

        result = db.questions.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        question_id
                    ),

                "section_id":
                    section_id
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
# DELETE QUESTION
# ==========================================================

def delete_question(
    question_id: str,
    section_id: str
):

    try:

        deleted = db.questions.delete_one(

            {
                "_id":
                    ObjectId(
                        question_id
                    ),

                "section_id":
                    section_id
            }
        )

        if deleted.deleted_count != 1:

            return False

        # --------------------------------------------------
        # REBUILD QUESTION ORDER
        # --------------------------------------------------

        questions = get_section_questions(
            section_id
        )

        for index, question in enumerate(
            questions,
            start=1
        ):

            db.questions.update_one(

                {
                    "_id":
                        question["_id"]
                },

                {
                    "$set": {

                        "order":
                            index,

                        "updated_at":
                            datetime.now(
                                timezone.utc
                            )
                    }
                }
            )

        return True

    except Exception:

        return False