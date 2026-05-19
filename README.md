# AI Interviewer Assistant - Member A Starter Files

This starter package contains the first deliverables for Member A:

- `data/job_descriptions/`: 16 synthetic IT job descriptions in `.txt` format
- `data/cvs/`: 16 synthetic CVs in `.txt` format
- `data/skills_dataset.csv`: 170+ labeled IT skills with aliases
- `src/parser.py`: parser for PDF, DOCX and TXT files
- `notebooks/01_data_analysis.ipynb`: data analysis notebook with basic stats and visualizations

Important: Most of the JD files are synthetic examples, not copied real job ads. 

## PyCharm setup

1. Open this folder as a PyCharm project.
2. Create a virtual environment with Python 3.11.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Test the parser:

```bash
python src/parser.py data/job_descriptions/python_developer_01.txt
```

5. Open `notebooks/01_data_analysis.ipynb` and run all cells from the repo root.
