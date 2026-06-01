import ollama
import logging

logger = logging.getLogger(__name__)


def generate_questions(skill: str, priority: str, nr_intrebari: int = 3, context_jd: str = "") -> list[str]:
    context_part = f"\nJob context: {context_jd[:300]}" if context_jd else ""

    # Cerem dublu față de ce vrem, ca să avem siguranță
    nr_cerut = nr_intrebari * 2

    prompt = f"""Generate {nr_cerut} technical interview questions about "{skill}".
{context_part}

Output ONLY the questions, one per line, numbered. Nothing else.

1. [question about {skill}]?
2. [question about {skill}]?
3. [question about {skill}]?"""

    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response["message"]["content"].strip()
        questions = _parse_questions(raw, nr_cerut)

        # Tăiem exact la numărul dorit
        questions = questions[:nr_intrebari]

        # Dacă tot nu avem destule, completăm cu o întrebare generică
        while len(questions) < nr_intrebari:
            questions.append(f"Can you describe your experience with {skill} and give a practical example?")

        logger.info(f"Generat {len(questions)} întrebări pentru '{skill}'")
        return questions
    except Exception as e:
        logger.error(f"Eroare Ollama pentru '{skill}': {e}")
        raise RuntimeError(f"Eroare la generarea întrebărilor pentru '{skill}': {e}")

def generate_questions_for_matches(matching_df, nr_intrebari: int = 3, context_jd: str = "") -> dict:
    """Generează întrebări pentru toate skill-urile din tabelul de matching.

    Args:
        matching_df:  DataFrame-ul returnat de match_skills()
        nr_intrebari: Numărul de întrebări per competență
        context_jd:   Textul JD-ului pentru context

    Returns:
        Dict: { "skill_name": ["întrebare1", "întrebare2", ...] }
    """
    results = {}
    for _, row in matching_df.iterrows():
        skill = row["jd_skill"]
        priority = row.get("priority", "Unknown")
        try:
            questions = generate_questions(skill, priority, nr_intrebari, context_jd)
            results[skill] = questions
        except RuntimeError as e:
            logger.warning(str(e))
            results[skill] = [f"Eroare la generarea întrebărilor: {e}"]
    return results


def _parse_questions(raw_text: str, nr_intrebari: int) -> list[str]:
    """Parsează răspunsul modelului și extrage întrebările numerotate."""
    lines = raw_text.strip().split("\n")
    questions = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Sare peste linii introductive (nu conțin "?")
        if "?" not in line:
            continue
        # Elimină numerotarea (1. / 1) / 1- etc.)
        import re
        line = re.sub(r"^\d+[\.\)\-]\s*", "", line).strip()
        if len(line) > 20:
            questions.append(line)
        if len(questions) >= nr_intrebari:
            break
    # Fallback dacă nu s-a prins nimic
    if not questions:
        questions = [l.strip() for l in lines if len(l.strip()) > 20 and "?" in l][:nr_intrebari]
    return questions


if __name__ == "__main__":
    # Test rapid
    print("Test generare întrebări pentru 'Python'...\n")
    questions = generate_questions("Python", "Must Have", nr_intrebari=3)
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
