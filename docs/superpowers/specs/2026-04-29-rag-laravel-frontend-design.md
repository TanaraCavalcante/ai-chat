# RAG Chatbot — Laravel Frontend Design (v2)

**Data:** 2026-04-29
**Substitui:** `2026-04-14-rag-laravel-frontend-design.md`
**Estado:** Aprovado
**URL local:** https://ai-wtech.test

---

## 1. Visão Geral

Interface web para o chatbot RAG existente (Python + Groq + FAISS). O utilizador carrega um ou mais documentos no browser, faz perguntas em linguagem natural e recebe respostas baseadas no conteúdo dos documentos.

O `main.py` existente **não é alterado**. O `rag.py` recebe uma alteração mínima: suporte a `.xlsx` via `UnstructuredExcelLoader`. Adiciona-se `api.py` como camada HTTP sobre o código existente.

A UI está inteiramente em **italiano** (público-alvo italiano). O código-fonte (variáveis, comentários) permanece em portugues/italiano.

---

## 2. Por que é necessário o `api.py`

Laravel é PHP. PHP não pode importar nem executar funções Python directamente. O `api.py` (Flask) transforma as funções de `rag.py` em endpoints HTTP REST que o Laravel chama via `Http` facade — exactamente como chamaria qualquer API externa. O browser nunca acede directamente à porta 5000; só o Laravel (server-side) o faz.

```
Browser → Laravel :443 (ai-wtech.test) → api.py Flask :5000 → rag.py → Groq API
```

---

## 3. Estrutura de Ficheiros

```
settimana 08/
├── rag.py              (existente — sem alterações)
├── main.py             (existente — sem alterações)
├── api.py              (NOVO — Flask, porta 5000)
├── requirements.txt    (NOVO — adiciona flask, unstructured[xlsx])
├── .env                (existente — sem alterações)
├── venv/               (existente)
└── laravel/            (NOVO — app Laravel 12)
    ├── public/
    │   └── images/
    │       └── logo.png        (placeholder — colocar logo W-Tech aqui)
    ├── app/Http/Controllers/
    │   └── ChatController.php
    ├── resources/views/
    │   └── chat.blade.php
    ├── routes/
    │   └── web.php
    └── .env            (PYTHON_API_URL=http://127.0.0.1:5000)
```

**Valet:** após criar o projecto Laravel:
```bash
valet unlink ai-wtech        # desvincula a pasta raiz (se existir)
cd laravel && valet link ai-wtech
```

---

## 4. Alteração em `rag.py` — suporte a Excel

A função `carregar_documento` recebe um novo `elif` para `.xlsx`, usando `UnstructuredExcelLoader` do LangChain. Cada folha (sheet) do ficheiro Excel é convertida num `Document` separado.

```python
# Adicionar no topo de rag.py:
from langchain_community.document_loaders import UnstructuredExcelLoader

# Adicionar dentro de carregar_documento(), após o elif .docx:
elif extensao == ".xlsx":
    loader = UnstructuredExcelLoader(caminho)
```

**Dependência nova:** `unstructured[xlsx]` (instalar via `pip install "unstructured[xlsx]"`).

O comportamento do chunking e embedding não muda — o Excel passa pelo mesmo pipeline do `criar_vector_store`.

---

## 5. Python API (`api.py`)  <!-- era §4 -->

Framework: **Flask** (porta 5000, padrão Flask).
Sem CORS — o browser nunca chama o Flask directamente.

### 4.1 Estado em memória

```python
sessions = {}
# { session_id: {"store": FAISS, "docs": [{"name": str, "chunks": int}]} }
```

O vector store e a lista de documentos vivem enquanto o processo Flask estiver activo. Cada sessão browser tem o seu próprio store isolado. Documentos adicionados ao mesmo `session_id` são **acumulados** no mesmo store (chunks de todos os documentos indexados juntos).

### 4.2 Endpoints

#### `POST /api/upload`

Recebe um ficheiro multipart (`.txt`, `.pdf`, `.docx`, `.xlsx`) e um `session_id` opcional.

