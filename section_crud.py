from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from app.database.mongodb import db

from app.models.section_model import (
    section_document
)


# ==========================================================
# SECTION PRIORITY
# ==========================================================

SECTION_PRIORITY = {

    "MCQ": 1,

    "DESCRIPTIVE": 2,

    "PDF": 3
}


# ==========================================================
# GET NEXT SECTION ORDER
# ==========================================================

def get_next_section_order(
    assessment_id: str,
    section_type: str
):

    # ------------------------------------------------------
    # CHECK IF SECTION TYPE ALREADY EXISTS
    # ------------------------------------------------------

    existing = db.sections.find_one(
        {
            "assessment_id":
                assessment_id,

            "section_type":
                section_type
        }
    )

    if existing:

        return None

    # ------------------------------------------------------
    # PRIORITY OF NEW SECTION
    # ------------------------------------------------------

    new_priority = SECTION_PRIORITY[
        section_type
    ]

    # ------------------------------------------------------
    # GET ALL EXISTING SECTIONS
    # ------------------------------------------------------

    sections = list(
        db.sections.find(
            {
                "assessment_id":
                    assessment_id
            }
        )
    )

    # ------------------------------------------------------
    # DETERMINE NEW ORDER
    #
    # MCQ       -> 1
    # DESCRIPTIVE -> 2
    # PDF       -> 3
    #
    # If a lower-priority section already exists,
    # shift it forward.
    # ------------------------------------------------------

    new_order = 1

    for section in sections:

        existing_priority = SECTION_PRIORITY[
            section["section_type"]
        ]

        if existing_priority < new_priority:

            new_order += 1

    # ------------------------------------------------------
    # SHIFT EXISTING SECTIONS
    # ------------------------------------------------------

    db.sections.update_many(

        {
            "assessment_id":
                assessment_id,

            "order": {
                "$gte":
                    new_order
            }
        },

        {
            "$inc": {
                "order":
                    1
            }
        }
    )

    return new_order


# ==========================================================
# CREATE SECTION
# ==========================================================

def create_section(
    section: dict
):

    document = section_document(
        section
    )

    result = db.sections.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    return document


# ==========================================================
# GET SECTION BY ID
# ==========================================================

def get_section_by_id(
    section_id: str
):

    try:

        return db.sections.find_one(
            {
                "_id":
                    ObjectId(
                        section_id
                    )
            }
        )

    except Exception:

        return None


# ==========================================================
# GET SECTIONS FOR ASSESSMENT
# ==========================================================

def get_assessment_sections(
    assessment_id: str
):

    return list(

        db.sections.find(
            {
                "assessment_id":
                    assessment_id
            }
        ).sort(
            "order",
            1
        )
    )


# ==========================================================
# UPDATE SECTION
# ==========================================================

def update_section(
    section_id: str,
    assessment_id: str,
    updates: dict
):

    if not updates:

        return get_section_by_id(
            section_id
        )

    updates["updated_at"] = (
        datetime.now(
            timezone.utc
        )
    )

    try:

        result = db.sections.find_one_and_update(

            {
                "_id":
                    ObjectId(
                        section_id
                    ),

                "assessment_id":
                    assessment_id
            },

            {
                "$set":
                    updates
            },

            return_document=ReturnDocument.AFTER
        )

        return result

    except Exception:

        return None


# ==========================================================
# DELETE SECTION
# ==========================================================

def delete_section(
    section_id: str,
    assessment_id: str
):

    try:

        section = db.sections.find_one(
            {
                "_id":
                    ObjectId(
                        section_id
                    ),

                "assessment_id":
                    assessment_id
            }
        )

        if not section:

            return False

        deleted = db.sections.delete_one(
            {
                "_id":
                    ObjectId(
                        section_id
                    ),

                "assessment_id":
                    assessment_id
            }
        )

        if deleted.deleted_count != 1:

            return False

        # --------------------------------------------------
        # REBUILD ORDER AFTER DELETE
        # --------------------------------------------------

        sections = get_assessment_sections(
            assessment_id
        )

        for index, current_section in enumerate(
            sections,
            start=1
        ):

            db.sections.update_one(

                {
                    "_id":
                        current_section["_id"]
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