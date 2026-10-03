"""
INTELLIGENT CV SCREENING SYSTEM
AI Screening Engine
Version: 2.9.0

Purpose:
- Extract CV text from PDF, scanned PDF and DOCX files
- Perform OCR when required
- Extract education and qualification information
- Estimate work experience
- Extract technical and professional skills
- Match related/equivalent skills
- Calculate education, experience, title and text scores
- Calculate final candidate compatibility score
- Optionally store screening information in MySQL
"""

import os
import re
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False


try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    Image = None
    TESSERACT_AVAILABLE = False


try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF_AVAILABLE = False


try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    Document = None
    DOCX_AVAILABLE = False


try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False


# ============================================================
# ENGINE INFORMATION
# ============================================================

ENGINE_VERSION = "2.9.0"


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

if TESSERACT_AVAILABLE:
    for _path in TESSERACT_PATHS:
        if os.path.exists(_path):
            pytesseract.pytesseract.tesseract_cmd = _path
            print(f"Tesseract OCR configured: {_path}")
            break


# ============================================================
# JOB PROFILES
# ============================================================

JOB_PROFILES = {

    "Junior Software Developer": {
        "skills": [
            "programming",
            "python",
            "java",
            "javascript",
            "html",
            "css",
            "database",
            "sql",
            "software development",
            "problem solving",
            "debugging",
            "git",
        ],
        "education": [
            "information technology",
            "information communication technology",
            "computer science",
            "software engineering",
            "computer studies",
        ],
        "experience": 1.0,
        "titles": [
            "software developer",
            "software engineer",
            "developer",
            "programmer",
            "web developer",
            "junior developer",
        ],
    },

    "Network Administrator": {
        "skills": [
            "networking",
            "network administration",
            "network configuration",
            "cisco",
            "lan",
            "wan",
            "tcp/ip",
            "routing",
            "switching",
            "network troubleshooting",
            "firewall",
            "network security",
        ],
        "education": [
            "information technology",
            "information communication technology",
            "computer science",
            "networking",
            "computer networks",
        ],
        "experience": 1.0,
        "titles": [
            "network administrator",
            "network technician",
            "network engineer",
            "network support",
        ],
    },

    "Cybersecurity Analyst": {
        "skills": [
            "cybersecurity",
            "network security",
            "information security",
            "security",
            "firewall",
            "threat detection",
            "incident response",
            "vulnerability assessment",
            "risk assessment",
            "penetration testing",
        ],
        "education": [
            "cyber security",
            "cybersecurity",
            "information security",
            "information technology",
            "computer science",
        ],
        "experience": 1.0,
        "titles": [
            "cybersecurity analyst",
            "security analyst",
            "cyber security analyst",
            "security technician",
        ],
    },

    "IT Support Specialist": {
        "skills": [
            "it support",
            "technical support",
            "user support",
            "customer support",
            "technical assistance",
            "troubleshooting",
            "hardware",
            "hardware maintenance",
            "software",
            "software installation",
            "installation",
            "configuration",
            "computer maintenance",
            "networking",
            "network configuration",
            "operating systems",
            "windows",
            "linux",
            "printer",
            "printers",
            "system support",
        ],
        "education": [
            "information technology",
            "information communication technology",
            "computer science",
            "computer studies",
            "ict",
        ],
        "experience": 1.0,
        "titles": [
            "it support specialist",
            "it support",
            "technical support",
            "support technician",
            "ict support",
            "it technician",
            "computer technician",
        ],
    },

    "Data Analyst": {
        "skills": [
            "data analysis",
            "data science",
            "excel",
            "sql",
            "database",
            "statistics",
            "python",
            "data visualization",
            "power bi",
            "tableau",
        ],
        "education": [
            "data science",
            "statistics",
            "information technology",
            "computer science",
            "data analytics",
        ],
        "experience": 1.0,
        "titles": [
            "data analyst",
            "data scientist",
            "data analyst intern",
            "business analyst",
        ],
    },

    "Systems Administrator": {
        "skills": [
            "system administration",
            "systems administration",
            "windows",
            "linux",
            "server",
            "networking",
            "hardware",
            "software",
            "troubleshooting",
            "configuration",
            "system support",
            "backup",
            "security",
        ],
        "education": [
            "information technology",
            "information communication technology",
            "computer science",
            "systems administration",
        ],
        "experience": 1.0,
        "titles": [
            "systems administrator",
            "system administrator",
            "system technician",
            "server administrator",
        ],
    },
}


# ============================================================
# POSITION ALIASES
# ============================================================

POSITION_ALIASES = {
    "software developer": "Junior Software Developer",
    "junior software developer": "Junior Software Developer",
    "developer": "Junior Software Developer",
    "programmer": "Junior Software Developer",
    "web developer": "Junior Software Developer",

    "network administrator": "Network Administrator",
    "network technician": "Network Administrator",
    "network engineer": "Network Administrator",
    "network support": "Network Administrator",

    "cyber security analyst": "Cybersecurity Analyst",
    "cybersecurity analyst": "Cybersecurity Analyst",
    "security analyst": "Cybersecurity Analyst",
    "security technician": "Cybersecurity Analyst",

    "it support": "IT Support Specialist",
    "it support specialist": "IT Support Specialist",
    "ict support": "IT Support Specialist",
    "technical support": "IT Support Specialist",
    "it technician": "IT Support Specialist",
    "computer technician": "IT Support Specialist",
    "support technician": "IT Support Specialist",

    "data analyst": "Data Analyst",
    "data scientist": "Data Analyst",
    "business analyst": "Data Analyst",

    "system administrator": "Systems Administrator",
    "systems administrator": "Systems Administrator",
    "server administrator": "Systems Administrator",
}


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "ict": "information communication technology",
    "cict": "information communication technology",
    "it": "information technology",

    "cyber security": "cybersecurity",
    "cyber-security": "cybersecurity",

    "network admin": "network administration",

    "tech support": "technical support",

    "computer repair": "hardware maintenance",
    "pc repair": "hardware maintenance",

    "ms windows": "windows",
    "microsoft windows": "windows",
    "win": "windows",

    "network support": "network troubleshooting",

    "system admin": "system administration",

    "systems admin": "system administration",

    "data analytics": "data analysis",

    "power bi": "power bi",
}


# ============================================================
# RELATED SKILL GROUPS
#
# These groups allow the screening engine to understand that
# different phrases can represent the same practical ability.
# ============================================================

