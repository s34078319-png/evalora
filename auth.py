import os
import uuid
import shutil

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Form,
    UploadFile,
    File
)

from app.schemas.user_schema import (
    StudentRegister,
    TeacherRegister,
    UserLogin,
    Token
)

from app.crud.user_crud import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_login,
    create_user
)

from app.utils.security import (
    hash_password,
    verify_password
)

from app.utils.jwt import (
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ==========================================================
# PROFILE PHOTO DIRECTORY
# ==========================================================

PROFILE_PHOTO_DIRECTORY = os.path.join(
    "uploads",
    "profile_photos"
)


# ==========================================================
# CHECK DUPLICATE USER
# ==========================================================

def check_existing_user(
    username: str,
    email: str
):

    existing_username = get_user_by_username(
        username
    )

    if existing_username:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists."
        )

    existing_email = get_user_by_email(
        email
    )

    if existing_email:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists."
        )


# ==========================================================
# STUDENT REGISTRATION
#
# Content-Type:
# multipart/form-data
#
# Student profile photo is REQUIRED.
#
# Role is automatically assigned:
#
# student
# ==========================================================

@router.post(
    "/register/student",
    status_code=status.HTTP_201_CREATED
)
async def register_student(

    name: str = Form(...),

    username: str = Form(...),

    email: str = Form(...),

    password: str = Form(...),

    branch: str = Form(...),

    semester: int = Form(...),

    bio: str | None = Form(None),

    profile_photo: UploadFile = File(...)

):

    # ======================================================
    # VALIDATE FORM DATA
    # ======================================================

    try:

        data = StudentRegister(
            name=name,
            username=username,
            email=email,
            password=password,
            branch=branch,
            semester=semester,
            bio=bio
        )

    except ValueError as e:

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    # ======================================================
    # PROFILE PHOTO REQUIRED
    # ======================================================

    if not profile_photo.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile photo is required."
        )

    # ======================================================
    # VALIDATE PHOTO EXTENSION
    # ======================================================

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png"
    }

    original_filename = (
        profile_photo.filename.lower()
    )

    extension = os.path.splitext(
        original_filename
    )[1]

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Profile photo must be a JPG, JPEG, "
                "or PNG image."
            )
        )

    # ======================================================
    # CHECK DUPLICATES
    # ======================================================

    check_existing_user(
        data.username,
        str(data.email)
    )

    # ======================================================
    # CREATE DIRECTORY
    # ======================================================

    os.makedirs(
        PROFILE_PHOTO_DIRECTORY,
        exist_ok=True
    )

    # ======================================================
    # UNIQUE PHOTO NAME
    # ======================================================

    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    photo_path = os.path.join(
        PROFILE_PHOTO_DIRECTORY,
        unique_filename
    )

    # ======================================================
    # SAVE PHOTO
    # ======================================================

    try:

        with open(
            photo_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                profile_photo.file,
                buffer
            )

    except Exception as e:

        if os.path.exists(photo_path):

            os.remove(photo_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Unable to save profile photo: {str(e)}"
            )
        )

    finally:

        await profile_photo.close()

    # ======================================================
    # CREATE STUDENT DOCUMENT
    #
    # Role is assigned by backend.
    # ======================================================

    user = {

        "name":
            data.name,

        "username":
            data.username,

        "email":
            str(data.email),

        "hashed_password":
            hash_password(
                data.password
            ),

        "role":
            "student",

        "branch":
            data.branch,

        "semester":
            data.semester,

        "bio":
            data.bio,

        "profile_photo":
            unique_filename
    }

    # ======================================================
    # CREATE DATABASE USER
    # ======================================================

    try:

        created_user = create_user(
            user
        )

    except Exception as e:

        if os.path.exists(photo_path):

            os.remove(photo_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Unable to create student: {str(e)}"
            )
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    return {

        "message":
            "Student registered successfully.",

        "user_id":
            str(created_user["_id"]),

        "username":
            created_user["username"],

        "role":
            created_user["role"],

        "profile_photo":
            created_user["profile_photo"]
    }


# ==========================================================
# TEACHER REGISTRATION
#
# Content-Type:
# application/json
#
# Role automatically assigned:
#
# teacher
# ==========================================================

@router.post(
    "/register/teacher",
    status_code=status.HTTP_201_CREATED
)
def register_teacher(
    data: TeacherRegister
):

    # ======================================================
    # CHECK DUPLICATES
    # ======================================================

    check_existing_user(
        data.username,
        str(data.email)
    )

    # ======================================================
    # CREATE TEACHER DOCUMENT
    # ======================================================

    user = {

        "name":
            data.name,

        "username":
            data.username,

        "email":
            str(data.email),

        "hashed_password":
            hash_password(
                data.password
            ),

        "role":
            "teacher",

        "department":
            data.department,

        "bio":
            data.bio
    }

    # ======================================================
    # INSERT INTO MONGODB
    # ======================================================

    try:

        created_user = create_user(
            user
        )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Unable to create teacher: {str(e)}"
            )
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    return {

        "message":
            "Teacher registered successfully.",

        "user_id":
            str(created_user["_id"]),

        "username":
            created_user["username"],

        "role":
            created_user["role"]
    }


# ==========================================================
# LOGIN
#
# User can login using:
#
# username
# OR
# email
# ==========================================================

@router.post(
    "/login",
    response_model=Token
)
def login(
    data: UserLogin
):

    # ======================================================
    # FIND USER
    # ======================================================

    user = get_user_by_login(
        data.login
    )

    # ======================================================
    # INVALID USER
    # ======================================================

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    # ======================================================
    # VERIFY PASSWORD
    # ======================================================

    password_valid = verify_password(
        data.password,
        user["hashed_password"]
    )

    if not password_valid:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password."
        )

    # ======================================================
    # CREATE JWT
    # ======================================================

    access_token = create_access_token(
        user_id=str(user["_id"]),
        role=user["role"]
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return {

        "access_token":
            access_token,

        "token_type":
            "bearer"
    }