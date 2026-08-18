from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.schemas.section_schema import (
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionType
)

from app.crud.section_crud import (
    create_section,
    get_section_by_id,
    get_assessment_sections,
    update_section,
    delete_section,
    get_next_section_order
)

from app.crud.assessment_crud import (
    get_assessment_by_id
)

from app.dependencies.auth_dependencies import (
    require_teacher
)


router = APIRouter(
    prefix="/teacher/assessments",
    tags=["Assessment Sections"]
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
# SERIALIZE SECTION
# ==========================================================

def serialize_section(
    section: dict
):

    return {

        "id":
            str(
                section["_id"]
            ),

        "assessment_id":
            section["assessment_id"],

        "title":
            section["title"],

        "section_type":
            section["section_type"],

        "order":
            section["order"],

        "created_at":
            section["created_at"],

        "updated_at":
            section["updated_at"]
    }


# ==========================================================
# CREATE SECTION
# ==========================================================
#
# Automatically maintains:
#
# MCQ -> DESCRIPTIVE -> PDF
#
# Examples:
#
# Create PDF
#       PDF
#
# Then create MCQ
#       MCQ
#       PDF
#
# Then create DESCRIPTIVE
#       MCQ
#       DESCRIPTIVE
#       PDF
#
# ==========================================================

@router.post(
    "/{assessment_id}/sections",
    response_model=SectionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_section(

    assessment_id: str,

    data: SectionCreate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    # ======================================================
    # OWNERSHIP
    # ======================================================

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    # ======================================================
    # ONLY DRAFT
    # ======================================================

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Sections can only be added "
                "to draft assessments."
            )
        )

    # ======================================================
    # SECTION TYPE
    # ======================================================

    section_type = (
        data.section_type.value
    )

    # ======================================================
    # ONLY ONE SECTION OF EACH TYPE
    # ======================================================

    existing_sections = (
        get_assessment_sections(
            assessment_id
        )
    )

    for section in existing_sections:

        if section["section_type"] == section_type:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{section_type} section "
                    "already exists."
                )
            )

    # ======================================================
    # MAXIMUM THREE SECTIONS
    # ======================================================

    if len(existing_sections) >= 3:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "An assessment can contain "
                "at most three sections."
            )
        )

    # ======================================================
    # CALCULATE ORDER
    # ======================================================

    new_priority = SECTION_PRIORITY[
        section_type
    ]

    new_order = 1

    for section in existing_sections:

        existing_priority = SECTION_PRIORITY[
            section["section_type"]
        ]

        if existing_priority < new_priority:

            new_order += 1

    # ======================================================
    # SHIFT EXISTING SECTIONS
    # ======================================================

    for section in existing_sections:

        if section["order"] >= new_order:

            from app.database.mongodb import db

            db.sections.update_one(

                {
                    "_id":
                        section["_id"]
                },

                {
                    "$inc": {
                        "order": 1
                    }
                }
            )

    # ======================================================
    # CREATE
    # ======================================================

    section = create_section(

        {

            "assessment_id":
                assessment_id,

            "title":
                data.title,

            "section_type":
                section_type,

            "order":
                new_order
        }
    )

    return serialize_section(
        section
    )


# ==========================================================
# GET ALL SECTIONS
# ==========================================================

@router.get(
    "/{assessment_id}/sections",
    response_model=list[SectionResponse]
)
def get_sections(

    assessment_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    sections = get_assessment_sections(
        assessment_id
    )

    return [

        serialize_section(
            section
        )

        for section in sections
    ]


# ==========================================================
# GET ONE SECTION
# ==========================================================

@router.get(
    "/{assessment_id}/sections/{section_id}",
    response_model=SectionResponse
)
def get_one_section(

    assessment_id: str,

    section_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    section = get_section_by_id(
        section_id
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found."
        )

    if section["assessment_id"] != assessment_id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Section does not belong "
                "to this assessment."
            )
        )

    return serialize_section(
        section
    )


# ==========================================================
# UPDATE SECTION
# ==========================================================

@router.put(
    "/{assessment_id}/sections/{section_id}",
    response_model=SectionResponse
)
def update_existing_section(

    assessment_id: str,

    section_id: str,

    data: SectionUpdate,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Published assessment "
                "sections cannot be edited."
            )
        )

    section = get_section_by_id(
        section_id
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found."
        )

    if section["assessment_id"] != assessment_id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Section does not belong "
                "to this assessment."
            )
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    updated = update_section(

        section_id,

        assessment_id,

        updates
    )

    if not updated:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Section could not "
                "be updated."
            )
        )

    return serialize_section(
        updated
    )


# ==========================================================
# DELETE SECTION
# ==========================================================

@router.delete(
    "/{assessment_id}/sections/{section_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_existing_section(

    assessment_id: str,

    section_id: str,

    current_teacher: dict = Depends(
        require_teacher
    )
):

    assessment = get_assessment_by_id(
        assessment_id
    )

    if not assessment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found."
        )

    if assessment["teacher_id"] != str(
        current_teacher["_id"]
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this assessment."
            )
        )

    if assessment["status"] != "DRAFT":

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Published assessment "
                "sections cannot be deleted."
            )
        )

    section = get_section_by_id(
        section_id
    )

    if not section:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found."
        )

    if section["assessment_id"] != assessment_id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Section does not belong "
                "to this assessment."
            )
        )

    deleted = delete_section(

        section_id,

        assessment_id
    )

    if not deleted:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Section could not "
                "be deleted."
            )
        )

    return None