RELATED_SKILLS = {

    "it support": {
        "it support",
        "technical support",
        "user support",
        "customer support",
        "technical assistance",
        "system support",
        "ict support",
        "support technician",
        "it technician",
        "computer technician",
    },

    "technical support": {
        "it support",
        "technical support",
        "user support",
        "technical assistance",
        "system support",
        "ict support",
    },

    "user support": {
        "it support",
        "technical support",
        "user support",
        "customer support",
        "technical assistance",
    },

    "customer support": {
        "it support",
        "technical support",
        "user support",
        "customer support",
        "technical assistance",
    },

    "technical assistance": {
        "it support",
        "technical support",
        "user support",
        "technical assistance",
    },

    "hardware": {
        "hardware",
        "hardware maintenance",
        "computer maintenance",
        "computer hardware",
        "computer repair",
    },

    "hardware maintenance": {
        "hardware",
        "hardware maintenance",
        "computer maintenance",
        "computer hardware",
    },

    "computer maintenance": {
        "hardware",
        "hardware maintenance",
        "computer maintenance",
        "computer repair",
    },

    "software": {
        "software",
        "software installation",
        "installation",
        "configuration",
    },

    "software installation": {
        "software installation",
        "installation",
        "software",
    },

    "installation": {
        "software installation",
        "installation",
        "configuration",
    },

    "configuration": {
        "configuration",
        "software installation",
        "network configuration",
        "system administration",
    },

    "networking": {
        "networking",
        "network administration",
        "network configuration",
        "network troubleshooting",
        "computer networks",
        "computer networking",
        "lan",
        "wan",
        "routing",
        "switching",
    },

    "network configuration": {
        "network configuration",
        "networking",
        "network administration",
        "network troubleshooting",
    },

    "network administration": {
        "network administration",
        "networking",
        "network configuration",
        "network troubleshooting",
    },

    "network troubleshooting": {
        "network troubleshooting",
        "networking",
        "network configuration",
        "technical support",
        "troubleshooting",
    },

    "troubleshooting": {
        "troubleshooting",
        "computer troubleshooting",
        "network troubleshooting",
        "technical support",
        "technical assistance",
    },

    "operating systems": {
        "operating systems",
        "windows",
        "linux",
        "system administration",
        "system support",
    },

    "windows": {
        "windows",
        "operating systems",
        "system administration",
        "system support",
    },

    "linux": {
        "linux",
        "operating systems",
        "system administration",
        "system support",
    },

    "system support": {
        "system support",
        "it support",
        "technical support",
        "operating systems",
        "troubleshooting",
    },

    "printers": {
        "printers",
        "printer",
        "hardware",
        "hardware maintenance",
        "technical support",
        "troubleshooting",
    },

    "printer": {
        "printer",
        "printers",
        "hardware",
        "hardware maintenance",
        "technical support",
        "troubleshooting",
    },

    "cybersecurity": {
        "cybersecurity",
        "cyber security",
        "information security",
        "network security",
        "security",
    },

    "network security": {
        "network security",
        "cybersecurity",
        "information security",
        "security",
        "firewall",
    },

    "information security": {
        "information security",
        "cybersecurity",
        "network security",
        "security",
    },

    "database": {
        "database",
        "sql",
        "data analysis",
    },

    "sql": {
        "sql",
        "database",
    },

    "data analysis": {
        "data analysis",
        "data analytics",
        "data science",
        "statistics",
        "sql",
        "excel",
    },

    "data science": {
        "data science",
        "data analysis",
        "data analytics",
        "statistics",
        "python",
    },

    "programming": {
        "programming",
        "python",
        "java",
        "javascript",
        "software development",
        "web development",
    },

    "software development": {
        "software development",
        "programming",
        "developer",
        "web development",
        "debugging",
    },
}


# ============================================================
# ADDITIONAL SKILL DETECTION PATTERNS
# ============================================================

ADDITIONAL_SKILL_PATTERNS = {

    "network troubleshooting":
        r"\bnetwork[\s-]+troubleshooting\b",

    "hardware maintenance":
        r"\bhardware[\s-]+maintenance\b",

    "computer maintenance":
        r"\bcomputer[\s-]+maintenance\b",

    "technical support":
        r"\btechnical[\s-]+support\b",

    "technical assistance":
        r"\btechnical[\s-]+assistance\b",

    "user support":
        r"\buser[\s-]+support\b",

    "customer support":
        r"\bcustomer[\s-]+support\b",

    "software installation":
        r"\bsoftware[\s-]+installation\b",

    "network configuration":
        r"\bnetwork[\s-]+configuration\b",

    "operating systems":
        r"\boperating[\s-]+systems?\b",

    "data science":
        r"\bdata[\s-]+science\b",

    "data analytics":
        r"\bdata[\s-]+analytics\b",

    "data analysis":
        r"\bdata[\s-]+analysis\b",

    "cybersecurity":
        r"\bcyber[\s-]+security\b|\bcybersecurity\b",

    "information security":
        r"\binformation[\s-]+security\b",

    "network administration":
        r"\bnetwork[\s-]+administration\b",

    "system administration":
        r"\bsystems?[\s-]+administration\b",

    "computer hardware":
        r"\bcomputer[\s-]+hardware\b",

    "computer troubleshooting":
        r"\bcomputer[\s-]+troubleshooting\b",

    "web development":
        r"\bweb[\s-]+development\b",

    "software development":
        r"\bsoftware[\s-]+development\b",

    "problem solving":
        r"\bproblem[\s-]+solving\b",

    "data visualization":
        r"\bdata[\s-]+visualization\b",

    "power bi":
        r"\bpower[\s-]+bi\b",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    """
    Normalize text for reliable matching and OCR processing.
    """

    if not text:
        return ""

    text = str(text).lower()

    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2012": "-",
        "\u2212": "-",
        "\u00a0": " ",
        "\t": " ",
        "\r": "\n",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[ ]+", " ", text)

    return text.strip()


# ============================================================
# WORD/PHRASE MATCHING
# ============================================================

def phrase_exists(text, phrase):
    """
    Safely determine whether a phrase exists in text.

    Word boundaries are used so that short terms such as IT do
    not accidentally match unrelated words.
    """

    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    if not normalized_text or not normalized_phrase:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(normalized_phrase)
        + r"(?![a-z0-9])"
    )

    return bool(
        re.search(
            pattern,
            normalized_text,
            re.IGNORECASE,
        )
    )


# ============================================================
# CANONICAL SKILL
# ============================================================

def canonical_skill(skill):

    skill = normalize_text(skill)

    if not skill:
        return ""

    return SKILL_ALIASES.get(
        skill,
        skill
    )


# ============================================================
# CANONICAL POSITION
# ============================================================

def canonical_position(position):

    position = normalize_text(position)

    if not position:
        return "IT Support Specialist"

    if position in POSITION_ALIASES:
        return POSITION_ALIASES[position]

    for alias, standard in POSITION_ALIASES.items():

        if phrase_exists(position, alias):
            return standard

    return position.title()


# ============================================================
# PDF SELECTABLE TEXT EXTRACTION
# ============================================================

