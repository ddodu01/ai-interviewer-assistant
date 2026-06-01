import streamlit as st
import tempfile
import os
import pandas as pd
import sys

# ─── Path setup ──────────────────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from pipeline import run_pipeline

# ─── Configurare pagină ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interviewer Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS custom ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        color: white; padding: 2rem 2.5rem; border-radius: 16px; margin-bottom: 2rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
    .main-header p  { margin: 0.5rem 0 0; opacity: 0.85; font-size: 1rem; }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 1.25rem 1.5rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .metric-card .value { font-size: 2.2rem; font-weight: 700; color: #1e3a5f; }
    .metric-card .label { font-size: 0.85rem; color: #64748b; margin-top: 0.2rem; }
    .badge-must { background:#fef2f2; color:#dc2626; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    .badge-good { background:#eff6ff; color:#2563eb; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; }
    section[data-testid="stSidebar"] { background: #f8fafc; }
    .match-bar-wrap { background:#e2e8f0; border-radius:8px; height:8px; width:100%; }
    .match-bar-fill { height:8px; border-radius:8px; transition: width 0.4s ease; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.5rem 0; }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3a5f, #2563eb);
        border: none; color: white; border-radius: 10px;
        font-weight: 600; padding: 0.6rem 1.5rem; transition: opacity 0.2s;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover { opacity: 0.88; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Interviewer Assistant Tool</h1>
    <p>Analizează potrivirea dintre un Job Description și un CV și generează întrebări de interviu structurate</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 Încarcă documentele")
    st.markdown("Formate acceptate: **PDF, DOCX, TXT**")
    jd_file = st.file_uploader("Job Description", type=["pdf", "docx", "txt"])
    cv_file = st.file_uploader("CV Candidat", type=["pdf", "docx", "txt"])
    st.markdown("---")
    st.markdown("## ⚙️ Setări")
    threshold = st.slider("Prag de similaritate", min_value=0.30, max_value=0.95, value=0.70, step=0.05)
    st.caption(f"Valoare curentă: **{threshold:.2f}**")
    st.markdown("---")
    analyze_btn = st.button("🔍 Analizează", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("### ℹ️ Despre")
    st.markdown("Instrument AI pentru recrutori: identifică competențele din JD și CV, calculează potrivirea semantică și generează întrebări de interviu.")

# ─── Helpers ─────────────────────────────────────────────────────────────────

def save_temp_file(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name

def score_color(score: float) -> str:
    if score >= 0.80:
        return "#16a34a"
    elif score >= 0.60:
        return "#d97706"
    else:
        return "#dc2626"

def render_matching_table(df: pd.DataFrame) -> None:
    required_cols = {"jd_skill", "priority", "best_cv_match", "similarity_score", "match"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Coloane lipsă din tabel: {missing}")
        st.dataframe(df)
        return

    col_widths = [2, 2, 2, 3]
    headers = st.columns(col_widths)
    for h, label in zip(headers, ["Skill cerut", "Prioritate", "Cel mai bun match CV", "Scor similaritate"]):
        h.markdown(f"**{label}**")
    st.markdown("<hr style='margin:0.3rem 0 0.5rem'>", unsafe_allow_html=True)

    for _, row in df.iterrows():
        cols = st.columns(col_widths)
        cols[0].markdown(f"`{row['jd_skill']}`")
        cols[1].markdown(f"`{row['priority']}`")
        cols[2].markdown(f"`{row['best_cv_match']}`")
        score = float(row["similarity_score"])
        pct = int(score * 100)
        color = score_color(score)
        cols[3].markdown(
            f"""<div style="display:flex; align-items:center; gap:10px;">
                <div class="match-bar-wrap" style="flex:1">
                    <div class="match-bar-fill" style="width:{pct}%; background:{color}"></div>
                </div>
                <span style="font-size:0.85rem; font-weight:600; color:{color}; min-width:38px">{score:.2f}</span>
            </div>""",
            unsafe_allow_html=True,
        )

def render_summary(df: pd.DataFrame) -> None:
    total = len(df)
    n_da = (df["match"] == "Da").sum() if "match" in df.columns else 0
    n_must_lipsa = (
        (df["priority"].str.lower().str.contains("must", na=False)) &
        (df["match"] == "Nu")
    ).sum() if all(c in df.columns for c in ["priority", "match"]) else 0
    avg_score = df["similarity_score"].mean() if "similarity_score" in df.columns else 0.0
    match_pct = int((n_da / total * 100)) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, total,               "Competențe analizate"),
        (c2, f"{n_da} / {total}", "Competențe identificate"),
        (c3, f"{match_pct}%",     "Rată de potrivire"),
        (c4, f"{avg_score:.2f}",  "Scor mediu similaritate"),
    ]:
        col.markdown(
            f'<div class="metric-card"><div class="value">{val}</div><div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )

    if n_must_lipsa > 0:
        st.warning(f"⚠️ Candidatul nu are {n_must_lipsa} competență/e Must Have.")
    elif n_da == total:
        st.success("✅ Candidatul îndeplinește toate competențele cerute!")
    else:
        st.info(f"ℹ️ Candidatul are {n_da} din {total} competențe cerute.")

# ─── Logică principală ────────────────────────────────────────────────────────

# Inițializare session_state
if "result" not in st.session_state:
    st.session_state["result"] = None
if "questions_dict" not in st.session_state:
    st.session_state["questions_dict"] = {}

# ── Buton Analizează ──
if analyze_btn:
    if not jd_file or not cv_file:
        st.error("⚠️ Te rog încarcă atât **Job Description-ul** cât și **CV-ul** înainte de analiză.")
    else:
        jd_tmp = None
        cv_tmp = None
        try:
            jd_tmp = save_temp_file(jd_file)
            cv_tmp = save_temp_file(cv_file)
            with st.spinner("⏳ Se analizează documentele... (parsare → extracție → matching)"):
                result = run_pipeline(jd_tmp, cv_tmp, threshold=threshold)
            st.session_state["result"] = result
            st.session_state["questions_dict"] = {}  # resetează întrebările la analiză nouă
        except FileNotFoundError as e:
            st.error(f"❌ Fișier negăsit: {e}")
        except ValueError as e:
            st.error(f"❌ Date invalide: {e}")
        except RuntimeError as e:
            st.error(f"❌ Eroare în pipeline: {e}")
        except Exception as e:
            st.error(f"❌ Eroare neașteptată: {e}")
        finally:
            for tmp_path in [jd_tmp, cv_tmp]:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

# ── Afișare rezultate (persistente prin session_state) ──
if st.session_state["result"] is not None:
    result = st.session_state["result"]
    df = result["matching_table"]

    st.success("✅ Analiză finalizată!")
    st.markdown("---")

    st.subheader("📈 Rezumat potrivire")
    render_summary(df)

    st.markdown("---")

    st.subheader("📊 Tabel de potrivire competențe")
    render_matching_table(df)

    st.markdown("---")

    with st.expander("📝 Texte parsate (debug)"):
        t1, t2 = st.tabs(["Job Description", "CV"])
        with t1:
            st.text_area("Text JD", result["jd_text"][:3000], height=200, disabled=True)
        with t2:
            st.text_area("Text CV", result["cv_text"][:3000], height=200, disabled=True)

    with st.expander("🔧 Competențe extrase (debug)"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Skills din JD:**")
            st.write(result["jd_skills"])
        with c2:
            st.markdown("**Skills din CV:**")
            st.write(result["cv_skills"])

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descarcă tabelul ca CSV",
        data=csv_data,
        file_name="matching_rezultate.csv",
        mime="text/csv",
    )

    # ── Generare întrebări ──
    st.markdown("---")
    st.subheader("💬 Generare întrebări de interviu")

    matched_df = df[df["match"] == "Da"]

    if matched_df.empty:
        st.warning("⚠️ Nu există competențe cu match pentru a genera întrebări.")
    else:
        st.info(f"Se vor genera întrebări pentru **{len(matched_df)} competențe** identificate în CV.")

        nr_intrebari = st.number_input(
            "Număr de întrebări per competență",
            min_value=1, max_value=10, value=3, step=1
        )

        generate_btn = st.button("🎯 Generează întrebări", type="primary")

        if generate_btn:
            try:
                from question_generator import generate_questions
                questions_dict = {}
                progress = st.progress(0)
                status = st.empty()

                for idx, (_, row) in enumerate(matched_df.iterrows()):
                    skill = row["jd_skill"]
                    priority = str(row.get("priority", "Unknown"))
                    status.markdown(f"⏳ Generez întrebări pentru **{skill}**...")
                    questions_dict[skill] = generate_questions(
                        skill, priority, int(nr_intrebari), result["jd_text"]
                    )
                    progress.progress((idx + 1) / len(matched_df))

                status.empty()
                progress.empty()
                st.session_state["questions_dict"] = questions_dict

            except RuntimeError as e:
                st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"❌ Eroare neașteptată: {e}")

        # ── Afișează întrebările generate ──
        if st.session_state["questions_dict"]:
            st.markdown("### 📋 Întrebări generate")
            for skill, questions in st.session_state["questions_dict"].items():
                row_data = df[df["jd_skill"] == skill]
                priority = row_data.iloc[0]["priority"] if not row_data.empty else ""
                badge = "🔴" if "must" in str(priority).lower() else "🔵"

                with st.expander(f"{badge} **{skill}** — {priority}", expanded=True):
                    for i, q in enumerate(questions, 1):
                        st.markdown(f"**{i}.** {q}")

else:
    # ── Pagina inițială ──
    st.markdown("### 👋 Cum funcționează")
    col1, col2, col3, col4 = st.columns(4)
    for col, step, title, desc in [
        (col1, "1️⃣", "Încarcă documentele",    "Adaugă JD-ul și CV-ul din sidebar (PDF, DOCX sau TXT)"),
        (col2, "2️⃣", "Setează pragul",          "Alege threshold-ul de similaritate (implicit 0.70)"),
        (col3, "3️⃣", "Apasă Analizează",        "Sistemul parsează, extrage competențe și calculează matching"),
        (col4, "4️⃣", "Generează întrebări",     "Alege numărul de întrebări și generează cu Ollama (llama3)"),
    ]:
        col.markdown(
            f"""<div class="metric-card" style="text-align:left; padding:1.5rem">
                <div style="font-size:1.5rem">{step}</div>
                <div style="font-weight:600; margin:0.5rem 0 0.3rem">{title}</div>
                <div style="font-size:0.85rem; color:#64748b">{desc}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#94a3b8; font-size:0.9rem'>"
        "AI Interviewer Assistant Tool · Proiect AI · Facultatea de Informatică · 2024–2025"
        "</div>",
        unsafe_allow_html=True,
    )
