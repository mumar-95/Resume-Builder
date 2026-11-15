# CareerForge Resume Builder

Build ATS-friendly resumes tailored to your role, technology priorities, and company experience.

## Features

1. Collect personal details, technologies, and project tenure
2. Capture companies one by one with project information
3. Optionally upload a Word/PDF reference resume to prefill details
4. Prioritize technologies and choose role focus:
   - Only Development
   - Development + Testing
   - Development + Production
   - Development + Testing + Production
5. Preview a professional ATS layout
6. Download as Word (`.docx`) or PDF

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

## Project layout

- `streamlit_app.py` — guided multi-step UI
- `utils/resume_builder.py` — role-aware ATS content generation
- `utils/resume_parser.py` — Word/PDF reference parsing
- `utils/exporters.py` — Word and PDF export
- `.streamlit/config.toml` — trust-focused professional theme
