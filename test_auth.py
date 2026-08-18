from fastapi import (
    APIRouter,
    Depends
)

from app.dependencies.auth_dependencies import (
    get_current_user,
    require_student,
    require_teacher
)


router = APIRouter(
    prefix="/test-auth",
    tags=["Authorization Testing"]
)


# ==========================================================
# ANY AUTHENTICATED USER
# ==========================================================

@router.get(
    "/me"
)
def test_current_user(
    current_user: dict = Depends(
        get_current_user
    )
):

    return {
        "message": "Authentication successful.",
        "user_id": str(
            current_user["_id"]
        ),
        "username":
            current_user["username"],
        "email":
            current_user["email"],
        "role":
            current_user["role"]
    }


# ==========================================================
# STUDENT ONLY
# ==========================================================

@router.get(
    "/student"
)
def test_student_access(
    current_user: dict = Depends(
        require_student
    )
):

    return {
        "message":
            "Student authorization successful.",
        "username":
            current_user["username"],
        "role":
            current_user["role"]
    }


# ==========================================================
# TEACHER ONLY
# ==========================================================

@router.get(
    "/teacher"
)
def test_teacher_access(
    current_user: dict = Depends(
        require_teacher
    )
):

    return {
        "message":
            "Teacher authorization successful.",
        "username":
            current_user["username"],
        "role":
            current_user["role"]
    }