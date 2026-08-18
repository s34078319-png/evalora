from enum import Enum


# ==========================================================
# BRANCHES
# ==========================================================

class Branch(str, Enum):

    CSE = "Computer Science Engineering"

    MECH = "Mechanical Engineering"

    BIOMEDICAL = "Biomedical Engineering"

    EEE = "Electrical & Electronics Engineering"

    IT = "Information Technology"

    CIVIL = "Civil Engineering"


# ==========================================================
# SEMESTER LIMITS
# ==========================================================

MIN_SEMESTER = 1

MAX_SEMESTER = 8