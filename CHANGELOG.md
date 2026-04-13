## [1.0.0] - 2026-04-13 - Implementazione RAG chatbot

### Aggiunto
- `rag.py`: modulo RAG con 3 funzioni pure e testabili
  - `carregar_documento`: carica .txt, .pdf, .docx tramite LangChain
  - `criar_vector_store`: chunking + embeddings (all-MiniLM-L6-v2) + FAISS
  - `buscar_contexto`: ricerca per similarità vettoriale
- `tests/test_rag.py`: 6 test (tutti passanti) per le 3 funzioni RAG
- Design spec RAG (`docs/superpowers/specs/2026-04-07-rag-chatbot-design.md`)
- Piano di implementazione RAG (`docs/superpowers/plans/2026-04-07-rag-chatbot.md`)

### Modificato
- `main.py`: integrazione RAG completa
  - documento passato via `sys.argv[1]` (es. `python main.py file.pdf`)
  - verbose output `[1/4]...[4/4]` durante l'indicizzazione
  - system prompt restrittivo: risponde solo dal documento
  - risposta in italiano se la risposta non è nel documento
  - modalità normale (senza documento) rimane disponibile
- `.claude/settings.json`: aggiunta directory progetto e `docs/superpowers`
- `main.py`: prompt input cambiato da "Tanara:" a "User:"
