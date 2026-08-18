from typing import Optional, Literal
import re

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator
)

from app.constants.academic import (
    Branch,
    MIN_SEMESTER,
    MAX_SEMESTER
)


# ==========================================================
# PASSWORD VALIDATION
#
# Requirements:
# - At least 8 characters
# - At least one uppercase letter
# - At least one lowercase letter
# - At least one digit
# - At least one special character
# ==========================================================

def validate_strong_password(
    value: str
) -> str:

    if not re.search(
        r"[A-Z]",
        value
    ):

        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(
        r"[a-z]",
        value
    ):

        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(
        r"\d",
        value
    ):

        raise ValueError(
            "Password must contain at least one digit."
        )

    if not re.search(
        r"[^A-Za-z0-9]",
        value
    ):

        raise ValueError(
            "Password must contain at least one special character."
        )

    return value


# ==========================================================
# GMAIL VALIDATION
#
# Evalora currently accepts Gmail addresses only.
#
# Email addresses are normalized to lowercase.
#
# Example:
#
# Shabina@gmail.com
# SHABINA@GMAIL.COM
# shabina@gmail.com
#
# All become:
#
# shabina@gmail.com
# ==========================================================

def validate_gmail(
    value: EmailStr
) -> EmailStr:

    email = str(
        value
    ).strip().lower()

    if not email.endswith(
        "@gmail.com"
    ):

        raise ValueError(
            "Only Gmail addresses ending with @gmail.com are allowed."
        )

    return email


# ==========================================================
# STUDENT REGISTRATION
#
# role is NOT accepted from the client.
#
# Backend automatically sets:
#
# role = "student"
#
# Student profile photo is handled separately
# through UploadFile in the authentication route.
#
# Branch comes from academic.py.
#
# Semester is limited using:
#
# MIN_SEMESTER
# MAX_SEMESTER
# ==========================================================

class StudentRegister(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    branch: Branch

    semester: int = Field(
        ge=MIN_SEMESTER,
        le=MAX_SEMESTER
    )

    bio: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(
        cls,
        value: EmailStr
    ) -> EmailStr:

        return validate_gmail(
            value
        )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str
    ) -> str:

        return validate_strong_password(
            value
        )


# ==========================================================
# TEACHER REGISTRATION
#
# role is NOT accepted from the client.
#
# Backend automatically sets:
#
# role = "teacher"
# ==========================================================

class TeacherRegister(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )

    department: str = Field(
        min_length=1,
        max_length=100
    )

    bio: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(
        cls,
        value: EmailStr
    ) -> EmailStr:

        return validate_gmail(
            value
        )

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value: str
    ) -> str:

        return validate_strong_password(
            value
        )


# ==========================================================
# LOGIN
# ==========================================================

class UserLogin(BaseModel):

    login: str = Field(
        min_length=1
    )

    password: str = Field(
        min_length=1
    )


# ==========================================================
# TOKEN RESPONSE
# ==========================================================

class Token(BaseModel):

    access_token: str

    token_type: str


# ==========================================================
# PUBLIC USER RESPONSE
# ==========================================================

class UserResponse(BaseModel):

    id: str

    name: str

    username: str

    email: EmailStr

    role: Literal[
        "student",
        "teacher"
    ]

    bio: Optional[str] = None