**Fluxo interno:**
1. Guarda o ficheiro em `/tmp`
2. Chama `carregar_documento(caminho)`
3. Chama `criar_vector_store(docs)` para obter os novos chunks
4. Se `session_id` já existe em `sessions`: faz `merge_from` para adicionar ao store existente
5. Se não existe: cria nova entrada com UUID4
6. Actualiza a lista `docs` da sessão com nome + nº de chunks do novo ficheiro
7. Apaga o ficheiro temporário

**Resposta `200`:**
```json
{
  "session_id": "uuid4",
  "filename": "relatorio.pdf",
  "chunks": 42,
  "total_docs": 2,
  "total_chunks": 70
}
```

**Resposta `400`:**
```json
{ "error": "Formato '.csv' non supportato. Usa .txt, .pdf, .docx o .xlsx" }
```

**Resposta `413`:**
```json
{ "error": "File troppo grande. Massimo 20 MB." }
```

---

#### `POST /api/chat`

```json
// Request
{ "session_id": "uuid4", "pergunta": "Qual è la conclusione?" }

// Resposta 200
{
  "resposta": "La conclusione indica che…",
  "chunks_usados": [
    { "texto": "…", "score": 0.42, "fonte": "relatorio.pdf" },
    { "texto": "…", "score": 0.61, "fonte": "contratto.docx" }
  ]
}

// Resposta 404
{ "error": "Sessione non trovata. Carica un documento prima." }
```

**Fluxo interno:**
1. Valida `session_id`
2. Chama `buscar_contexto(store, pergunta)`
3. Monta prompt com contexto (igual ao `main.py`)
4. Chama Groq (`llama-3.3-70b-versatile`)
5. Devolve resposta + chunks com ficheiro de origem

---

#### `POST /api/clear`

```json
// Request
{ "session_id": "uuid4" }

// Resposta 200
{ "ok": true }
```

Remove a sessão de `sessions`. Chamado pelo botão "Ricomincia".

---

## 6. Laravel Frontend

### 5.1 Stack

| Camada | Tecnologia |
|--------|-----------|
| Framework | Laravel 12 |
| CSS | Bootstrap 5 (CDN) |
| UI components | Tabler UI (CDN) — apenas se Bootstrap não chegar |
| Ícones | FontAwesome 6 (CDN) |
| HTTP client | Laravel `Http` facade (Guzzle) |
| JavaScript | Vanilla JS (sem build step) |

### 5.2 Rotas (`routes/web.php`)

| Método | Rota | Controller@método |
|--------|------|------------------|
| `GET` | `/` | `ChatController@index` |
| `POST` | `/upload` | `ChatController@upload` |
| `POST` | `/chat` | `ChatController@chat` |
| `POST` | `/clear` | `ChatController@clear` |

### 5.3 Controller (`ChatController.php`)

**`index()`** — devolve a view `chat`.

**`upload(Request $request)`**
- Valida: ficheiro obrigatório, extensões `pdf,txt,docx,xlsx`, máximo 20 MB
- Recupera `session_id` da sessão Laravel (ou `null` se primeira vez)
- Faz `Http::attach(...)->post(PYTHON_API_URL . '/api/upload', ['session_id' => ...])`
- Sucesso: guarda `session_id` na sessão Laravel, devolve JSON ao JS
- Erro: devolve mensagem de erro ao JS

**`chat(Request $request)`**
- Valida: `pergunta` obrigatória, `session_id` presente na sessão Laravel
- Faz `Http::post(PYTHON_API_URL . '/api/chat', [...])`
- Devolve JSON `{resposta, chunks_usados}` ao JS

**`clear(Request $request)`**
- Lê `session_id` da sessão Laravel
- Faz `Http::post(PYTHON_API_URL . '/api/clear', [...])`
- Limpa `session_id` da sessão Laravel
- Devolve `{ok: true}` ao JS

### 5.4 View (`chat.blade.php`)

#### Navbar (`#1a2f6e`)

```
[ <img src="{{ asset('images/logo.png') }}" alt="W-Tech"> ]  W-Tech AI Chat
                                                              Assistente documentale
```

