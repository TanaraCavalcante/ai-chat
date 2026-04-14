# RAG Chatbot — Laravel Frontend Design

**Data:** 2026-04-14  
**Estado:** Aguardando revisão  
**URL local:** https://ai-wtech.test

---

## 1. Visão Geral

Interface web para o chatbot RAG existente (Python + Groq + FAISS). O utilizador carrega um documento no browser, faz perguntas em linguagem natural e recebe respostas baseadas no conteúdo do documento — tal como no terminal, mas com uma UI moderna.

O código Python existente (`rag.py`, `main.py`) **não é alterado**. Apenas se adiciona `api.py` como camada HTTP sobre o código existente.

---

## 2. Estrutura de Ficheiros

```
settimana 08/
├── rag.py              (existente — sem alterações)
├── main.py             (existente — sem alterações)
├── api.py              (NOVO — Flask, porta 5000)
├── requirements.txt    (NOVO — adiciona flask, flask-cors)
├── .env                (existente — sem alterações)
├── venv/               (existente)
└── laravel/            (NOVO — app Laravel 12)
    ├── public/
    ├── app/
    │   └── Http/
    │       └── Controllers/
    │           └── ChatController.php
    ├── resources/
    │   └── views/
    │       └── chat.blade.php
    ├── routes/
    │   └── web.php
    └── .env            (variável PYTHON_API_URL=http://127.0.0.1:5000)
```

**Valet:** após criar o projeto Laravel, redirecionar o link:
```bash
valet unlink ai-wtech        # desvincula a pasta raiz
cd laravel && valet link ai-wtech  # vincula a subpasta Laravel
```

---

## 3. Python API (api.py)

Framework: **Flask** (porta 5000, padrão Flask, sem configuração extra).  
Sem CORS necessário — o browser fala apenas com Laravel, e é o Laravel (server-side) que chama o Python. O Python nunca é chamado diretamente pelo browser.

### 3.1 Estado em memória

```python
sessions = {}  # { session_id: vector_store }
```

O vector store vive enquanto o processo Flask estiver ativo. Cada sessão browser tem o seu próprio store isolado.

### 3.2 Endpoints

#### `POST /api/upload`

Recebe um ficheiro multipart (`.txt`, `.pdf`, `.docx`).

**Fluxo interno:**
1. Guarda o ficheiro em `/tmp`
2. Chama `carregar_documento(caminho)`
3. Chama `criar_vector_store(docs)`
4. Gera um `session_id` (UUID4)
5. Guarda o store em `sessions[session_id]`
6. Apaga o ficheiro temporário

**Resposta de sucesso `200`:**
```json
{
  "session_id": "uuid4",
  "filename": "relatorio.pdf",
  "chunks": 42
}
```

**Resposta de erro `400`:**
```json
{ "error": "Formato '.xlsx' não suportado. Use .txt, .pdf ou .docx" }
```

---

#### `POST /api/chat`

Recebe JSON com `session_id` e `pergunta`.

**Request:**
```json
{
  "session_id": "uuid4",
  "pergunta": "Qual é a conclusão do relatório?"
}
```

**Fluxo interno:**
1. Valida que `session_id` existe em `sessions`
2. Chama `buscar_contexto(store, pergunta)`
3. Monta prompt com contexto (igual ao `construir_mensagem_com_contexto` do `main.py`)
4. Chama Groq API (`llama-3.3-70b-versatile`)
5. Devolve resposta

**Resposta de sucesso `200`:**
```json
{
  "resposta": "A conclusão do relatório indica que...",
  "chunks_usados": [
    { "texto": "...", "score": 0.42 },
    { "texto": "...", "score": 0.61 }
  ]
}
```

**Resposta de erro `404`:**
```json
{ "error": "Sessão não encontrada. Carregue um documento primeiro." }
```

---

## 4. Laravel Frontend

### 4.1 Stack

| Camada | Tecnologia |
|--------|-----------|
| Framework | Laravel 12 |
| UI Kit | Tabler UI (CDN) |
| Ícones | FontAwesome 6 (CDN) |
| HTTP client | Laravel `Http` facade (Guzzle) |
| JavaScript | Vanilla JS (sem build step) |

