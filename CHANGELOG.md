## [2026-05-08] - Documentação técnica e suporte .docx

### Aggiunto
- `docs/apresentacao.md`: documentação técnica completa em português — arquitetura, pipeline RAG, integração Python ↔ Laravel, testes, glossário
- `docx2txt`: dependência instalada para suporte completo a arquivos `.docx`

---

## [2026-05-04] - Aggiunto README

### Aggiunto
- `README.md`: documentazione in italiano — architettura, setup, modalità terminale (normale e RAG), endpoint API

---

## [2026-05-04] - Melhoria RAG: extração PDF e embeddings multilíngues

### Modificato
- `rag.py`: substituído `PyPDFLoader` por `pdfplumber` com `extract_text(layout=True)` — preserva layout de laudos médicos
- `rag.py`: embedding trocado de `all-MiniLM-L6-v2` para `paraphrase-multilingual-MiniLM-L12-v2` — suporte a italiano/português
- `rag.py`: `chunk_size` 500→1200, `chunk_overlap` 50→150, `k` 3→6 — mais contexto por chunk, mais chunks recuperados
- `api.py`: porta corrigida 5000→5001, `debug=False` para compatibilidade com execução em background

---

## [2026-04-29] - Reorganização: AI-chat separado de AI-chat-frontend

### Modificato
- Movido `laravel/` para projeto separado `AI-chat-frontend/`
- Movidos docs do frontend Laravel (`plans/2026-04-29`, `specs/2026-04-14`, `specs/2026-04-29`) para `AI-chat-frontend/`
- Movido `.superpowers/` (brainstorm de layout/UI) para `AI-chat-frontend/`
- `AI-chat` passa a conter somente o backend Python (Flask API + RAG)

---

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