def extract_pdf_selectable_text(file_path):

    text = ""

    if PYMUPDF_AVAILABLE:

        try:

            print(
                "Trying PyMuPDF PDF text extraction..."
            )

            document = fitz.open(file_path)

            pages = []

            for page in document:
                pages.append(
                    page.get_text()
                )

            document.close()

            text = "\n".join(pages).strip()

            if text:
                return text

        except Exception as error:

            print(
                "PyMuPDF extraction failed: "
                f"{error}"
            )

    if PYPDF_AVAILABLE:

        try:

            print(
                "Trying pypdf PDF text extraction..."
            )

            reader = PdfReader(file_path)

            pages = []

            for page in reader.pages:

                try:
                    pages.append(
                        page.extract_text() or ""
                    )

                except Exception:
                    pass

            text = "\n".join(pages).strip()

            if text:
                return text

        except Exception as error:

            print(
                "pypdf extraction failed: "
                f"{error}"
            )

    return ""


# ============================================================
# PDF OCR
# ============================================================

def extract_pdf_with_ocr(file_path):

    if (
        not PYMUPDF_AVAILABLE
        or not TESSERACT_AVAILABLE
    ):
        return ""

    try:

        print(
            "No selectable PDF text found. "
            "Attempting OCR on scanned PDF..."
        )

        document = fitz.open(file_path)

        total_pages = len(document)

        print(
            f"OCR started: {total_pages} page(s)."
        )

        pages = []

        for index, page in enumerate(document):

            print(
                f"OCR processing page "
                f"{index + 1}/{total_pages}..."
            )

            matrix = fitz.Matrix(2.5, 2.5)

            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )

            page_text = pytesseract.image_to_string(
                image,
                config="--psm 6",
            )

            pages.append(page_text)

        document.close()

        text = "\n".join(pages).strip()

        print(
            "OCR completed successfully. "
            f"Extracted {len(text)} characters."
        )

        return text

    except Exception as error:

        print(
            f"OCR extraction failed: {error}"
        )

        return ""


# ============================================================
# DOCX EXTRACTION
# ============================================================

def extract_docx_text(file_path):

    if not DOCX_AVAILABLE:
        return ""

    try:

        document = Document(file_path)

        parts = []

        for paragraph in document.paragraphs:

            if paragraph.text.strip():

                parts.append(
                    paragraph.text
                )

        for table in document.tables:

            for row in table.rows:

                row_text = []

                for cell in row.cells:
                    row_text.append(cell.text)

                parts.append(
                    " ".join(row_text)
                )

        return "\n".join(parts).strip()

    except Exception as error:

        print(
            f"DOCX extraction failed: {error}"
        )

        return ""


# ============================================================
# COMPLETE CV TEXT EXTRACTION
# ============================================================

