# 🤖 AI Interviewer Assistant Tool

Sistem inteligent care analizează Job Descriptions și CV-uri, identifică competențe relevante și generează automat întrebări de interviu structurate.

---

## Echipa

| Nume                   | Rol | Responsabilități |
|------------------------|-----|-----------------|
| Dorhoi Mara Iulia      | Date & Parsare | Colectare dataset, parsare PDF/DOCX/TXT, analiză exploratorie |
| Dodu Daniel Ionut      | Extracție NLP | Extracția competențelor cu SkillNer + spaCy, clasificare Must/Good to Have |
| Dobinda Catalin Andrei | Matching Semantic | Sentence-BERT embeddings, cosine similarity, evaluare model |
| Dumiter George Gabriel | Integrare & UI | Pipeline, Streamlit, generare întrebări LLM cu Ollama, video teaser |

---

## Problema abordată

Pregătirea interviurilor tehnice este un proces manual, consumator de timp și adesea subiectiv. Recrutorii trebuie să compare manual CV-uri cu cerințele postului și să formuleze întrebări relevante pentru fiecare candidat. Instrumentul nostru automatizează acest proces de la capăt la capăt.

---

## Soluția propusă

Un pipeline AI care primește un Job Description și un CV, extrage și compară competențele, apoi generează întrebări de interviu personalizate.

```
[JD + CV] → Parsare → Extracție NLP → Matching Semantic → Generare Întrebări → UI
```

**Inputuri:** Job Description + CV (PDF / DOCX / TXT), număr de întrebări dorite per competență  
**Outputuri:** Tabel de potrivire competențe (cu scor de similaritate) + întrebări de interviu generate automat

---

## Pipeline de integrare (`src/pipeline.py`)

Modulul `pipeline.py` leagă toate componentele sistemului într-un flux unic, apelat atât din interfața Streamlit cât și din linia de comandă.

**Flux de execuție:**

```
parse_document(jd_path)  ──┐
                            ├──► extract_skills() ──► match_skills() ──► dict rezultate
parse_document(cv_path)  ──┘
```

**Funcția principală:**

```python
result = run_pipeline(jd_path, cv_path, threshold=0.7)
# Returnează:
# result['jd_text']        — textul brut al JD-ului
# result['cv_text']        — textul brut al CV-ului
# result['jd_skills']      — lista de competențe extrase din JD
# result['cv_skills']      — lista de competențe extrase din CV
# result['matching_table'] — DataFrame cu tabelul de potrivire
```

**Caracteristici tehnice:**
- Validare input: verifică existența fișierului, extensia suportată (`.pdf`, `.docx`, `.txt`) și că textul parsat nu este gol
- Fallback automat cu funcții mock dacă un modul nu este disponibil
- Logging cu timestamps la fiecare etapă a pipeline-ului
- Tratare erori tipizată: `FileNotFoundError`, `ValueError`, `RuntimeError`
- Rulare directă pentru testare rapidă: `python src/pipeline.py`

---

## Interfața web (`app.py`)

Aplicația Streamlit oferă o interfață vizuală completă pentru rularea pipeline-ului fără linie de comandă.

**Funcționalități principale:**

| Componentă | Descriere |
|------------|-----------|
| Upload documente | Sidebar cu încărcare JD + CV (PDF / DOCX / TXT) |
| Slider threshold | Configurare prag de similaritate cosinus (0.30 – 0.95) |
| Tabel de potrivire | Skill cerut, prioritate, cel mai bun match din CV, scor similaritate cu bară de progres |
| Metrici sumar | 4 carduri: total competențe, câte are candidatul, rată de potrivire %, scor mediu |
| Avertismente inteligente | Warning automat dacă lipsesc competențe Must Have |
| Generare întrebări | Selectare număr de întrebări + generare automată cu Ollama pentru skillurile identificate |
| Export CSV | Descărcare tabel de rezultate |
| Debug expandere | Texte parsate și skills extrase (ascunse implicit) |
| Session state | Rezultatele persistă între interacțiuni fără resetarea paginii |

**Rulare:**

```bash
streamlit run app.py
```

Aplicația se deschide automat în browser la `http://localhost:8501`.

---

## Generare întrebări de interviu (`src/question_generator.py`)

Modulul folosește **Ollama (llama3)** rulat local pentru a genera întrebări de interviu personalizate per competență.

**Cum funcționează:**

```
Skill identificat + Prioritate + Context JD
            ↓
    Prompt Engineering
            ↓
    Ollama (llama3) — rulat local, fără internet
            ↓
    Întrebări tehnice structurate
```

**Tehnici folosite:**
- **Prompt engineering** — instrucțiuni clare cu format demonstrat (few-shot prompting) pentru a controla outputul modelului
- **Context injection** — primele 300 de caractere din JD sunt incluse în prompt pentru întrebări relevante jobului specific
- **Oversampling** — se cer de 2x mai multe întrebări decât e nevoie, apoi se taie la numărul dorit pentru a garanta acoperirea
- **Post-procesare** — filtrare linii fără `?`, eliminare numerotare, fallback automat dacă modelul generează prea puțin

