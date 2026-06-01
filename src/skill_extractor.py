import spacy
from spacy.matcher import PhraseMatcher
import pandas as pd
import re


nlp = spacy.load("en_core_web_md")
#nlp = spacy.load("en_core_web_sm")


def load_skills_database(csv_path: str = "data/skills_dataset.csv") -> pd.DataFrame:
    """Load the skills dataset and expand aliases into a list."""
    df = pd.read_csv(csv_path)

    # Remove extra spaces from column names
    df.columns = df.columns.str.strip()

    # Convert aliases from string to list
    # Example: '"Python3, Py"' -> ['Python3', 'Py']
    def parse_aliases(alias_str):
        if pd.isna(alias_str) or str(alias_str).strip() == "":
            return []
        # Remove surrounding quotes if present
        alias_str = str(alias_str).strip().strip('"')
        # Split by comma and strip spaces
        return [a.strip() for a in alias_str.split(",") if a.strip()]

    df["aliases_list"] = df["aliases"].apply(parse_aliases)

    # Create a column with all variants (skill_name + aliases)
    # to be used in PhraseMatcher
    df["all_variants"] = df.apply(
        lambda row: [row["skill_name"].strip()] + row["aliases_list"], axis=1
    )

    return df


def build_phrase_matcher(skills_df: pd.DataFrame) -> tuple[PhraseMatcher, dict]:
    """Build a PhraseMatcher with all skills and their aliases.

    Returns:
        - matcher: the configured PhraseMatcher
        - variant_to_skill: dict mapping each variant to the main skill name
          Example: {"js": "JavaScript", "ecmascript": "JavaScript", "py": "Python"}
    """
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    # Dictionary mapping each alias (lowercase) back to the main skill
    # Ex: "py" -> "Python", "js" -> "JavaScript"
    variant_to_skill = {}

    for _, row in skills_df.iterrows():
        skill_name = row["skill_name"].strip()

        for variant in row["all_variants"]:
            variant_clean = variant.strip()
            if variant_clean:  # Don't add empty strings
                # Map the lowercase variant to the main skill
                variant_to_skill[variant_clean.lower()] = skill_name

                # Create the spaCy pattern and add it to the matcher
                pattern = nlp.make_doc(variant_clean)
                # Use skill_name as label for the matcher
                matcher.add(skill_name, [pattern])

    return matcher, variant_to_skill


def detect_sections(text: str) -> dict:
    """Detect sections in a JD: requirements, nice_to_have, etc.

    Returns a dict with:
    - 'must_have': text from Requirements/Must Have/Required section
    - 'good_to_have': text from Nice to Have/Preferred/Bonus section
    - 'full_text': the complete text (fallback)
    """
    sections = {
        "must_have": "",
        "good_to_have": "",
        "full_text": text
    }

    # Regex patterns for must_have sections
    must_have_keywords = (
        r'requirements|required\s+skills|must\s+have|qualifications|'
        r"what\s+you'll\s+need|what\s+we're\s+looking\s+for|"
        r'minimum\s+qualifications|essential\s+skills|key\s+skills|'
        r'required\s+qualifications|technical\s+requirements|what\s+you\s+need'
    )

    # Regex patterns for good_to_have sections
    good_to_have_keywords = (
        r'nice\s+to\s+have|preferred|bonus|good\s+to\s+have|desirable|'
        r'preferred\s+qualifications|additional\s+skills|'
        r'nice\-to\-have|good\-to\-have|advantageous'
    )

    # All possible section headers (used as delimiters)
    all_keywords = (
        must_have_keywords + r'|' +
        good_to_have_keywords + r'|' +
        r'responsibilities|about\s+the\s+role|about\s+us|'
        r"what\s+you'll\s+do|benefits|perks|compensation|"
        r'how\s+to\s+apply|about\s+the\s+company|'
        r'soft\s+skills|seniority|company\s+context|role\s+overview'
    )

    # Find all section headers in the text
    section_markers = []

    # Match lines that look like section headers:
    # - may have leading whitespace, numbers, or bullets
    # - contain the keyword
    # - may have extra short words around it (e.g. "Nice to Have / Good to Have:")
    # - total line length under 80 chars (real headers are short, not full sentences)
    pattern = r'(?im)^(.{0,80}(' + all_keywords + r').{0,40})$'
    for line_match in re.finditer(pattern, text):
        line_text = line_match.group(0).strip()
        # Skip lines that look like full sentences (contain verbs/long phrases)
        # Real headers are short: "Must Have Requirements:", "Nice to Have:"
        # Sentences are long: "Analyze requirements and clarify technical assumptions"
        word_count = len(line_text.split())
        if word_count > 10:
            continue
        section_markers.append({
            "start": line_match.start(),
            "end": line_match.end(),
            "header": line_text,
            "header_lower": line_text.lower()
        })

    # Sort by position in the text
    section_markers.sort(key=lambda x: x["start"])

    # Extract the text content of each section
    for i, marker in enumerate(section_markers):
        # Section text: from end of header to start of next header
        content_start = marker["end"]
        if i + 1 < len(section_markers):
            content_end = section_markers[i + 1]["start"]
        else:
            content_end = len(text)

        section_text = text[content_start:content_end].strip()
        header = marker["header_lower"]

        # Classify the section based on its header
        if re.search(must_have_keywords, header, re.IGNORECASE):
            sections["must_have"] += " " + section_text
        elif re.search(good_to_have_keywords, header, re.IGNORECASE):
            sections["good_to_have"] += " " + section_text

    # Clean up extra whitespace
    sections["must_have"] = sections["must_have"].strip()
    sections["good_to_have"] = sections["good_to_have"].strip()

    return sections

