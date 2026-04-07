# RAG Chatbot — Design Spec
**Data:** 2026-04-07  
**Projeto:** Settimana 08 — chatbot com suporte a documentos  
**Objetivo:** Aprender RAG (Retrieval-Augmented Generation) adicionando suporte a documentos no chatbot existente

---

## Contexto

O `main.py` atual é um chatbot simples usando Groq API com histórico de conversa. O objetivo é adicionar a capacidade de carregar um documento (.txt, .pdf, .docx), transformá-lo em embeddings e fazer o chatbot responder perguntas baseadas no conteúdo do documento.

---

## Arquitetura

### Fase 1 — Indexação (roda uma vez ao carregar o documento)

```
Arquivo (.txt/.pdf/.docx)
     ↓
Leitura do documento         ← LangChain Loaders
     ↓
Divisão em chunks            ← RecursiveCharacterTextSplitter
     ↓
Criação dos embeddings       ← sentence-transformers (local, grátis)
     ↓
Armazenamento no FAISS       ← vector store em memória
```

### Fase 2 — Consulta (roda a cada pergunta)

```
Pergunta do utilizador
     ↓
Embedding da pergunta        ← mesmo modelo
     ↓
Busca dos 3 chunks mais similares ← similaridade coseno no FAISS
     ↓
Monta prompt com contexto    ← "Usa este trecho para responder:"
     ↓
Groq LLM gera resposta       ← llama-3.3-70b-versatile
     ↓
Resposta para o utilizador
```

---

## Experiência no terminal

```
=== Chatbot con RAG ===

Vuoi caricare un documento? (s/n): s
Percorso del documento: relatorio.pdf

[1/4] Lettura del documento...
      ✓ 12 pagine trovate

[2/4] Divisione in chunks...
      ✓ 47 chunks creati (dimensione: ~500 caratteri)

[3/4] Generazione degli embeddings...
      ✓ 47 vettori creati (modello: all-MiniLM-L6-v2)

[4/4] Indicizzazione in FAISS...
      ✓ Base di conoscenza pronta!

Ora puoi fare domande sul documento.
Digita 'esci' per uscire.

User: Qual è l'obiettivo del rapporto?

[RAG] Ricerca chunks rilevanti...
      → Chunk 3 (similarità: 0.89)
      → Chunk 7 (similarità: 0.74)
      → Chunk 12 (similarità: 0.71)

Bot: Il rapporto ha come obiettivo...
```

- Se o utilizador responder **n**, o chatbot funciona como o atual (sem RAG)
- O feedback verbose é educacional — mostra o RAG funcionando em tempo real

---

## Idioma

- O chatbot responde **sempre em italiano** (público-alvo: empresa italiana)
- O system prompt instrui o modelo a usar italiano e a basear-se no documento quando disponível

```python
system_prompt = """Sei un assistente utile. Rispondi sempre in italiano.
Quando viene fornito un contesto dal documento, basati su di esso 
per rispondere. Se la risposta non si trova nel documento, dillo 
chiaramente all'utente."""
```

---

## Componentes técnicos

| Biblioteca | Função |
|---|---|
| `langchain` | Orquestra o fluxo RAG |
| `langchain-community` | Loaders para PDF, DOCX, TXT |
| `sentence-transformers` | Embeddings locais (grátis, ~80MB) |
| `faiss-cpu` | Vector store para busca por similaridade |
| `pypdf` | Leitura de PDFs |
| `python-docx` | Leitura de DOCX |

**Modelo de embeddings:** `all-MiniLM-L6-v2` — leve, rápido, multilíngue

---

## Estrutura do código

```
main.py
  ├── carregar_documento(caminho)       → lê o arquivo pelo tipo
  ├── criar_vector_store(docs)          → chunks + embeddings + FAISS
  ├── buscar_contexto(store, pergunta)  → retorna 3 chunks relevantes
  ├── chat(mensagem, contexto)          → envia para Groq
  └── main()                           → loop principal com verbose output
```

---

## Dependências a instalar

```bash
pip install langchain langchain-community sentence-transformers faiss-cpu pypdf python-docx
```
