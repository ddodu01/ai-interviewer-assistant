import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor
import re

# Load model once at import time (slow, ~5 seconds)
nlp = spacy.load("en_core_web_lg")
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)


def detect_sections(text: str) -> dict:
    """Split JD text into sections: must_have and good_to_have.

    Searches for typical JD section headers and returns text from each section.
    Only considers short lines as headers (under 10 words) to avoid
    matching keywords inside regular sentences.
    """
    sections = {
        'must_have': '',
        'good_to_have': '',
        'full_text': text
    }

    # Patterns for mandatory requirements section
    must_have_keywords = (
        r'requirements?|required\s+skills?|must\s+have|qualifications?|'
        r"what\s+you'll\s+need|what\s+we're\s+looking\s+for|"
        r'minimum\s+qualifications?|essential\s+skills?|key\s+skills?|'
        r'required\s+qualifications?|technical\s+requirements?|mandatory'
    )

    # Patterns for optional requirements section
    good_to_have_keywords = (
        r'nice\s+to\s+have|preferred|bonus|good\s+to\s+have|desirable|'
        r'preferred\s+qualifications?|additional\s+skills?|'
        r'nice\-to\-have|good\-to\-have|advantageous|optionally?'
    )

    # All section delimiters combined
    all_keywords = (
        must_have_keywords + r'|' +
        good_to_have_keywords + r'|' +
        r'responsibilities|about\s+the\s+role|about\s+us|'
        r"what\s+you'll\s+do|benefits|perks|compensation|"
        r'how\s+to\s+apply|about\s+the\s+company|'
        r'soft\s+skills?|seniority|company\s+context|role\s+overview'
    )

    # Find all section headers in the text
    # Only match short lines (real headers are brief, not full sentences)
    section_markers = []
    pattern = r'(?im)^(.{0,80}(' + all_keywords + r').{0,40})$'
    for line_match in re.finditer(pattern, text):
        line_text = line_match.group(0).strip()
        # Skip lines that look like full sentences (over 10 words)
        if len(line_text.split()) > 10:
            continue
        section_markers.append({
            'start': line_match.start(),
            'end': line_match.end(),
            'header': line_text,
            'header_lower': line_text.lower()
        })

    # Sort by position in text
    section_markers.sort(key=lambda x: x['start'])

    # Extract text content of each section
    for i, marker in enumerate(section_markers):
        content_start = marker['end']
        if i + 1 < len(section_markers):
            content_end = section_markers[i + 1]['start']
        else:
            content_end = len(text)

        section_text = text[content_start:content_end].strip()
        header = marker['header_lower']

        if re.search(must_have_keywords, header, re.IGNORECASE):
            sections['must_have'] += ' ' + section_text
        elif re.search(good_to_have_keywords, header, re.IGNORECASE):
            sections['good_to_have'] += ' ' + section_text

    sections['must_have'] = sections['must_have'].strip()
    sections['good_to_have'] = sections['good_to_have'].strip()

    return sections


def get_skill_type(skill_name: str) -> str:
    """Look up the type of a skill in the SkillNER database.

    Returns: 'Hard Skill', 'Soft Skill', 'Certification' or 'Unknown'
    """
    for skill_id, skill_data in SKILL_DB.items():
        if skill_data.get('skill_name', '').lower() == skill_name.lower():
            return skill_data.get('skill_type', 'Unknown')
    return 'Unknown'


def extract_raw_skills(text: str) -> list[str]:
    """Extract skills from text using SkillNER.

    Returns a list of skill names (strings).
    """
    if not text or len(text.strip()) < 10:
        return []

    try:
        annotations = skill_extractor.annotate(text)
        skills_found = []

        # Full matches - SkillNER is confident these are skills
        for match in annotations['results']['full_matches']:
            skill_id = match['skill_id']
            skill_name = SKILL_DB.get(skill_id, {}).get('skill_name', None)
            if skill_name and skill_name not in skills_found:
                skills_found.append(skill_name)

        # Ngram scored - filter by score > 0.5 to reduce noise
        for match in annotations['results']['ngram_scored']:
            score = match.get('score', 0)
            if score > 0.5:
                skill_id = match['skill_id']
                skill_name = SKILL_DB.get(skill_id, {}).get('skill_name', None)
                if skill_name and skill_name not in skills_found:
                    skills_found.append(skill_name)

        return skills_found

    except Exception as e:
        print(f"Warning: SkillNER error on text snippet: {e}")
        return []


def extract_skills(text: str, is_jd: bool = True) -> list[dict]:
    """Main function - extract and classify skills from text.

    Parameters:
    - text: raw text from a JD or CV
    - is_jd: True if text is a Job Description (classify Must/Good to Have)
             False if text is a CV (all skills marked as 'present')

    Returns a list of dictionaries:
    [
        {"skill": "Python", "skill_type": "Hard Skill", "priority": "must_have"},
        {"skill": "Communication", "skill_type": "Soft Skill", "priority": "good_to_have"},
    ]
    """
    results = []
    seen_skills = set()

    if is_jd:
        # For JDs, detect sections and classify accordingly
        sections = detect_sections(text)

        # Extract skills from must_have section (fallback to full text)
        must_text = sections['must_have'] if sections['must_have'] else sections['full_text']
        for skill_name in extract_raw_skills(must_text):
            if skill_name.lower() not in seen_skills:
                seen_skills.add(skill_name.lower())
                results.append({
                    "skill": skill_name,
                    "skill_type": get_skill_type(skill_name),
                    "priority": "must_have"
                })

        # Extract skills from good_to_have section
        if sections['good_to_have']:
            for skill_name in extract_raw_skills(sections['good_to_have']):
                if skill_name.lower() not in seen_skills:
                    seen_skills.add(skill_name.lower())
                    results.append({
                        "skill": skill_name,
                        "skill_type": get_skill_type(skill_name),
                        "priority": "good_to_have"
                    })

    else:
        # For CVs, extract all skills without Must/Good classification
        for skill_name in extract_raw_skills(text):
            if skill_name.lower() not in seen_skills:
                seen_skills.add(skill_name.lower())
                results.append({
                    "skill": skill_name,
                    "skill_type": get_skill_type(skill_name),
                    "priority": "present"
                })

    return results