def extract_skills(text: str, csv_path: str = "data/skills_dataset.csv") -> list[dict]:
    """Main function - extracts skills from text and classifies them.

    Returns a list of dictionaries:
    [
        {"skill": "Python", "category": "programming", "priority": "must_have"},
        {"skill": "Docker", "category": "devops", "priority": "good_to_have"},
        ...
    ]
    """
    # 1. Load skills database
    skills_df = load_skills_database(csv_path)

    # 2. Build PhraseMatcher
    matcher, variant_to_skill = build_phrase_matcher(skills_df)

    # 3. Detect sections in the text
    sections = detect_sections(text)

    # 4. Run matcher on each section and collect results
    found_skills = {}  # skill_name -> {"category": ..., "priority": ...}

    # Build a quick lookup: skill_name -> category
    skill_to_category = {}
    for _, row in skills_df.iterrows():
        skill_to_category[row["skill_name"].strip()] = row["category"].strip()

    # Search in must_have section
    if sections["must_have"]:
        doc = nlp(sections["must_have"])
        matches = matcher(doc)
        for match_id, start, end in matches:
            matched_text = doc[start:end].text.lower()
            skill_name = variant_to_skill.get(matched_text, matched_text)
            if skill_name not in found_skills:
                found_skills[skill_name] = {
                    "skill": skill_name,
                    "category": skill_to_category.get(skill_name, "other"),
                    "priority": "must_have"
                }

    # Search in good_to_have section
    if sections["good_to_have"]:
        doc = nlp(sections["good_to_have"])
        matches = matcher(doc)
        for match_id, start, end in matches:
            matched_text = doc[start:end].text.lower()
            skill_name = variant_to_skill.get(matched_text, matched_text)
            # Only add if not already found in must_have
            # (must_have takes priority)
            if skill_name not in found_skills:
                found_skills[skill_name] = {
                    "skill": skill_name,
                    "category": skill_to_category.get(skill_name, "other"),
                    "priority": "good_to_have"
                }

    # 5. Fallback: if no sections were detected, search the full text
    if not sections["must_have"] and not sections["good_to_have"]:
        doc = nlp(sections["full_text"])
        matches = matcher(doc)
        for match_id, start, end in matches:
            matched_text = doc[start:end].text.lower()
            skill_name = variant_to_skill.get(matched_text, matched_text)
            if skill_name not in found_skills:
                found_skills[skill_name] = {
                    "skill": skill_name,
                    "category": skill_to_category.get(skill_name, "other"),
                    "priority": "must_have"  # Default when no sections found
                }

    # 6. Return as a sorted list
    result = list(found_skills.values())
    result.sort(key=lambda x: (x["priority"], x["category"], x["skill"]))

    return result