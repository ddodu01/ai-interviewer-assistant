"""
Finetuning SkillNer — extinderea SKILL_DB cu skilluri moderne.

Procesul:
1. Am testat extracția pe toate cele 20 JD-uri din data/job_descriptions/
2. Am identificat manual skillurile care nu erau detectate
3. Le-am adăugat în CUSTOM_SKILLS de mai jos
4. Am măsurat îmbunătățirea în notebooks/02_skill_extraction.ipynb
"""

import uuid
from skillNer.general_params import SKILL_DB


# ── Skilluri identificate ca lipsă după testare manuală ──────────────────────

CUSTOM_SKILLS = [
    # Frameworks moderne web/backend
    {"skill_name": "FastAPI",           "skill_type": "Hard Skill"},
    {"skill_name": "Next.js",           "skill_type": "Hard Skill"},
    {"skill_name": "NestJS",            "skill_type": "Hard Skill"},
    {"skill_name": "Prisma",            "skill_type": "Hard Skill"},
    {"skill_name": "GraphQL",           "skill_type": "Hard Skill"},
    {"skill_name": "tRPC",              "skill_type": "Hard Skill"},

    # AI / ML tools
    {"skill_name": "LangChain",         "skill_type": "Hard Skill"},
    {"skill_name": "Ollama",            "skill_type": "Hard Skill"},
    {"skill_name": "Hugging Face",      "skill_type": "Hard Skill"},
    {"skill_name": "Sentence-BERT",     "skill_type": "Hard Skill"},
    {"skill_name": "SkillNer",          "skill_type": "Hard Skill"},
    {"skill_name": "Streamlit",         "skill_type": "Hard Skill"},
    {"skill_name": "LLM",               "skill_type": "Hard Skill"},
    {"skill_name": "Prompt Engineering","skill_type": "Hard Skill"},
    {"skill_name": "RAG",               "skill_type": "Hard Skill"},
    {"skill_name": "Fine-tuning",       "skill_type": "Hard Skill"},

    # DevOps / Cloud
    {"skill_name": "Kubernetes",        "skill_type": "Hard Skill"},
    {"skill_name": "GitHub Actions",    "skill_type": "Hard Skill"},
    {"skill_name": "Terraform",         "skill_type": "Hard Skill"},
    {"skill_name": "Helm",              "skill_type": "Hard Skill"},

    # Baze de date moderne
    {"skill_name": "Supabase",          "skill_type": "Hard Skill"},
    {"skill_name": "PlanetScale",       "skill_type": "Hard Skill"},
    {"skill_name": "Pinecone",          "skill_type": "Hard Skill"},
    {"skill_name": "Weaviate",          "skill_type": "Hard Skill"},

    # Soft skills
    {"skill_name": "Agile",             "skill_type": "Soft Skill"},
    {"skill_name": "Scrum",             "skill_type": "Soft Skill"},
    {"skill_name": "Kanban",            "skill_type": "Soft Skill"},
    {"skill_name": "Code Review",       "skill_type": "Soft Skill"},

    {"skill_name": "Problem Solving",           "skill_type": "Soft Skill"},
    {"skill_name": "Adaptability",              "skill_type": "Soft Skill"},
    {"skill_name": "Teamwork",                  "skill_type": "Soft Skill"},
    {"skill_name": "Collaboration",             "skill_type": "Soft Skill"},
    {"skill_name": "Time Management",           "skill_type": "Soft Skill"},
    {"skill_name": "Relationship Building",     "skill_type": "Soft Skill"},
    {"skill_name": "Attention to Detail",       "skill_type": "Soft Skill"},
    {"skill_name": "Negotiation",               "skill_type": "Soft Skill"},
    {"skill_name": "Strategic Thinking",        "skill_type": "Soft Skill"},
    {"skill_name": "Self-motivation",           "skill_type": "Soft Skill"},
    {"skill_name": "Analytical Thinking",       "skill_type": "Soft Skill"},
    {"skill_name": "Confidentiality",           "skill_type": "Soft Skill"},
    {"skill_name": "Change Management",         "skill_type": "Soft Skill"},
    {"skill_name": "Critical Thinking",         "skill_type": "Soft Skill"},
    {"skill_name": "Coaching",                  "skill_type": "Soft Skill"},

    # Hard skills business
    {"skill_name": "Data Analysis",             "skill_type": "Hard Skill"},
    {"skill_name": "Project Management",        "skill_type": "Hard Skill"},
    {"skill_name": "Financial Analysis",        "skill_type": "Hard Skill"},
    {"skill_name": "Financial Reporting",       "skill_type": "Hard Skill"},
    {"skill_name": "Financial Modeling",        "skill_type": "Hard Skill"},
    {"skill_name": "Customer Relationship Management", "skill_type": "Hard Skill"},
    {"skill_name": "Microsoft Office",          "skill_type": "Hard Skill"},
    {"skill_name": "Microsoft Excel",           "skill_type": "Hard Skill"},
    {"skill_name": "Performance Management",    "skill_type": "Hard Skill"},
    {"skill_name": "Business Development",      "skill_type": "Hard Skill"},
    {"skill_name": "Market Analysis",           "skill_type": "Hard Skill"},
    {"skill_name": "Strategic Planning",        "skill_type": "Hard Skill"},
    {"skill_name": "Budgeting",                 "skill_type": "Hard Skill"},
    {"skill_name": "Lead Generation",           "skill_type": "Hard Skill"},
    {"skill_name": "Recruitment",               "skill_type": "Hard Skill"},
    {"skill_name": "Employee Relations",        "skill_type": "Hard Skill"},
]



def load_custom_skills(custom_skills: list[dict] = None) -> int:
    if custom_skills is None:
        custom_skills = CUSTOM_SKILLS

    # Luăm un entry existent ca template
    template = next(iter(SKILL_DB.values()))

    added = 0
    for skill in custom_skills:
        skill_name = skill["skill_name"]

        already_exists = any(
            v.get("skill_name", "").lower() == skill_name.lower()
            for v in SKILL_DB.values()
        )

        if not already_exists:
            skill_id = f"custom_{str(uuid.uuid4())[:8]}"

            # Copiem structura completă din template
            import copy
            new_entry = copy.deepcopy(template)

            # Suprascriem câmpurile noastre
            new_entry["skill_name"] = skill_name
            new_entry["skill_type"] = skill.get("skill_type", "Hard Skill")
            new_entry["skill_len"] = len(skill_name.split())
            new_entry["high_surfce_forms"] = {
                "full": skill_name,
                "lower": skill_name.lower(),
                "abbreviated": skill_name
            }

            SKILL_DB[skill_id] = new_entry
            added += 1

    return added

def get_custom_skill_names() -> list[str]:
    """Returnează lista numelor de skilluri custom."""
    return [s["skill_name"] for s in CUSTOM_SKILLS]


# ── Auto-load la import ───────────────────────────────────────────────────────
_added = load_custom_skills()
if _added > 0:
    print(f"[finetune_skills] Adăugate {_added} skilluri custom în SKILL_DB.")


if __name__ == "__main__":
    print(f"Total skilluri custom definite: {len(CUSTOM_SKILLS)}")
    print(f"Skilluri adăugate în SKILL_DB: {_added}")
    print(f"Total skilluri în SKILL_DB după finetuning: {len(SKILL_DB)}")
    print("\nSkilluri custom:")
    for s in CUSTOM_SKILLS:
        print(f"  - {s['skill_name']} ({s['skill_type']})")