**Funcția principală:**

```python
questions = generate_questions(skill, priority, nr_intrebari=3, context_jd="...")
# Returnează: ["Întrebare 1?", "Întrebare 2?", "Întrebare 3?"]
```

---

## Finetuning și îmbunătățiri

Sistemul include trei niveluri de finetuning fără antrenarea unui model de la zero:

| Nivel | Fișier | Ce face |
|-------|--------|---------|
| Skilluri custom | `skill_extractor.py` → `CUSTOM_SKILLS` | Adaugă skilluri noi în SKILL_DB la runtime (FastAPI, LangChain, Next.js etc.) |
| Pattern-uri secțiuni JD | `skill_extractor.py` → regex `must_have_keywords` / `good_to_have_keywords` | Recunoaște mai multe headere din JD-uri reale |
| Threshold matching | `matcher.py` + slider UI | Ajustează pragul de similaritate cosinus |

---

## Modele și tehnologii AI folosite

| Componentă | Tehnologie | Rol |
|------------|-----------|-----|
| Extracție competențe | `SkillNer` + spaCy `en_core_web_lg` | Identificare automată skilluri din text folosind SKILL_DB |
| Detectare secțiuni JD | Regex patterns + spaCy | Clasificare Must Have / Good to Have din structura JD-ului |
| Matching semantic | `sentence-transformers/all-MiniLM-L6-v2` (Sentence-BERT) | Embeddings + cosine similarity între skill-uri JD vs CV |
| Generare întrebări | **Ollama — llama3** (rulat local) | LLM cu prompt engineering pentru întrebări tehnice structurate |

---

## Tech Stack

- **Python 3.11** — limbaj principal
- **PyPDF2, python-docx** — parsare documente
- **spaCy + en_core_web_lg** — procesare NLP
- **SkillNer** — extracție competențe din SKILL_DB
- **sentence-transformers** — embeddings semantice
- **scikit-learn** — cosine similarity, metrici evaluare
- **pandas, matplotlib, wordcloud** — analiză și vizualizări
- **Ollama (llama3)** — generare întrebări de interviu, rulat local
- **Streamlit** — interfață web

---

## Instalare și rulare

```bash
# Clonare repo
git clone [URL]
cd ai-interviewer-assistant

# Instalare dependențe Python
pip install -r requirements.txt

# Descărcare model spaCy
python -m spacy download en_core_web_lg

# Instalare Ollama (Windows)
# Descarcă de pe https://ollama.com/download și instalează

# Descărcare model llama3
ollama pull llama3

# Rulare aplicație
streamlit run app.py
```

Aplicația se deschide automat la `http://localhost:8501`.

> **Notă:** Ollama trebuie să ruleze în background pentru funcționalitatea de generare întrebări. Se pornește automat după instalare.

---

## Structura proiectului

```
ai-interviewer-assistant/
├── data/
│   ├── job_descriptions/   ← 20 JD-uri reale (.txt)
│   ├── cvs/                ← CV-uri candidați
│   └── skills_dataset.csv  ← dataset competențe etichetate
├── notebooks/
│   ├── 01_data_analysis.ipynb
│   ├── 02_skill_extraction.ipynb
│   ├── 03_matching_model.ipynb
│   └── 04_question_generation.ipynb
├── src/
│   ├── parser.py              ← parsare PDF/DOCX/TXT
│   ├── skill_extractor.py     ← extracție skilluri cu SkillNer + finetuning custom
│   ├── matcher.py             ← matching semantic Sentence-BERT
│   ├── question_generator.py  ← generare întrebări cu Ollama llama3
│   └── pipeline.py            ← integrare toate modulele
├── app.py                     ← interfață Streamlit
├── requirements.txt
└── README.md
```

---

## SDG-uri impactate

- **SDG 8 — Muncă decentă și creștere economică:** Eficientizarea procesului de recrutare
- **SDG 10 — Reducerea inegalităților:** Evaluare standardizată, reducerea bias-ului subiectiv în selecția candidaților
- **SDG 4 — Educație de calitate:** Feedback structurat și întrebări relevante pentru candidați

---

## Link prezentare video
https://youtu.be/DZUe8Y5TSyY

---


## Bibliografie

- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP 2019.
- Honnibal, M. et al. (2020). *spaCy: Industrial-strength Natural Language Processing in Python.*
- Touvron, H. et al. (2023). *Llama 2: Open Foundation and Fine-Tuned Chat Models.* Meta AI.
- Nguyen, A. et al. (2021). *SkillNer: Mining and Normalizing Skill Mentions in Job Postings.* 
- Ollama. (2023). *Run Large Language Models Locally.* https://ollama.com
