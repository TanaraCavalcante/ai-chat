# AI-chat — Backend RAG

Chatbot che risponde esclusivamente in base al contenuto dei documenti caricati.

**Stack:** Flask · Groq (llama-3.3-70b) · FAISS · HuggingFace embeddings · LangChain

---

## Architettura del progetto

Questo progetto fa parte di un sistema composto da due repository separati che lavorano insieme:

| Repository | Ruolo |
|---|---|
| **AI-chat** *(questo)* | Backend Python — API Flask + pipeline RAG |
| **AI-chat-frontend** | Frontend Laravel — interfaccia web che consuma questa API |

Il frontend si connette al backend sulla porta `5001`. I due progetti possono essere avviati e sviluppati indipendentemente.

---

## Come funziona il RAG

1. **Upload** documento → testo estratto, diviso in chunk, convertito in vettori (embeddings), indicizzato in FAISS
2. **Domanda** → i top-6 chunk più simili vengono recuperati → inviati come contesto al LLM Groq
3. **Risposta** solo dal documento — se la risposta non c'è, il bot risponde: *"Non è presente nel documento una risposta alla domanda posta."*

Modello embeddings: `paraphrase-multilingual-MiniLM-L12-v2` (locale, supporta italiano e portoghese)

---

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crea il file `.env`:
```
groq_api_key=la_tua_chiave
```

---

## Modalità di utilizzo

### 1. API Flask (per il frontend)

```bash
python api.py
# server su http://localhost:5001
```

### 2. Terminale — modalità normale

Chatbot in italiano senza documento. Conversazione libera.

```bash
python main.py
```

### 3. Terminale — modalità RAG

Chatbot vincolato al contenuto del documento. Supporta `.txt`, `.pdf`, `.docx`, `.xlsx`.

```bash
python main.py relazione.pdf
```

Il documento viene indicizzato con feedback visivo `[1/4]...[4/4]` prima di iniziare la chat.
Per uscire: `esci`.

---

## Endpoint API

### `POST /api/upload`
Carica un documento e crea (o estende) una sessione.

**Form data:**
- `file` — `.txt`, `.pdf`, `.docx`, `.xlsx` (max 20 MB)
- `session_id` *(opzionale)* — sessione esistente a cui aggiungere il documento

**Risposta:**
```json
{
  "session_id": "uuid",
  "filename": "doc.pdf",
  "chunks": 42,
  "total_docs": 1,
  "total_chunks": 42
}
```

### `POST /api/chat`
Invia una domanda sulla sessione attiva.

**Body:**
```json
{ "session_id": "uuid", "pergunta": "Qual è la diagnosi?" }
```

**Risposta:**
```json
{
  "resposta": "La diagnosi è...",
  "chunks_usados": [
    { "texto": "...", "score": 0.31, "fonte": "doc.pdf" }
  ]
}
```

### `POST /api/clear`
Elimina una sessione dalla memoria.

**Body:**
```json
{ "session_id": "uuid" }
```

---

## Struttura del progetto

```
api.py          — API Flask, gestione sessioni, endpoint
rag.py          — pipeline RAG (carica → chunk → embed → cerca)
main.py         — modalità terminale (normale e RAG)
tests/          — suite pytest
requirements.txt
CHANGELOG.md
```