def extract_cv_text(file_path):

    if not file_path:
        return ""

    if not os.path.exists(file_path):

        print(
            f"CV file not found: {file_path}"
        )

        return ""

    extension = os.path.splitext(
        file_path
    )[1].lower()

    text = ""

    if extension == ".pdf":

        text = extract_pdf_selectable_text(
            file_path
        )

        if not text:

            text = extract_pdf_with_ocr(
                file_path
            )

    elif extension == ".docx":

        text = extract_docx_text(
            file_path
        )

    else:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:

                text = file.read()

        except Exception as error:

            print(
                f"Text extraction failed: {error}"
            )

    text = text.strip()

    if text:

        print(
            "CV text extracted successfully."
        )

    return text


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text):

    normalized = normalize_text(text)

    extracted = set()

    if not normalized:
        return []

    all_skills = set()

    for profile in JOB_PROFILES.values():

        for skill in profile.get("skills", []):

            canonical = canonical_skill(skill)

            if canonical:
                all_skills.add(canonical)

    # --------------------------------------------------------
    # Standard profile skills
    # --------------------------------------------------------

    for skill in all_skills:

        if phrase_exists(
            normalized,
            skill
        ):

            extracted.add(skill)

    # --------------------------------------------------------
    # Additional robust patterns
    # --------------------------------------------------------

    for skill, pattern in ADDITIONAL_SKILL_PATTERNS.items():

        if re.search(
            pattern,
            normalized,
            re.IGNORECASE,
        ):

            extracted.add(
                canonical_skill(skill)
            )

    # --------------------------------------------------------
    # Common short technical terms
    # --------------------------------------------------------

    short_skill_patterns = {

        "python": r"\bpython\b",

        "java": r"\bjava\b",

        "javascript": r"\bjavascript\b",

        "html": r"\bhtml\b",

        "css": r"\bcss\b",

        "sql": r"\bsql\b",

        "excel": r"\bexcel\b",

        "git": r"\bgit\b",

        "cisco": r"\bcisco\b",

        "lan": r"\blan\b",

        "wan": r"\bwan\b",

        "routing": r"\brouting\b",

        "switching": r"\bswitching\b",

        "firewall": r"\bfirewall\b",

        "linux": r"\blinux\b",

        "windows": r"\bwindows\b",

        "server": r"\bservers?\b",

        "security": r"\bsecurity\b",

        "statistics": r"\bstatistics\b",

        "tableau": r"\btableau\b",

        "power bi": r"\bpower[\s-]+bi\b",
    }

    for skill, pattern in short_skill_patterns.items():

        if re.search(
            pattern,
            normalized,
            re.IGNORECASE,
        ):

            extracted.add(skill)

    return sorted(extracted)


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def extract_education(text):

    normalized = normalize_text(text)

    found = set()

    if not normalized:
        return []

    # --------------------------------------------------------
    # OCR normalization
    # --------------------------------------------------------

    normalized_ocr = normalized

    normalized_ocr = re.sub(
        r"\bc1ct\b",
        "cict",
        normalized_ocr,
        flags=re.IGNORECASE,
    )

    normalized_ocr = re.sub(
        r"\bc[\s\.\-_/]*i[\s\.\-_/]*c[\s\.\-_/]*t\b",
        "cict",
        normalized_ocr,
        flags=re.IGNORECASE,
    )

    normalized_ocr = re.sub(
        r"\binformation\s+and\s+communication\s+technology\b",
        "information communication technology",
        normalized_ocr,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # Education terms
    # --------------------------------------------------------

    education_terms = [

        "information technology",

        "information communication technology",

        "computer science",

        "computer studies",

        "software engineering",

        "cyber security",

        "cybersecurity",

        "information security",

        "computer networking",

        "computer networks",

        "data science",

        "data analytics",

        "data analysis",

        "statistics",

        "networking",

        "ict",

        "cict",

        "diploma",

        "certificate",

        "degree",

        "bachelor",

        "higher diploma",

        "associate degree",
    ]

    for term in education_terms:

        if phrase_exists(
            normalized_ocr,
            term
        ):

            found.add(term)

    # --------------------------------------------------------
    # Qualification terms
    # --------------------------------------------------------

    qualification_pattern = (
        r"(?:"
        r"diploma|"
        r"certificate|"
        r"degree|"
        r"higher\s+diploma|"
        r"bachelor(?:s)?|"
        r"master(?:s)?"
        r")"
    )

    subject_pattern = (
        r"(?:"
        r"ict|"
        r"cict|"
        r"information\s+technology|"
        r"information\s+communication\s+technology|"
        r"information\s+and\s+communication\s+technology|"
        r"computer\s+science|"
        r"computer\s+studies|"
        r"networking|"
        r"cyber[\s-]+security|"
        r"cybersecurity|"
        r"data\s+science|"
        r"data\s+analytics|"
        r"statistics"
        r")"
    )

    qualification_subject_patterns = [

        rf"\b{qualification_pattern}\b"
        rf".{{0,150}}"
        rf"\b{subject_pattern}\b",

        rf"\b{subject_pattern}\b"
        rf".{{0,150}}"
        rf"\b{qualification_pattern}\b",
    ]

    for pattern in qualification_subject_patterns:

        if re.search(
            pattern,
            normalized_ocr,
            re.IGNORECASE,
        ):

            match_text = re.search(
                pattern,
                normalized_ocr,
                re.IGNORECASE,
            )

            if not match_text:
                continue

            matched_text = match_text.group(0)

            # ICT/IT
            if re.search(
                r"\bict\b|\bcict\b|"
                r"\binformation\s+technology\b|"
                r"\binformation\s+communication\s+technology\b|"
                r"\bcomputer\s+science\b|"
                r"\bcomputer\s+studies\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("ict")
                found.add(
                    "information technology"
                )
                found.add(
                    "information communication technology"
                )

            # Networking
            if re.search(
                r"\bnetworking\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("networking")

            # Cybersecurity
            if re.search(
                r"\bcyber[\s-]+security\b|"
                r"\bcybersecurity\b|"
                r"\binformation\s+security\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("cybersecurity")

            # Data
            if re.search(
                r"\bdata\s+science\b|"
                r"\bdata\s+analytics\b|"
                r"\bstatistics\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("data science")

    # --------------------------------------------------------
    # Explicit Diploma in ICT / IT
    # --------------------------------------------------------

    diploma_patterns = [

        r"\bdiploma\s+in\s+ict\b",

        r"\bdiploma\s+in\s+cict\b",

        r"\bdiploma\s+in\s+it\b",

        r"\bdiploma\s+in\s+information\s+technology\b",

        r"\bdiploma\s+in\s+information\s+communication\s+technology\b",

        r"\bdiploma\s+in\s+information\s+and\s+communication\s+technology\b",

        r"\bdiploma\s+in\s+computer\s+science\b",

        r"\bdiploma\s+in\s+computer\s+studies\b",

        r"\bdiploma\s+in\s+networking\b",
    ]

    for pattern in diploma_patterns:

        if re.search(
            pattern,
            normalized_ocr,
            re.IGNORECASE,
        ):

            found.add("diploma")

            if re.search(
                r"\bict\b|\bcict\b|"
                r"\binformation\s+technology\b|"
                r"\binformation\s+communication\s+technology\b|"
                r"\bcomputer\s+science\b|"
                r"\bcomputer\s+studies\b",
                re.search(
                    pattern,
                    normalized_ocr,
                    re.IGNORECASE,
                ).group(0),
                re.IGNORECASE,
            ):

                found.add("ict")
                found.add(
                    "information technology"
                )
                found.add(
                    "information communication technology"
                )

            if re.search(
                r"\bnetworking\b",
                re.search(
                    pattern,
                    normalized_ocr,
                    re.IGNORECASE,
                ).group(0),
                re.IGNORECASE,
            ):

                found.add("networking")

    # --------------------------------------------------------
    # Explicit Certificate in ICT / IT
    # --------------------------------------------------------

    certificate_patterns = [

        r"\bcertificate\s+in\s+ict\b",

        r"\bcertificate\s+in\s+cict\b",

        r"\bcertificate\s+in\s+it\b",

        r"\bcertificate\s+in\s+information\s+technology\b",

        r"\bcertificate\s+in\s+information\s+communication\s+technology\b",

        r"\bcertificate\s+in\s+information\s+and\s+communication\s+technology\b",

        r"\bcertificate\s+in\s+computer\s+science\b",

        r"\bcertificate\s+in\s+computer\s+studies\b",

        r"\bcertificate\s+in\s+networking\b",
    ]

    for pattern in certificate_patterns:

        if re.search(
            pattern,
            normalized_ocr,
            re.IGNORECASE,
        ):

            found.add("certificate")

            match = re.search(
                pattern,
                normalized_ocr,
                re.IGNORECASE,
            )

            matched_text = match.group(0)

            if re.search(
                r"\bict\b|\bcict\b|"
                r"\binformation\s+technology\b|"
                r"\binformation\s+communication\s+technology\b|"
                r"\bcomputer\s+science\b|"
                r"\bcomputer\s+studies\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("ict")
                found.add(
                    "information technology"
                )
                found.add(
                    "information communication technology"
                )

            if re.search(
                r"\bnetworking\b",
                matched_text,
                re.IGNORECASE,
            ):

                found.add("networking")

    # --------------------------------------------------------
    # Current studies / pursuing education
    # --------------------------------------------------------

    study_pattern = (
        r"\b(?:pursuing|studying|currently\s+pursuing|"
        r"student\s+of)\b"
        r".{0,200}"
        r"\b(?:diploma|certificate|degree|"
        r"higher\s+diploma)\b"
        r".{0,200}"
        r"\b(?:ict|cict|information\s+technology|"
        r"information\s+communication\s+technology|"
        r"information\s+and\s+communication\s+technology|"
        r"computer\s+science|computer\s+studies)\b"
    )

    if re.search(
        study_pattern,
        normalized_ocr,
        re.IGNORECASE,
    ):

        found.add("diploma")
        found.add("ict")
        found.add("information technology")
        found.add(
            "information communication technology"
        )

    # --------------------------------------------------------
    # Cybersecurity education
    # --------------------------------------------------------

    cybersecurity_pattern = (
        r"\bcyber[\s-]+security\b|"
        r"\bcybersecurity\b|"
        r"\binformation\s+security\b"
    )

    if re.search(
        cybersecurity_pattern,
        normalized_ocr,
        re.IGNORECASE,
    ):

        found.add("cybersecurity")

    # --------------------------------------------------------
    # Data education
    # --------------------------------------------------------

    if re.search(
        r"\bdata\s+science\b|"
        r"\bdata\s+analytics\b|"
        r"\bstatistics\b",
        normalized_ocr,
        re.IGNORECASE,
    ):

        found.add("data science")

    return sorted(found)


# ============================================================
# EDUCATION LEVEL DETECTION
# ============================================================

def detect_education_level(text):

    normalized = normalize_text(text)

    levels = []

    if re.search(
        r"\bphd\b|\bdoctorate\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("doctorate")

    if re.search(
        r"\bmasters?\b|\bmsc\b|\bma\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("masters")

    if re.search(
        r"\bbachelors?\b|\bbsc\b|\bba\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("bachelor")

    if re.search(
        r"\bhigher\s+diploma\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("higher diploma")

    if re.search(
        r"\bdiploma\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("diploma")

    if re.search(
        r"\bcertificate\b",
        normalized,
        re.IGNORECASE,
    ):

        levels.append("certificate")

    return levels


# ============================================================
# EXPERIENCE DATE PARSING
# ============================================================

MONTHS = {

    "january": 1,
    "jan": 1,

    "february": 2,
    "feb": 2,

    "march": 3,
    "mar": 3,

    "april": 4,
    "apr": 4,

    "may": 5,

    "june": 6,
    "jun": 6,

    "july": 7,
    "jul": 7,

    "august": 8,
    "aug": 8,

    "september": 9,
    "sep": 9,
    "sept": 9,

    "october": 10,
    "oct": 10,

    "november": 11,
    "nov": 11,

    "december": 12,
    "dec": 12,
}


def month_number(name):

    return MONTHS.get(
        normalize_text(name)
    )


def month_index(year, month):

    return year * 12 + month


MONTH_PATTERN = (
    r"(january|jan|february|feb|march|mar|"
    r"april|apr|may|june|jun|july|jul|"
    r"august|aug|september|sep|sept|"
    r"october|oct|november|nov|"
    r"december|dec)"
)


# ============================================================
# MONTH/YEAR DATE RANGE PARSER
# ============================================================

def parse_month_year_ranges(text):

    if not text:
        return []

    ranges = []

    normalized = normalize_text(text)

    pattern_month_first = re.compile(
        rf"\b{MONTH_PATTERN}\s+(20\d{{2}})"
        rf"\s+(?:to|until|-)\s+"
        rf"{MONTH_PATTERN}\s+(20\d{{2}})\b",
        re.IGNORECASE,
    )

    for match in pattern_month_first.finditer(
        normalized
    ):

        start_month = month_number(
            match.group(1)
        )

        start_year = int(
            match.group(2)
        )

        end_month = month_number(
            match.group(3)
        )

        end_year = int(
            match.group(4)
        )

        if not start_month or not end_month:
            continue

        start = month_index(
            start_year,
            start_month
        )

        end = month_index(
            end_year,
            end_month
        )

        if (
            end >= start
            and end - start <= 480
        ):

            ranges.append(
                (start, end)
            )

    pattern_year_first = re.compile(
        rf"\b(20\d{{2}})\s+{MONTH_PATTERN}"
        rf"\s+(?:to|until|-)\s+"
        rf"(20\d{{2}})\s+{MONTH_PATTERN}\b",
        re.IGNORECASE,
    )

    for match in pattern_year_first.finditer(
        normalized
    ):

        start_year = int(
            match.group(1)
        )

        start_month = month_number(
            match.group(2)
        )

        end_year = int(
            match.group(3)
        )

        end_month = month_number(
            match.group(4)
        )

        if not start_month or not end_month:
            continue

        start = month_index(
            start_year,
            start_month
        )

        end = month_index(
            end_year,
            end_month
        )

        if (
            end >= start
            and end - start <= 480
        ):

            ranges.append(
                (start, end)
            )

    return ranges


# ============================================================
# PRESENT DATE PARSER
# ============================================================

def parse_single_month_present_ranges(text):

    if not text:
        return []

    ranges = []

    normalized = normalize_text(text)

    now = datetime.now()

    pattern_month_first = re.compile(
        rf"\b{MONTH_PATTERN}\s+(20\d{{2}})"
        rf"\s+(?:to|until|-)\s+"
        rf"(present|current|now)\b",
        re.IGNORECASE,
    )

    for match in pattern_month_first.finditer(
        normalized
    ):

        start_month = month_number(
            match.group(1)
        )

        start_year = int(
            match.group(2)
        )

        if not start_month:
            continue

        start = month_index(
            start_year,
            start_month
        )

        end = month_index(
            now.year,
            now.month
        )

        if (
            end >= start
            and end - start <= 480
        ):

            ranges.append(
                (start, end)
            )

    pattern_year_first = re.compile(
        rf"\b(20\d{{2}})\s+{MONTH_PATTERN}"
        rf"\s+(?:to|until|-)\s+"
        rf"(present|current|now)\b",
        re.IGNORECASE,
    )

    for match in pattern_year_first.finditer(
        normalized
    ):

        start_year = int(
            match.group(1)
        )

        start_month = month_number(
            match.group(2)
        )

        if not start_month:
            continue

        start = month_index(
            start_year,
            start_month
        )

        end = month_index(
            now.year,
            now.month
        )

        if (
            end >= start
            and end - start <= 480
        ):

            ranges.append(
                (start, end)
            )

    return ranges


# ============================================================
# YEAR RANGE PARSER
# ============================================================

def parse_year_range(text):

    if not text:
        return []

    ranges = []

    normalized = normalize_text(text)

    pattern = re.compile(
        r"\b(20\d{2})\s+"
        r"(?:-|to|until)\s+"
        r"(20\d{2}|present|current)\b",
        re.IGNORECASE,
    )

    for match in pattern.finditer(
        normalized
    ):

        start_year = int(
            match.group(1)
        )

        end_value = normalize_text(
            match.group(2)
        )

        if end_value in (
            "present",
            "current",
        ):

            end_year = datetime.now().year

        else:

            end_year = int(
                end_value
            )

        if (
            end_year >= start_year
            and end_year - start_year <= 10
        ):

            ranges.append(
                (
                    month_index(
                        start_year,
                        1
                    ),
                    month_index(
                        end_year,
                        12
                    ),
                )
            )

    return ranges


# ============================================================
# WORK EXPERIENCE SECTION
# ============================================================

def isolate_work_experience_section(text):

    if not text:
        return ""

    lines = text.splitlines()

    start_index = None

    experience_headings = [
        "work experience",
        "working experience",
        "employment history",
        "professional experience",
        "experience",
        "internship",
        "industrial attachment",
        "work history",
        "employment",
    ]

    end_headings = [
        "education",
        "academic qualifications",
        "academic qualification",
        "educational background",
        "skills",
        "technical skills",
        "certifications",
        "certificates",
        "references",
        "referees",
        "languages",
        "personal details",
        "personal information",
        "career objective",
        "profile",
        "professional profile",
        "hobbies",
        "interests",
    ]

    for index, line in enumerate(lines):

        clean_line = normalize_text(line)

        clean_line = re.sub(
            r"[^a-z0-9 ]",
            " ",
            clean_line
        )

        clean_line = re.sub(
            r"\s+",
            " ",
            clean_line
        ).strip()

        if not clean_line:
            continue

        for heading in experience_headings:

            if (
                clean_line == heading
                or clean_line.startswith(
                    heading + " "
                )
            ):

                start_index = index + 1
                break

        if start_index is not None:
            break

    if start_index is None:
        return ""

    end_index = len(lines)

    for index in range(
        start_index,
        len(lines)
    ):

        clean_line = normalize_text(
            lines[index]
        )

        clean_line = re.sub(
            r"[^a-z0-9 ]",
            " ",
            clean_line
        )

        clean_line = re.sub(
            r"\s+",
            " ",
            clean_line
        ).strip()

        if not clean_line:
            continue

        for heading in end_headings:

            if (
                clean_line == heading
                or clean_line.startswith(
                    heading + " "
                )
            ):

                end_index = index
                break

        if end_index != len(lines):
            break

    section = "\n".join(
        lines[start_index:end_index]
    ).strip()

    if len(section) < 20:
        return ""

    return section


# ============================================================
# MERGE EXPERIENCE PERIODS
# ============================================================

def merge_experience_periods(periods):

    if not periods:
        return []

    cleaned = []

    for start, end in periods:

        if end >= start:
            cleaned.append(
                (start, end)
            )

    if not cleaned:
        return []

    cleaned.sort(
        key=lambda item: item[0]
    )

    merged = [cleaned[0]]

    for start, end in cleaned[1:]:

        old_start, old_end = merged[-1]

        if start <= old_end + 1:

            merged[-1] = (
                old_start,
                max(old_end, end),
            )

        else:

            merged.append(
                (start, end)
            )

    return merged


# ============================================================
# EXPERIENCE ESTIMATION
# ============================================================

def estimate_experience_years(text):

    if not text:
        return 0.0

    work_text = isolate_work_experience_section(
        text
    )

    if not work_text:
        return 0.0

    periods = []

    periods.extend(
        parse_month_year_ranges(
            work_text
        )
    )

    periods.extend(
        parse_single_month_present_ranges(
            work_text
        )
    )

    if not periods:

        periods.extend(
            parse_year_range(
                work_text
            )
        )

    if not periods:
        return 0.0

    merged = merge_experience_periods(
        periods
    )

    if not merged:
        return 0.0

    total_months = 0

    for start, end in merged:

        total_months += (
            end - start + 1
        )

    experience_years = (
        Decimal(total_months)
        / Decimal("12")
    ).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )

    return float(
        min(
            experience_years,
            Decimal("40.0")
        )
    )


# ============================================================
# TITLE MATCHING
# ============================================================

def calculate_title_score(
    text,
    position,
):

    normalized = normalize_text(text)

    canonical = canonical_position(
        position
    )

    profile = JOB_PROFILES.get(
        canonical
    )

    if not profile:
        return 50.0

    titles = profile.get(
        "titles",
        []
    )

    for title in titles:

        if phrase_exists(
            normalized,
            title
        ):

            return 100.0

    role_words = {

        "IT Support Specialist": [
            "ict support",
            "it support",
            "technical support",
            "support technician",
            "it technician",
            "computer technician",
        ],

        "Network Administrator": [
            "network technician",
            "network engineer",
            "network support",
        ],

        "Cybersecurity Analyst": [
            "security technician",
            "security analyst",
            "cyber security",
            "cybersecurity",
        ],

        "Junior Software Developer": [
            "developer",
            "programmer",
            "software",
        ],

        "Data Analyst": [
            "data science",
            "data analyst",
        ],

        "Systems Administrator": [
            "system administrator",
            "systems administrator",
            "server administrator",
        ],
    }

    for phrase in role_words.get(
        canonical,
        []
    ):

        if phrase_exists(
            normalized,
            phrase
        ):

            return 75.0

    return 0.0


# ============================================================
# EDUCATION SCORE
# ============================================================

def calculate_education_score(
    text,
    position,
):

    canonical = canonical_position(
        position
    )

    profile = JOB_PROFILES.get(
        canonical
    )

    if not profile:
        return 0.0

    normalized = normalize_text(text)

    education = extract_education(text)

    education_set = set(
        normalize_text(item)
        for item in education
        if item
    )

    has_certificate = bool(
        re.search(
            r"\bcertificate\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_diploma = bool(
        re.search(
            r"\bdiploma\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_higher_diploma = bool(
        re.search(
            r"\bhigher\s+diploma\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_degree = bool(
        re.search(
            r"\bdegree\b|\bbachelors?\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_masters = bool(
        re.search(
            r"\bmasters?\b|\bmsc\b|\bma\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_ict = bool(
        re.search(
            r"\bict\b|"
            r"\bcict\b|"
            r"\bc1ct\b|"
            r"\binformation\s+technology\b|"
            r"\binformation\s+communication\s+technology\b|"
            r"\binformation\s+and\s+communication\s+technology\b|"
            r"\bcomputer\s+science\b|"
            r"\bcomputer\s+studies\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_cybersecurity = bool(
        re.search(
            r"\bcyber[\s-]+security\b|"
            r"\bcybersecurity\b|"
            r"\binformation\s+security\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_data = bool(
        re.search(
            r"\bdata\s+science\b|"
            r"\bdata\s+analytics\b|"
            r"\bdata\s+analysis\b|"
            r"\bstatistics\b",
            normalized,
            re.IGNORECASE,
        )
    )

    has_networking = bool(
        re.search(
            r"\bnetworking\b|"
            r"\bcomputer\s+networking\b|"
            r"\bcomputer\s+networks\b",
            normalized,
            re.IGNORECASE,
        )
    )

    required = [
        normalize_text(item)
        for item in profile.get(
            "education",
            []
        )
        if item
    ]

    matched = 0

    for required_item in required:

        if required_item in education_set:
            matched += 1
            continue

        for candidate_item in education_set:

            if (
                required_item in candidate_item
                or candidate_item in required_item
            ):

                matched += 1
                break

    if required:

        direct_score = (
            matched / len(required)
        ) * 100

    else:

        direct_score = 0.0

    score = direct_score

    # --------------------------------------------------------
    # ICT RELATED POSITIONS
    # --------------------------------------------------------

    ict_related_positions = {
        "IT Support Specialist",
        "Network Administrator",
        "Systems Administrator",
        "Junior Software Developer",
    }

    if canonical in ict_related_positions:

        if (
            (
                has_diploma
                or has_higher_diploma
                or has_certificate
                or has_degree
                or has_masters
            )
            and has_ict
        ):

            score = max(
                score,
                100.0
            )

        elif has_ict:

            score = max(
                score,
                90.0
            )

        elif (
            has_diploma
            and has_networking
        ):

            score = max(
                score,
                85.0
            )

        elif (
            has_certificate
            and has_networking
        ):

            score = max(
                score,
                75.0
            )

        elif has_higher_diploma:

            score = max(
                score,
                80.0
            )

        elif has_diploma:

            score = max(
                score,
                65.0
            )

        elif has_certificate:

            score = max(
                score,
                55.0
            )

        if re.search(
            r"\bcomputer\s+science\b",
            normalized,
            re.IGNORECASE,
        ):

            score = max(
                score,
                90.0
            )

    # --------------------------------------------------------
    # CYBERSECURITY
    # --------------------------------------------------------

    if canonical == "Cybersecurity Analyst":

        if (
            (
                has_diploma
                or has_higher_diploma
                or has_certificate
                or has_degree
                or has_masters
            )
            and has_cybersecurity
        ):

            score = max(
                score,
                100.0
            )

        elif has_cybersecurity:

            score = max(
                score,
                90.0
            )

        elif has_ict:

            score = max(
                score,
                80.0
            )

        elif has_diploma:

            score = max(
                score,
                65.0
            )

        elif has_certificate:

            score = max(
                score,
                55.0
            )

    # --------------------------------------------------------
    # DATA ANALYST
    # --------------------------------------------------------

    if canonical == "Data Analyst":

        if (
            (
                has_diploma
                or has_higher_diploma
                or has_certificate
                or has_degree
                or has_masters
            )
            and has_data
        ):

            score = max(
                score,
                100.0
            )

        elif has_data:

            score = max(
                score,
                90.0
            )

        elif has_ict:

            score = max(
                score,
                80.0
            )

        elif has_diploma:

            score = max(
                score,
                65.0
            )

        elif has_certificate:

            score = max(
                score,
                55.0
            )

    return round(
        max(
            0.0,
            min(
                score,
                100.0
            )
        ),
        1
    )


# ============================================================
# EXPERIENCE SCORE
# ============================================================

def calculate_experience_score(
    text,
    position,
):

    years = estimate_experience_years(
        text
    )

    canonical = canonical_position(
        position
    )

    profile = JOB_PROFILES.get(
        canonical
    )

    required = 1.0

    if profile:

        required = float(
            profile.get(
                "experience",
                1.0
            )
        )

    if required <= 0:
        return 100.0

    score = (
        years / required
    ) * 100

    return round(
        min(
            max(
                score,
                0.0
            ),
            100.0
        ),
        1
    )


# ============================================================
# SKILL RELATIONSHIP MATCHING
# ============================================================

def skills_are_related(
    required_skill,
    candidate_skill,
):

    required_skill = canonical_skill(
        required_skill
    )

    candidate_skill = canonical_skill(
        candidate_skill
    )

    if not required_skill or not candidate_skill:
        return False

    if required_skill == candidate_skill:
        return True

    # Direct substring relationship for longer phrases
    if (
        required_skill in candidate_skill
        or candidate_skill in required_skill
    ):

        return True

    required_group = RELATED_SKILLS.get(
        required_skill,
        set()
    )

    candidate_group = RELATED_SKILLS.get(
        candidate_skill,
        set()
    )

    if candidate_skill in required_group:
        return True

    if required_skill in candidate_group:
        return True

    if (
        required_group
        and candidate_group
        and required_group.intersection(
            candidate_group
        )
    ):

        return True

    return False


# ============================================================
# SKILL SCORE
# ============================================================

def calculate_skill_score(
    text,
    position,
):

    canonical = canonical_position(
        position
    )

    profile = JOB_PROFILES.get(
        canonical
    )

    if not profile:

        extracted = extract_skills(text)

        return (
            0.0,
            [],
            [],
            extracted,
        )

    required_skills = [

        canonical_skill(skill)

        for skill in profile.get(
            "skills",
            []
        )

        if canonical_skill(skill)
    ]

    extracted = extract_skills(text)

    extracted_set = set(
        canonical_skill(skill)
        for skill in extracted
        if canonical_skill(skill)
    )

    matched = []
    missing = []

    # --------------------------------------------------------
    # Match every required skill against extracted skills
    # --------------------------------------------------------

    for required_skill in required_skills:

        matched_this_skill = False

        for candidate_skill in extracted_set:

            if skills_are_related(
                required_skill,
                candidate_skill
            ):

                matched_this_skill = True
                break

        if matched_this_skill:

            matched.append(
                required_skill
            )

        else:

            missing.append(
                required_skill
            )

    matched = sorted(
        set(matched)
    )

    missing = sorted(
        set(missing)
    )

    if not required_skills:

        score = 0.0

    else:

        score = (
            len(matched)
            / len(required_skills)
        ) * 100

    return (
        round(
            min(
                score,
                100.0
            ),
            1
        ),
        matched,
        missing,
        sorted(extracted_set),
    )


# ============================================================
# TEXT SIMILARITY
# ============================================================

def calculate_text_similarity(
    text,
    position,
):

    if (
        not text
        or not SKLEARN_AVAILABLE
    ):

        return 0.0

    canonical = canonical_position(
        position
    )

    profile = JOB_PROFILES.get(
        canonical
    )

    if not profile:
        return 0.0

    job_text = " ".join(
        profile.get("skills", [])
        + profile.get("education", [])
        + profile.get("titles", [])
    )

    try:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(
            [
                normalize_text(text),
                normalize_text(job_text),
            ]
        )

        similarity = cosine_similarity(
            matrix[0:1],
            matrix[1:2],
        )[0][0]

        return round(
            float(similarity * 100),
            1
        )

    except Exception as error:

        print(
            "TF-IDF similarity failed: "
            f"{error}"
        )

        return 0.0


# ============================================================
# FINAL MATCH SCORE
# ============================================================

def calculate_match_score(
    text,
    position,
):

    canonical = canonical_position(
        position
    )

    (
        skill_score,
        matched,
        missing,
        all_skills,
    ) = calculate_skill_score(
        text,
        canonical
    )

    education_score = calculate_education_score(
        text,
        canonical
    )

    experience_years = estimate_experience_years(
        text
    )

    experience_score = calculate_experience_score(
        text,
        canonical
    )

    title_score = calculate_title_score(
        text,
        canonical
    )

    text_similarity = calculate_text_similarity(
        text,
        canonical
    )

    # --------------------------------------------------------
    # OFFICIAL PROJECT WEIGHTING
    # --------------------------------------------------------

    weights = {
        "skills": 55,
        "education": 20,
        "experience": 15,
        "title": 5,
        "text_similarity": 5,
    }

    match_score = (
        skill_score * 0.55
        + education_score * 0.20
        + experience_score * 0.15
        + title_score * 0.05
        + text_similarity * 0.05
    )

    match_score = round(
        min(
            max(
                match_score,
                0.0
            ),
            100.0
        ),
        2
    )

    if match_score >= 80:

        band = "High compatibility"

    elif match_score >= 60:

        band = "Good compatibility"

    elif match_score >= 40:

        band = "Moderate compatibility"

    else:

        band = "Low compatibility"

    return {

        "engine_version":
            ENGINE_VERSION,

        "match_score":
            match_score,

        "skill_score":
            skill_score,

        "education_score":
            education_score,

        "experience_score":
            experience_score,

        "title_score":
            title_score,

        "text_similarity":
            text_similarity,

        "experience_years":
            experience_years,

        "matched_skills":
            matched,

        "missing_skills":
            missing,

        "all_extracted_skills":
            all_skills,

        "education":
            extract_education(text),

        "education_level":
            detect_education_level(text),

        "recommendation":
            band,

        "band":
            band,

        "compatibility_band":
            band,

        "position":
            canonical,

        "weights":
            weights,
    }


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    try:

        from database.database import get_db

        return get_db()

    except ImportError:

        return None

    except Exception as error:

        print(
            "Database connection helper warning: "
            f"{error}"
        )

        return None


# ============================================================
# ENSURE SCREENING TABLES
# ============================================================

def ensure_screening_tables():

    connection = get_db_connection()

    if not connection:
        return False

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id INT NOT NULL,
                job_profile VARCHAR(255),
                match_score DECIMAL(6,2),
                skill_score DECIMAL(6,2),
                education_score DECIMAL(6,2),
                experience_score DECIMAL(6,2),
                title_score DECIMAL(6,2),
                text_similarity DECIMAL(6,2),
                experience_years DECIMAL(6,2),
                recommendation VARCHAR(100),
                compatibility_band VARCHAR(100),
                matched_skills TEXT,
                missing_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_skills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                candidate_id INT NOT NULL,
                skill_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except Exception as error:

        print(
            "Could not create screening tables: "
            f"{error}"
        )

        try:
            connection.close()
        except Exception:
            pass

        return False


# ============================================================
# INSERT SCREENING RESULT
# ============================================================

def insert_screening_result(
    candidate_id,
    position,
    result,
):

    connection = get_db_connection()

    if not connection:
        return False

    try:

        cursor = connection.cursor()

        matched = ", ".join(
            result.get(
                "matched_skills",
                []
            )
        )

        missing = ", ".join(
            result.get(
                "missing_skills",
                []
            )
        )

        cursor.execute(
            """
            INSERT INTO screening_results
            (
                candidate_id,
                job_profile,
                match_score,
                skill_score,
                education_score,
                experience_score,
                title_score,
                text_similarity,
                experience_years,
                recommendation,
                compatibility_band,
                matched_skills,
                missing_skills
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s
            )
            """,
            (
                candidate_id,
                position,
                result.get("match_score", 0),
                result.get("skill_score", 0),
                result.get("education_score", 0),
                result.get("experience_score", 0),
                result.get("title_score", 0),
                result.get("text_similarity", 0),
                result.get("experience_years", 0),
                result.get("recommendation", ""),
                result.get("band", ""),
                matched,
                missing,
            ),
        )

        connection.commit()

        result_id = cursor.lastrowid

        cursor.close()
        connection.close()

        return result_id

    except Exception as error:

        print(
            "Could not save screening result: "
            f"{error}"
        )

        try:
            connection.rollback()
            connection.close()
        except Exception:
            pass

        return False


# ============================================================
# STORE CANDIDATE SKILLS
# ============================================================

def store_candidate_skills(
    candidate_id,
    skills,
):

    connection = get_db_connection()

    if not connection:
        return False

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM candidate_skills
            WHERE candidate_id = %s
            """,
            (candidate_id,),
        )

        for skill in skills:

            cursor.execute(
                """
                INSERT INTO candidate_skills
                (
                    candidate_id,
                    skill_name
                )
                VALUES
                (%s,%s)
                """,
                (
                    candidate_id,
                    skill
                ),
            )

        connection.commit()

        cursor.close()
        connection.close()

        return True

    except Exception as error:

        print(
            "Could not store candidate skills: "
            f"{error}"
        )

        try:
            connection.rollback()
            connection.close()
        except Exception:
            pass

        return False


# ============================================================
# COMPLETE SCREENING PIPELINE
# ============================================================

def run_cv_screening(
    candidate_id,
    file_path,
    position,
):

    print("=" * 60)

    print(
        "STARTING AI CV SCREENING"
    )

    print("=" * 60)

    text = extract_cv_text(
        file_path
    )

    if not text:

        return {
            "success": False,
            "error":
                "Could not extract text from CV.",
            "engine_version":
                ENGINE_VERSION,
        }

    result = calculate_match_score(
        text,
        position
    )

    result["candidate_id"] = candidate_id

    result["cv_file"] = file_path

    result["success"] = True

    result["screened_at"] = (
        datetime.now().isoformat()
    )

    # --------------------------------------------------------
    # Optional database storage
    #
    # app.py already performs the main screening database
    # storage in the current project. These calls remain safe
    # for standalone engine usage.
    # --------------------------------------------------------

    try:

        ensure_screening_tables()

        insert_screening_result(
            candidate_id,
            result.get(
                "position",
                position
            ),
            result
        )

        store_candidate_skills(
            candidate_id,
            result.get(
                "all_extracted_skills",
                []
            )
        )

    except Exception as error:

        print(
            "Database screening storage warning: "
            f"{error}"
        )

    print("=" * 60)

    print(
        "AI CV SCREENING COMPLETED"
    )

    print("=" * 60)

    print(
        f"Match Score: "
        f"{result['match_score']}%"
    )

    print(
        f"Experience: "
        f"{result['experience_years']} years"
    )

    print(
        f"Education Score: "
        f"{result['education_score']}%"
    )

    print(
        f"Skill Score: "
        f"{result['skill_score']}%"
    )

    print(
        f"Matched Skills: "
        f"{len(result['matched_skills'])}"
    )

    print(
        f"Missing Skills: "
        f"{len(result['missing_skills'])}"
    )

    print(
        f"Compatibility: "
        f"{result['band']}"
    )

    print("=" * 60)

    return result


# ============================================================
# TEST CV EXTRACTION
# ============================================================

def test_cv_extraction(file_path):

    text = extract_cv_text(
        file_path
    )

    return {

        "success":
            bool(text),

        "characters":
            len(text),

        "preview":
            text[:1000],

        "engine_version":
            ENGINE_VERSION,
    }


# ============================================================
# ENGINE STATUS
# ============================================================

def get_engine_status():

    return {

        "engine":
            "Intelligent CV Screening Engine",

        "version":
            ENGINE_VERSION,

        "pymupdf":
            PYMUPDF_AVAILABLE,

        "pypdf":
            PYPDF_AVAILABLE,

        "docx":
            DOCX_AVAILABLE,

        "tesseract":
            TESSERACT_AVAILABLE,

        "sklearn":
            SKLEARN_AVAILABLE,

        "skill_relationship_matching":
            True,

        "education_matching":
            True,

        "ocr_support":
            True,

        "status":
            "READY",
    }


# ============================================================
# STARTUP MESSAGE
# ============================================================

print(
    "AI CV screening engine loaded successfully. "
    f"Version {ENGINE_VERSION}"
)