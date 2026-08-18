from pydantic import BaseModel, Field


# ==========================================================
# FACE VERIFICATION RESPONSE
# ==========================================================

class FaceVerificationResponse(
    BaseModel
):

    verified: bool

    similarity: float = Field(
        ge=-1.0,
        le=1.0
    )

    face_verified: bool

    message: str