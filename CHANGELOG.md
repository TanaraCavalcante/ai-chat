## [2026-04-29] - Spec e plano do frontend Laravel RAG v2

### Aggiunto
- Spec revisada do frontend Laravel (v2): multi-documento, Bootstrap 5, texto UI em italiano, suporte a `.xlsx`
- Plano de implementação completo com 6 tasks e código completo em cada step
- Sessão de brainstorming visual com mockups (sidebar, chat bubbles, input bar com contador "N fonti")

### Modificato
- `rag.py`: suporte a `.xlsx` via `UnstructuredExcelLoader` documentado na spec
- `.claude/settings.json`: permissões atualizadas (brainstorm server + git add)
- `main.py`: ajuste menor no texto do modo normal

---

## [2026-04-14] - Design spec frontend Laravel para chatbot RAG

### Aggiunto
- Spec de design para interface web Laravel do chatbot RAG (`docs/superpowers/specs/2026-04-14-rag-laravel-frontend-design.md`)
- Arquitetura híbrida: Flask API (porta 5000) + Laravel 12 frontend (Tabler UI + FontAwesome)
- Definição dos endpoints Python `/api/upload` e `/api/chat`
- Layout do chat com upload drag-and-drop, bolhas de mensagem e spinner de loading

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