Sem npm build, sem Vite — apenas CDN para manter a instalação simples.

### 4.2 Rotas (`routes/web.php`)

| Método | Rota | Controller@método |
|--------|------|------------------|
| `GET` | `/` | `ChatController@index` |
| `POST` | `/upload` | `ChatController@upload` |
| `POST` | `/chat` | `ChatController@chat` |

### 4.3 Controller (`ChatController.php`)

**`index()`** — devolve a view `chat`.

**`upload(Request $request)`**
- Valida: ficheiro obrigatório, extensões `pdf,txt,docx`, máximo 20 MB
- Faz `Http::attach(...)->post(PYTHON_API_URL . '/api/upload')`
- Em caso de sucesso: guarda `session_id` na sessão Laravel, devolve JSON para o JS
- Em caso de erro: devolve mensagem de erro ao JS

**`chat(Request $request)`**
- Valida: `pergunta` obrigatória, `session_id` presente na sessão Laravel
- Faz `Http::post(PYTHON_API_URL . '/api/chat', [...])`
- Devolve JSON `{resposta, chunks_usados}` ao JS

### 4.4 View (`chat.blade.php`)

Layout Tabler com 3 zonas verticais:

```
┌─────────────────────────────────────┐
│  HEADER — "AI Chat" + estado doc    │
├─────────────────────────────────────┤
│  UPLOAD ZONE                        │
│  [drag & drop / clique para abrir]  │
│  (colapsa após upload bem-sucedido) │
├─────────────────────────────────────┤
│                                     │
│  CHAT AREA (scroll)                 │
│  ┌─────────────────────────────┐   │
│  │ 💬 Mensagem do utilizador   │   │
│  └─────────────────────────────┘   │
│        ┌─────────────────────────┐ │
│        │ 🤖 Resposta do bot      │ │
│        └─────────────────────────┘ │
│                                     │
├─────────────────────────────────────┤
│  [  Escreva a sua pergunta...  ] ▶  │
└─────────────────────────────────────┘
```

**Estados do header:**
- Sem documento: ícone cinza + "Carregue um documento para começar"
- Com documento: ícone verde + nome do ficheiro + nº de chunks

**Upload zone:**
- Drag-and-drop com highlight ao arrastar
- Barra de progresso durante upload + indexação
- Colapsa com animação após sucesso, mostrando badge com nome do ficheiro
- Botão "Trocar documento" para reabrir a zona

**Chat area:**
- Bolhas: utilizador à direita (azul Tabler), bot à esquerda (cinza claro)
- Avatar bot: ícone FontAwesome `fa-robot`
- Spinner animado enquanto aguarda resposta do Groq
- Auto-scroll para a última mensagem
- Input desabilitado até um documento estar carregado

---

## 5. Tratamento de Erros

| Cenário | Comportamento UI |
|---------|-----------------|
| Ficheiro com formato inválido | Toast de erro vermelho (Tabler alert) |
| Ficheiro > 20 MB | Validação Laravel, toast antes do upload |
| Python API offline | Toast "Serviço indisponível. Inicie o api.py." |
| Sessão expirada | Toast + reaparece zona de upload |
| Groq API error | Mensagem de erro na bolha do bot |

---

## 6. Configuração e Arranque

O utilizador precisa de 2 processos a correr em paralelo:

```bash
# Terminal 1 — Python API
source venv/bin/activate
python api.py

# Terminal 2 — já gerido pelo Valet (automático)
# https://ai-wtech.test já está disponível
```

A `PYTHON_API_URL` fica em `laravel/.env`:
```
PYTHON_API_URL=http://127.0.0.1:5000
```

---

## 7. Fora de Âmbito

- Autenticação / multi-utilizador
- Persistência de sessões entre reinícios do servidor Python
- Histórico de conversas guardado em base de dados
- Streaming de respostas (resposta completa antes de mostrar)
- Suporte a múltiplos documentos na mesma sessão