A logo é carregada de `public/images/logo.png`. O ficheiro não existe no repositório — colocar manualmente após o setup.

#### Sidebar (180px, fixa)

Três estados:

**Estado 1 — Sem documentos:**
- Badge vermelho `● Nessun documento`
- Zona upload dashed: ícone `fa-paperclip` + "Carica documento" + "PDF · TXT · DOCX · XLSX · max 20 MB"

**Estado 2 — Indexando (durante upload):**
- Badge amarelo `⏳ Indicizzazione…`
- 4 steps inline com ícone de check (FontAwesome `fa-check`) para concluídos e spinner para o actual:
  1. Lettura file
  2. Divisione in chunk
  3. Generazione embeddings
  4. Indicizzazione FAISS
- Os steps são **animados client-side com timers** (JS `setTimeout`) — o Flask não envia progresso real, só responde quando termina. Sequência sugerida: step 1 após 0.3s, step 2 após 0.8s, step 3 após 1.5s, step 4 quando a resposta HTTP chegar.
- Nome do ficheiro em processamento com barra de progresso indeterminada (Bootstrap `progress-bar-animated`)

**Estado 3 — Com documentos:**
- Badge verde `● N fonti attive`
- Lista de documentos: cada item mostra ícone `fa-file` + nome + "N chunk"
- Botão "Aggiungi fonte" (dashed, sempre visível) — máximo 5 documentos por sessão; aceita PDF · TXT · DOCX · XLSX
- Botão "Ricomincia" (vermelho claro) — chama `/clear`, apaga sessão e reset da UI

#### Chat area

**Estado vazio:** ícone `fa-file-alt` + "Carica un documento per iniziare"

**Bolhas de mensagem:**
- Utilizador: direita, fundo `#1a2f6e`, texto branco, border-radius `14px 14px 2px 14px`
- Bot: esquerda, fundo branco, border `1px solid #e2e8f0`, border-radius `14px 14px 14px 2px`
- Avatar bot: `<img src="{{ asset('images/logo.png') }}">` num círculo `#1a2f6e` com border `#3a5cc5` — exibe o símbolo da logo W-Tech

**Estado aguardando resposta:**
```
[avatar]  ● ●  elaborazione in corso…  (itálico, cinza)
```

#### Input bar (rodapé, sempre visível)

Pill shape (`border-radius: 24px`), fundo branco, border Bootstrap:

```
[  Inizia a digitare…          ]  [ N fonti ]  [ → ]
```

- Placeholder desabilitado: "Carica un documento per iniziare…"
- Contador "N fonti" actualiza em tempo real conforme docs são adicionados
- Botão `→` (FontAwesome `fa-arrow-right`): activo `#1a2f6e`, desabilitado cinza
- Input desabilitado até existir pelo menos 1 documento carregado

---

## 7. Tratamento de Erros

| Cenário | Comportamento UI |
|---------|-----------------|
| Formato inválido | Toast Bootstrap `alert-danger`: "Formato non supportato…" |
| Ficheiro > 20 MB | Validação Laravel antes do upload, toast |
| Máximo 5 docs atingido | Toast: "Limite di 5 documenti per sessione raggiunto" |
| Python API offline | Toast: "Servizio non disponibile. Avvia api.py." |
| Sessão expirada (Flask reiniciado) | Toast + reset UI para estado sem documentos |
| Erro Groq API | Mensagem de erro na bolha do bot |

---

## 8. Configuração e Arranque

```bash
# Terminal 1 — Python API
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
source venv/bin/activate
python api.py

# Terminal 2 — Valet gere o Laravel automaticamente
# https://ai-wtech.test já disponível após valet link
```

`laravel/.env`:
```
PYTHON_API_URL=http://127.0.0.1:5000
```

---

## 9. Fora de Âmbito

- Autenticação / multi-utilizador
- Persistência de sessões entre reinícios do Flask
- Histórico de conversas em base de dados
- Streaming de respostas
- Remoção individual de documentos (apenas "Ricomincia" limpa tudo)
- Modo chat livre sem documento
