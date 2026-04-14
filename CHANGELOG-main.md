## [2026-04-14] - Design spec frontend Laravel para chatbot RAG

### Aggiunto
- Spec de design para interface web Laravel do chatbot RAG (`docs/superpowers/specs/2026-04-14-rag-laravel-frontend-design.md`)
- Arquitetura híbrida: Flask API (porta 5000) + Laravel 12 frontend (Tabler UI + FontAwesome)
- Definição dos endpoints Python `/api/upload` e `/api/chat`
- Layout do chat com upload drag-and-drop, bolhas de mensagem e spinner de loading

## [2026-04-07] - RAG chatbot design e piano di implementazione

### Aggiunto
- Design spec per chatbot con RAG (`docs/superpowers/specs/2026-04-07-rag-chatbot-design.md`)
- Piano di implementazione RAG (`docs/superpowers/plans/2026-04-07-rag-chatbot.md`)
- Supporto a documenti .txt, .pdf, .docx tramite LangChain
- Embeddings locali con sentence-transformers (all-MiniLM-L6-v2)
- Vector store FAISS per ricerca per similarità
- Verbose output nel terminale per mostrare il processo RAG in tempo reale
- System prompt in italiano per il chatbot aziendale

### Modificato
- `main.py`: prompt input cambiato da "Tanara:" a "User:"
- `.claude/settings.json`: aggiunta cartella `docs/superpowers` alle directory aggiuntive
