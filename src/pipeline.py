import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Import module colegi ────────────────────────────────────────────────────

try:
    from parser import parse_document
except ImportError:
    logger.warning("parser.py nu a fost găsit — se folosește funcție mock.")
    def parse_document(path: str) -> str:
        """Mock: citește fișierul ca text simplu."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fișierul nu există: {path}")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

try:
    from skill_extractor import extract_skills
except ImportError:
    logger.warning("skill_extractor.py nu a fost găsit — se folosește funcție mock.")
    def extract_skills(text: str) -> list:
        """Mock: returnează cuvinte lungi ca 'skills'."""
        words = set(w.lower() for w in text.split() if len(w) > 5)
        return list(words)[:20]

try:
    from matcher import match_skills
except ImportError:
    logger.warning("matcher.py nu a fost găsit — se folosește funcție mock.")
    import pandas as pd
    import random


    def match_skills(jd_skills: list, cv_skills: list, threshold: float = 0.7) -> "pd.DataFrame":
        """Mock: generează un tabel dummy de matching."""
        rows = []
        for skill in jd_skills:
            # Extrage numele skill-ului indiferent dacă e dict sau string
            if isinstance(skill, dict):
                skill_name = skill.get("skill") or skill.get("name") or str(skill)
            else:
                skill_name = str(skill)

            score = random.uniform(0.5, 1.0)

            cv_names = []
            for s in cv_skills:
                if isinstance(s, dict):
                    cv_names.append((s.get("skill") or s.get("name") or str(s)).lower())
                else:
                    cv_names.append(str(s).lower())

            has_skill = skill_name.lower() in cv_names or score >= threshold
            rows.append({
                "Competență": skill_name,
                "Tip": "Must Have" if random.random() > 0.4 else "Good to Have",
                "Candidat are competența": "Da" if has_skill else "Nu",
                "Scor similaritate": round(score, 3),
            })
        return pd.DataFrame(rows)

# ─── Pipeline principal ──────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _validate_file(path: str) -> None:
    """Verifică dacă fișierul există și are extensie suportată."""
    if not path:
        raise ValueError("Calea fișierului nu poate fi goală.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fișierul nu a fost găsit: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Format nesuportat: '{ext}'. "
            f"Formate acceptate: {', '.join(SUPPORTED_EXTENSIONS)}"
        )


def run_pipeline(jd_path: str, cv_path: str, threshold: float = 0.7) -> dict:
    """Rulează pipeline-ul complet: parsare → extracție → matching.

    Args:
        jd_path:   Calea către fișierul Job Description (.pdf / .docx / .txt)
        cv_path:   Calea către fișierul CV (.pdf / .docx / .txt)
        threshold: Pragul de similaritate cosinus (0.0 – 1.0)

    Returns:
        Dict cu cheile:
            - 'jd_text'       : str — textul brut al JD-ului
            - 'cv_text'       : str — textul brut al CV-ului
            - 'jd_skills'     : list — competențe extrase din JD
            - 'cv_skills'     : list — competențe extrase din CV
            - 'matching_table': pd.DataFrame — tabelul de potrivire

    Raises:
        FileNotFoundError: dacă vreun fișier nu există
        ValueError:        dacă extensia nu e suportată sau threshold e invalid
        RuntimeError:      dacă un modul intern eșuează
    """
    # Validări input
    _validate_file(jd_path)
    _validate_file(cv_path)
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"Threshold trebuie să fie între 0 și 1, primit: {threshold}")

    logger.info("▶ Pipeline pornit")
    logger.info(f"  JD   : {jd_path}")
    logger.info(f"  CV   : {cv_path}")
    logger.info(f"  Prag : {threshold}")

    # 1. Parsare documente
    logger.info("[1/3] Parsare documente...")
    try:
        jd_text = parse_document(jd_path)
        cv_text = parse_document(cv_path)
    except Exception as e:
        raise RuntimeError(f"Eroare la parsare: {e}") from e

    if not jd_text.strip():
        raise ValueError("JD-ul este gol după parsare — verifică fișierul.")
    if not cv_text.strip():
        raise ValueError("CV-ul este gol după parsare — verifică fișierul.")
    logger.info(f"  JD: {len(jd_text)} caractere | CV: {len(cv_text)} caractere")

    # 2. Extracție competențe
    logger.info("[2/3] Extracție competențe...")
    try:
        jd_skills = extract_skills(jd_text)
        cv_skills = extract_skills(cv_text)
    except Exception as e:
        raise RuntimeError(f"Eroare la extracție competențe: {e}") from e

    logger.info(f"  JD skills: {len(jd_skills)} | CV skills: {len(cv_skills)}")

    # 3. Matching semantic
    logger.info("[3/3] Matching semantic...")
    try:
        matching_df = match_skills(jd_skills, cv_skills, threshold=threshold)
    except Exception as e:
        raise RuntimeError(f"Eroare la matching: {e}") from e

    logger.info(f"  Rezultate: {len(matching_df)} competențe analizate")
    logger.info("✅ Pipeline finalizat cu succes")

    return {
        "jd_text": jd_text,
        "cv_text": cv_text,
        "jd_skills": jd_skills,
        "cv_skills": cv_skills,
        "matching_table": matching_df,
    }


# ─── Test rapid (python src/pipeline.py) ────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Caută fișiere de test în data/
    jd_dir = os.path.join(os.path.dirname(__file__), "..", "data", "job_descriptions")
    cv_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cvs")

    jd_files = [f for f in os.listdir(jd_dir) if not f.startswith(".")] if os.path.exists(jd_dir) else []
    cv_files = [f for f in os.listdir(cv_dir) if not f.startswith(".")] if os.path.exists(cv_dir) else []

    if not jd_files or not cv_files:
        print("⚠ Nu există fișiere de test în data/job_descriptions sau data/cvs.")
        print("  Pune cel puțin un .txt în fiecare folder și reîncearcă.")
        sys.exit(1)

    jd_path = os.path.join(jd_dir, jd_files[0])
    cv_path = os.path.join(cv_dir, cv_files[0])

    print(f"\nTest cu: {jd_files[0]} + {cv_files[0]}\n")

    try:
        result = run_pipeline(jd_path, cv_path, threshold=0.7)
        print("\n── Tabel de potrivire ──────────────────────────────────")
        print(result["matching_table"].to_string(index=False))
        print(f"\nTotal competențe analizate: {len(result['matching_table'])}")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"❌ Eroare: {e}")
        sys.exit(1)