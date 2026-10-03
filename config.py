import os

# =========================================================
# APPLICATION CONFIGURATION
# INTELLIGENT CV SCREENING AND JOB MATCHING SYSTEM
# =========================================================

# ---------------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# ---------------------------------------------------------
# FLASK CONFIGURATION
# ---------------------------------------------------------

SECRET_KEY = "intelligent-cv-screening-secret-key-2026"

DEBUG = True


# ---------------------------------------------------------
# APPLICATION INFORMATION
# ---------------------------------------------------------

APP_NAME = "Intelligent CV Screening System"

APP_VERSION = "1.0.0"

ORGANIZATION_NAME = "AI Recruitment Intelligence"


# ---------------------------------------------------------
# FILE UPLOAD CONFIGURATION
# ---------------------------------------------------------

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

MAX_CONTENT_LENGTH = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}


# ---------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------

DB_HOST = "localhost"

DB_PORT = 3306

DB_NAME = "cv_screening_system"

DB_USER = "root"

DB_PASSWORD = ""


# ---------------------------------------------------------
# AI MATCHING WEIGHTS
# ---------------------------------------------------------

TECHNICAL_SKILLS_WEIGHT = 40

WORK_EXPERIENCE_WEIGHT = 25

EDUCATION_WEIGHT = 15

JOB_RELEVANCE_WEIGHT = 20


# ---------------------------------------------------------
# AI ENGINE SETTINGS
# ---------------------------------------------------------

AUTO_SKILL_EXTRACTION = True

AUTO_CANDIDATE_SCORING = True

AI_RECOMMENDATION = True


# ---------------------------------------------------------
# DIRECTORY SETUP
# ---------------------------------------------------------

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ---------------------------------------------------------
# CONFIGURATION TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("INTELLIGENT CV SCREENING SYSTEM")
    print("=" * 60)

    print(f"Application      : {APP_NAME}")
    print(f"Version          : {APP_VERSION}")
    print(f"Organization     : {ORGANIZATION_NAME}")

    print()
    print("Database Configuration")
    print("-" * 60)
    print(f"Host             : {DB_HOST}")
    print(f"Port             : {DB_PORT}")
    print(f"Database         : {DB_NAME}")
    print(f"User             : {DB_USER}")

    print()
    print("AI Matching Weights")
    print("-" * 60)
    print(f"Technical Skills : {TECHNICAL_SKILLS_WEIGHT}%")
    print(f"Experience       : {WORK_EXPERIENCE_WEIGHT}%")
    print(f"Education        : {EDUCATION_WEIGHT}%")
    print(f"Job Relevance    : {JOB_RELEVANCE_WEIGHT}%")

    print()
    print(f"Upload Folder    : {UPLOAD_FOLDER}")
    print("Maximum CV Size  : 10 MB")

    print("=" * 60)