## [2026-09-07] - Setup ambiente locale e correzione dipendenze

### Aggiunto
- `.env.example`: template per la configurazione della `groq_api_key`
- `README.md`: sezione setup separata per macOS/Linux e Windows (PowerShell), istruzioni per avviare e fermare l'API Flask
- `requirements.txt`: dipendenze mancanti aggiunte — `groq`, `python-dotenv`, `pdfplumber`, `docx2txt`, `langchain-core`, `langchain-community`, `langchain-text-splitters`, `langchain-huggingface`, `sentence-transformers`, `faiss-cpu`, `pytest`

### Modificato
- `.gitignore`: aggiunti `venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `.pytest_cache/`, `*.egg-info/`, `.vscode/`, `.idea/`
- Rimossi dal tracking git i file `.pyc` di `__pycache__/` e `tests/__pycache__/` che erano stati committati per errore
