"""
Skill Extractor Service
-----------------------
Identifies skills from CV text using the project's
skills.json knowledge base.

The service:
    1. Loads the skills knowledge base
    2. Searches CV text for known skills
    3. Handles common skill variations
    4. Categorizes detected skills
    5. Removes duplicates
    6. Returns structured skill data
"""

import json
import os
import re


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

SKILLS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "skills.json"
)


# ============================================================
# SKILL EXTRACTOR CLASS
# ============================================================

class SkillExtractor:

    def __init__(self, skills_file=SKILLS_FILE):

        self.skills_file = skills_file

        self.skills_database = {}

        self.skill_lookup = {}

        self.load_skills()


    # ========================================================
    # LOAD SKILLS DATABASE
    # ========================================================

    def load_skills(self):

        if not os.path.exists(self.skills_file):

            raise FileNotFoundError(
                f"Skills database not found: {self.skills_file}"
            )

        try:

            with open(
                self.skills_file,
                "r",
                encoding="utf-8"
            ) as file:

                self.skills_database = json.load(file)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid skills.json file: {error}"
            )

        self.build_skill_lookup()


    # ========================================================
    # BUILD SEARCHABLE SKILL LOOKUP
    # ========================================================

    def build_skill_lookup(self):

        self.skill_lookup = {}

        for category, skills in self.skills_database.items():

            for skill in skills:

                normalized = self.normalize_skill(skill)

                if normalized:

                    self.skill_lookup[normalized] = {
                        "name": skill,
                        "category": category
                    }


    # ========================================================
    # NORMALIZE TEXT
    # ========================================================

    @staticmethod
    def normalize_text(text):

        if not text:
            return ""

        text = text.lower()

        text = text.replace("&", " and ")

        text = re.sub(
            r"[^a-z0-9+#.\-/ ]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()


    # ========================================================
    # NORMALIZE SKILL
    # ========================================================

    @staticmethod
    def normalize_skill(skill):

        if not skill:
            return ""

        skill = skill.lower().strip()

        skill = skill.replace("&", " and ")

        skill = re.sub(
            r"\s+",
            " ",
            skill
        )

        return skill


    # ========================================================
    # CREATE SEARCH PATTERN
    # ========================================================

    @staticmethod
    def create_pattern(skill):

        escaped_skill = re.escape(
            skill
        )

        return r"(?<![a-zA-Z0-9])" + escaped_skill + r"(?![a-zA-Z0-9])"


    # ========================================================
    # EXTRACT SKILLS
    # ========================================================

    def extract_skills(self, cv_text):

        if not cv_text:

            return []

        normalized_cv = self.normalize_text(
            cv_text
        )

        detected_skills = []

        for normalized_skill, skill_info in self.skill_lookup.items():

            pattern = self.create_pattern(
                normalized_skill
            )

            if re.search(
                pattern,
                normalized_cv,
                re.IGNORECASE
            ):

                detected_skills.append({
                    "skill": skill_info["name"],
                    "category": skill_info["category"]
                })

        return self.remove_duplicates(
            detected_skills
        )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    @staticmethod
    def remove_duplicates(skills):

        unique_skills = []

        seen = set()

        for item in skills:

            key = item["skill"].lower()

            if key not in seen:

                seen.add(key)

                unique_skills.append(
                    item
                )

        return unique_skills


    # ========================================================
    # EXTRACT SKILL NAMES ONLY
    # ========================================================

    def extract_skill_names(self, cv_text):

        skills = self.extract_skills(
            cv_text
        )

        return [
            item["skill"]
            for item in skills
        ]


    # ========================================================
    # GROUP SKILLS BY CATEGORY
    # ========================================================

    def group_by_category(self, skills):

        grouped = {}

        for item in skills:

            category = item["category"]

            if category not in grouped:

                grouped[category] = []

            grouped[category].append(
                item["skill"]
            )

        return grouped


    # ========================================================
    # COUNT SKILLS
    # ========================================================

    @staticmethod
    def count_skills(skills):

        return len(skills)


    # ========================================================
    # CHECK REQUIRED SKILLS
    # ========================================================

    def compare_skills(
        self,
        candidate_skills,
        required_skills
    ):

        candidate_map = {
            self.normalize_skill(skill): skill
            for skill in candidate_skills
        }

        matched = []
        missing = []

        for required_skill in required_skills:

            normalized_required = self.normalize_skill(
                required_skill
            )

            if normalized_required in candidate_map:

                matched.append(
                    required_skill
                )

            else:

                # Try partial/variation matching
                found_partial = False

                for candidate_skill in candidate_skills:

                    candidate_normalized = self.normalize_skill(
                        candidate_skill
                    )

                    if (
                        normalized_required in candidate_normalized
                        or
                        candidate_normalized in normalized_required
                    ):

                        matched.append(
                            required_skill
                        )

                        found_partial = True

                        break

                if not found_partial:

                    missing.append(
                        required_skill
                    )

        total_required = len(
            required_skills
        )

        total_matched = len(
            matched
        )

        if total_required > 0:

            match_percentage = round(
                (total_matched / total_required) * 100,
                2
            )

        else:

            match_percentage = 0

        return {
            "matched": matched,
            "missing": missing,
            "match_percentage": match_percentage
        }


    # ========================================================
    # GENERATE SKILL SUMMARY
    # ========================================================

    def generate_summary(self, cv_text):

        detected_skills = self.extract_skills(
            cv_text
        )

        grouped_skills = self.group_by_category(
            detected_skills
        )

        return {
            "total_skills": len(detected_skills),
            "skills": detected_skills,
            "categories": grouped_skills
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_skills_from_text(cv_text):

    extractor = SkillExtractor()

    return extractor.extract_skills(
        cv_text
    )


def compare_candidate_to_job(
    candidate_skills,
    required_skills
):

    extractor = SkillExtractor()

    return extractor.compare_skills(
        candidate_skills,
        required_skills
    )


# ============================================================
# BASIC TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("INTELLIGENT CV SCREENING SYSTEM")
    print("AI SKILL EXTRACTOR SERVICE")
    print("=" * 60)

    sample_cv = """
    Experienced Software Developer with 3 years of experience
    developing web applications using Python, Flask, JavaScript,
    HTML, CSS and MySQL.

    Experienced with Git, GitHub, Docker and REST APIs.

    Strong communication, teamwork and problem solving skills.
    """

    extractor = SkillExtractor()

    results = extractor.generate_summary(
        sample_cv
    )

    print()
    print("Detected Skills:")
    print("-" * 40)

    for skill in results["skills"]:

        print(
            f"✓ {skill['skill']} "
            f"({skill['category']})"
        )

    print()
    print(
        f"Total skills detected: "
        f"{results['total_skills']}"
    )

    print()
    print("Skill Categories:")
    print("-" * 40)

    for category, skills in results["categories"].items():

        print(
            f"{category}: "
            f"{', '.join(skills)}"
        )

    print()
    print("Skill extractor service is ready.")
    print("=" * 60)