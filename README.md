# 🤖 AI Interviewer Assistant Tool

Sistem inteligent care analizează Job Descriptions și CV-uri, identifică competențe relevante și generează automat întrebări de interviu structurate.

---

## Echipa

| Nume                   | Rol | Responsabilități |
|------------------------|-----|-----------------|
| Dorhoi Mara Iulia      | Date & Parsare | Colectare dataset, parsare PDF/DOCX/TXT, analiză exploratorie |
| Dodu Daniel Ionut      | Extracție NLP | Extracția competențelor cu spaCy, clasificare Must/Good to Have |
| Dobinda Catalin Andrei | Matching Semantic | Sentence-BERT embeddings, cosine similarity, evaluare model |
| Dumiter George Gabriel | Integrare & UI | Pipeline, Streamlit, generare întrebări LLM, video teaser |

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
- Fallback automat cu funcții mock dacă un modul al unui coleg nu este încă disponibil (util în faza de dezvoltare paralelă)
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
| Tabel de potrivire | Badge-uri colorate pentru Tip (Must Have / Good to Have) și prezență competență (Da / Nu), bare de progres pentru scor |
| Metrici sumar | 4 carduri: total competențe, câte are candidatul, rată de potrivire %, scor mediu |
| Avertismente inteligente | Warning automat dacă lipsesc competențe Must Have |
| Export CSV | Descărcare tabel de rezultate |
| Debug expandere | Texte parsate și skills extrase (ascunse implicit) |

**Rulare:**

```bash
streamlit run app.py
```

Aplicația se deschide automat în browser la `http://localhost:8501`.

> **Săptămâna 14:** Interfața va include și secțiunea de generare automată a întrebărilor de interviu prin Google Gemini API.

---

## Modele și tehnologii AI folosite

| Componentă | Tehnologie | Rol |
|------------|-----------|-----|
| Extracție competențe | spaCy `en_core_web_md` + PhraseMatcher | NER pentru identificarea skill-urilor din text |
| Matching semantic | `sentence-transformers/all-MiniLM-L6-v2` (Sentence-BERT) | Embeddings + cosine similarity între skill-uri JD vs CV |
| Generare întrebări | **Google Gemini API** (`gemini-pro`) | LLM cu prompt engineering pentru întrebări structurate |

Gemini primește ca input competența identificată, tipul ei (Must Have / Good to Have) și contextul din JD, generând întrebări tehnice și comportamentale relevante.

---

## Tech Stack

- **Python 3.11** — limbaj principal
- **PyPDF2, python-docx** — parsare documente
- **spaCy** — procesare NLP
- **sentence-transformers** — embeddings semantice
- **scikit-learn** — metrici evaluare
- **pandas, matplotlib, wordcloud** — analiză și vizualizări
- **Google Gemini API** — generare întrebări cu LLM
- **Streamlit** — interfață web

---

## Instalare și rulare

```bash
git clone [URL]
cd ai-interviewer-assistant

pip install -r requirements.txt
python -m spacy download en_core_web_md

streamlit run app.py
```

---

## Structura proiectului

```
ai-interviewer-assistant/
├── data/
│   ├── job_descriptions/   ← 15-20 JD-uri reale (.txt)
│   ├── cvs/                ← 15-20 CV-uri
│   └── skills_dataset.csv  ← dataset competențe etichetate
├── notebooks/
│   ├── 01_data_analysis.ipynb
│   ├── 02_skill_extraction.ipynb
│   ├── 03_matching_model.ipynb
│   └── 04_question_generation.ipynb
├── src/
│   ├── parser.py
│   ├── skill_extractor.py
│   ├── matcher.py
│   ├── question_generator.py
│   └── pipeline.py
├── app.py
├── requirements.txt
└── README.md
```

---

## SDG-uri impactate

- **SDG 8 — Muncă decentă și creștere economică:** Eficientizarea procesului de recrutare
- **SDG 10 — Reducerea inegalităților:** Evaluare standardizată, reducerea bias-ului subiectiv
- **SDG 4 — Educație de calitate:** Feedback structurat pentru candidați

---

## Bibliografie

- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP 2019.
- Honnibal, M. et al. (2020). *spaCy: Industrial-strength Natural Language Processing in Python.*
- Google DeepMind. (2023). *Gemini: A Family of Highly Capable Multimodal Models.*
