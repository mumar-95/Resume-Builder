# CareerForge Resume Builder

Build ATS-friendly resumes tailored to your role, technology priorities, and company experience.

## Features

1. Choose from 20 dynamic resume templates (with role-based suggestions)
2. Collect personal details, custom job title, years of experience, and technologies
3. Capture companies one by one with project information
4. Prioritize technologies and choose role focus:
   - Only Development
   - Development + Testing
   - Development + Production
   - Development + Testing + Production
5. Jump between sections from the left sidebar at any time
6. Preview a professional ATS layout
7. Download as Word (`.docx`) or PDF

## Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Prefer running Streamlit from the project `.venv` so PDF export (`reportlab`) is available.

Open the URL shown in the terminal (usually http://localhost:8501).

## Project layout

- `streamlit_app.py` — guided multi-step UI
- `utils/resume_builder.py` — role-aware ATS content generation
- `utils/templates.py` — resume template gallery and examples
- `utils/exporters.py` — Word and PDF export
- `.streamlit/config.toml` — trust-focused professional theme
