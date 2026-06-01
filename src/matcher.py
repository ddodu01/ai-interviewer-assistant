from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np

# Incarcam modelul
model = SentenceTransformer('all-MiniLM-L6-v2')


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Genereaza embedding-uri pentru o lista de texte.
    Exemplu:
    Input:["Python", "Docker", "machine learning"]
    Output: array de forma (3, 384) — 3 texte, fiecare cu 384 de numere
    """
    return model.encode(texts, convert_to_numpy=True)


def compute_similarity_matrix(jd_skills: list[str], cv_skills: list[str]) -> np.ndarray:
    """Calculeaza matricea de similaritate cosinus intre skills JD si skills CV

    Exemplu:
    jd_skills = ["Python", "Docker"]
    cv_skills = ["Python 3", "containerization", "cooking"]

    Returnează o matrice de forma (2, 3):
    [
        [0.97, 0.45, 0.12],   <- Python vs [Python 3, containerization, cooking]
        [0.41, 0.74, 0.08],   <- Docker vs [Python 3, containerization, cooking]
    ]
    """
    jd_embeddings = get_embeddings(jd_skills)
    cv_embeddings = get_embeddings(cv_skills)
    return cosine_similarity(jd_embeddings, cv_embeddings)


def match_skills(jd_skills_list: list[dict], cv_skills_list: list[dict],
                 threshold: float = 0.5) -> pd.DataFrame:
    """Functia principala — compara skills JD cu skills CV.

    Parametri:
    - jd_skills_list: output-ul de la extract_skills() pe JD
    - cv_skills_list: output-ul de la extract_skills() pe CV
    - threshold: pragul de similaritate pentru a decide Da/Nu (default 0.5)

    Returneaza un DataFrame cu coloanele:
    - jd_skill, category, priority, best_cv_match, similarity_score, match
    """
    # Extrage numele skill-urilor
    jd_names = [s["skill"] for s in jd_skills_list]
    cv_names = [s["skill"] for s in cv_skills_list]

    # Cazul in care CV-ul nu are niciun skill
    if not cv_names:
        return pd.DataFrame([{
            "jd_skill": s["skill"],
            "category": s["category"],
            "priority": s["priority"],
            "best_cv_match": "N/A",
            "similarity_score": 0.0,
            "match": "Nu"
        } for s in jd_skills_list])

    #  Calculeaza matricea de similaritate
    sim_matrix = compute_similarity_matrix(jd_names, cv_names)

    #  Construieste rezultatele
    results = []
    for i, jd_skill in enumerate(jd_skills_list):
        # Gaseste indexul skill-ului din CV cu cel mai mare scor
        best_idx = np.argmax(sim_matrix[i])
        best_score = float(sim_matrix[i][best_idx])
        best_match = cv_names[best_idx]

        results.append({
            "jd_skill": jd_skill["skill"],
            "category": jd_skill["category"],
            "priority": jd_skill["priority"],
            "best_cv_match": best_match,
            "similarity_score": round(best_score, 4),
            "match": "Da" if best_score >= threshold else "Nu"
        })

    return pd.DataFrame(results)