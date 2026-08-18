import os
import shutil
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status
)

from app.dependencies.auth_dependencies import (
    require_teacher
)


router = APIRouter(
    prefix="/teacher",
    tags=["Teacher Uploads"]
)


# ==========================================================
# UPLOAD DIRECTORY
# ==========================================================

MODEL_ANSWER_DIRECTORY = os.path.join(
    "uploads",
    "model_answers"
)

os.makedirs(
    MODEL_ANSWER_DIRECTORY,
    exist_ok=True
)


# ==========================================================
# ALLOWED FILE TYPE
# ==========================================================

ALLOWED_CONTENT_TYPE = "application/pdf"


# ==========================================================
# UPLOAD MODEL ANSWER PDF
# ==========================================================

@router.post(
    "/upload/model-answer",
    status_code=status.HTTP_201_CREATED
)
def upload_model_answer_pdf(
    file: UploadFile = File(...),
    current_teacher: dict = Depends(
        require_teacher
    )
):

    # ------------------------------------------------------
    # CHECK FILE TYPE
    # ------------------------------------------------------

    if file.content_type != ALLOWED_CONTENT_TYPE:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Only PDF files are allowed."
        )

    # ------------------------------------------------------
    # CHECK FILE NAME
    # ------------------------------------------------------

    if not file.filename:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "A PDF file must be selected."
        )

    # ------------------------------------------------------
    # GENERATE SAFE UNIQUE FILE NAME
    # ------------------------------------------------------

    filename = (
        f"{uuid4().hex}.pdf"
    )

    file_path = os.path.join(
        MODEL_ANSWER_DIRECTORY,
        filename
    )

    # ------------------------------------------------------
    # SAVE FILE
    # ------------------------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception:

        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Could not save the PDF file."
        )

    # ------------------------------------------------------
    # RETURN FILE INFORMATION
    # ------------------------------------------------------

    return {

        "message":
            "Model answer PDF uploaded successfully.",

        "filename":
            filename,

        "url":
            f"/uploads/model_answers/{filename}"
    }