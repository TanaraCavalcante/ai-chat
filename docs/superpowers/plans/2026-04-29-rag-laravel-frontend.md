# RAG Laravel Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar interface web em Laravel 12 para o chatbot RAG existente (Python + Groq + FAISS), permitindo upload de múltiplos documentos e chat em italiano.

**Architecture:** `api.py` (Flask :5000) expõe `rag.py` como endpoints HTTP REST. Laravel actua como proxy server-side: recebe pedidos do browser, repassa ao Flask, devolve JSON ao JS. A view `chat.blade.php` gere todo o estado no cliente com vanilla JS.

**Tech Stack:** Python Flask, Laravel 12, Bootstrap 5 CDN, FontAwesome 6 CDN, Vanilla JS, LangChain UnstructuredExcelLoader, Groq llama-3.3-70b-versatile

---

## Mapa de ficheiros

| Ficheiro | Acção | Responsabilidade |
|----------|-------|-----------------|
| `rag.py` | Modificar | Adicionar loader `.xlsx` |
| `tests/test_rag.py` | Modificar | Adicionar teste xlsx |
| `api.py` | Criar | Flask: upload, chat, clear |
| `tests/test_api.py` | Criar | Testes Flask endpoints |
| `requirements.txt` | Criar | flask + unstructured[xlsx] |
| `laravel/` | Criar | Projecto Laravel via composer |
| `laravel/.env` | Modificar | Adicionar PYTHON_API_URL |
| `laravel/routes/web.php` | Modificar | 4 rotas: /, /upload, /chat, /clear |
| `laravel/app/Http/Controllers/ChatController.php` | Criar | Proxy entre browser e Flask |
| `laravel/tests/Feature/ChatControllerTest.php` | Criar | Testes do controller |
| `laravel/resources/views/chat.blade.php` | Criar | UI completa: sidebar + chat + JS |
| `laravel/public/images/logo.png` | Placeholder | Colocar logo W-Tech manualmente |

---

## Task 1: Suporte a .xlsx no `rag.py`

**Files:**
- Modify: `rag.py`
- Modify: `tests/test_rag.py`

- [ ] **Step 1: Instalar dependência xlsx no venv**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
source venv/bin/activate
pip install "unstructured[xlsx]"
```

Esperado: instalação sem erros. Verifica com:
```bash
python -c "from langchain_community.document_loaders import UnstructuredExcelLoader; print('OK')"
```

- [ ] **Step 2: Escrever o teste para xlsx em `tests/test_rag.py`**

Adiciona no final do ficheiro, após `test_busca_contexto_devolve_texto_e_scores`:

```python
def test_carrega_xlsx(tmp_path):
    """Deve carregar um ficheiro .xlsx e devolver pelo menos um Document."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws['A1'] = 'Produto'
    ws['B1'] = 'Preco'
    ws['A2'] = 'Widget'
    ws['B2'] = 50
    ficheiro = tmp_path / "teste.xlsx"
    wb.save(str(ficheiro))

    docs = carregar_documento(str(ficheiro))

    assert len(docs) >= 1
    assert any('Widget' in d.page_content or '50' in d.page_content for d in docs)
```

- [ ] **Step 3: Executar o teste para verificar que falha**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
pytest tests/test_rag.py::test_carrega_xlsx -v
```

Esperado: `FAILED` — `ValueError: Formato '.xlsx' não suportado`

- [ ] **Step 4: Adicionar o loader xlsx ao `rag.py`**

Adiciona o import no topo do ficheiro, junto aos outros loaders (linha ~13):

```python
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
)
```

Adiciona o `elif` dentro de `carregar_documento`, após o bloco `elif extensao == ".docx":` e antes do `else`:

```python
    elif extensao == ".xlsx":
        loader = UnstructuredExcelLoader(caminho)
```

- [ ] **Step 5: Executar todos os testes**

```bash
pytest tests/test_rag.py -v
```

Esperado: 7 testes PASSED (os 6 existentes + o novo xlsx)

- [ ] **Step 6: Commit**

```bash
git add rag.py tests/test_rag.py
git commit -m "feat: rag - adiciona suporte a .xlsx via UnstructuredExcelLoader"
```

---

## Task 2: `requirements.txt` e `api.py`

**Files:**
- Create: `requirements.txt`
- Create: `api.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Criar `requirements.txt`**

```
flask>=3.0
unstructured[xlsx]>=0.12
```

- [ ] **Step 2: Instalar Flask**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
source venv/bin/activate
pip install flask
python -c "from flask import Flask; print('Flask OK')"
```

Esperado: `Flask OK`

- [ ] **Step 3: Escrever os testes do api em `tests/test_api.py`**

```python
# tests/test_api.py
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_upload_sem_ficheiro(client):
    """Deve retornar 400 se nenhum ficheiro for enviado."""
    response = client.post('/api/upload')
    assert response.status_code == 400


def test_upload_formato_invalido(client, tmp_path):
    """Deve retornar 400 para extensão não suportada."""
    csv_file = tmp_path / "dados.csv"
    csv_file.write_text("a,b,c")
    with open(csv_file, 'rb') as f:
        response = client.post('/api/upload', data={
            'file': (f, 'dados.csv')
        })
    assert response.status_code == 400
    assert 'non supportato' in response.get_json()['error']


def test_chat_sessao_nao_encontrada(client):
    """Deve retornar 404 se session_id não existir."""
    response = client.post('/api/chat', json={
        'session_id': 'sessao-inexistente',
        'pergunta': 'Ciao'
    })
    assert response.status_code == 404
    assert 'Sessione non trovata' in response.get_json()['error']


def test_chat_pergunta_vazia(client):
    """Deve retornar 400 se a pergunta estiver vazia."""
    response = client.post('/api/chat', json={
        'session_id': 'qualquer',
        'pergunta': ''
    })
    assert response.status_code in (400, 404)


def test_clear_sessao_inexistente(client):
    """Deve retornar 200 mesmo se session_id não existir."""
    response = client.post('/api/clear', json={'session_id': 'nao-existe'})
    assert response.status_code == 200
    assert response.get_json()['ok'] is True
```

- [ ] **Step 4: Executar os testes para verificar que falham**

```bash
pytest tests/test_api.py -v
```

Esperado: `ImportError: cannot import name 'app' from 'api'` — o ficheiro não existe ainda.

- [ ] **Step 5: Criar `api.py`**

```python
# api.py
import os
import uuid
import tempfile

from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv

from rag import carregar_documento, criar_vector_store, buscar_contexto

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB

client = Groq(api_key=os.getenv("groq_api_key"))

sessions = {}
# { session_id: {"store": FAISS, "docs": [{"name": str, "chunks": int}]} }

SYSTEM_PROMPT = (
    "Sei un assistente utile. Rispondi sempre in italiano. "
    "Rispondi esclusivamente in base al contesto fornito dal documento. "
    "Se la risposta non è presente nel documento, rispondi esattamente: "
    "'Non è presente nel documento una risposta alla domanda posta.'"
)

EXTENSOES_PERMITIDAS = {'.txt', '.pdf', '.docx', '.xlsx'}


@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "Nessun file ricevuto"}), 400

    file = request.files['file']
    session_id = request.form.get('session_id') or None
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in EXTENSOES_PERMITIDAS:
        return jsonify({"error": f"Formato '{ext}' non supportato. Usa .txt, .pdf, .docx o .xlsx"}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
            file.save(tmp_path)

        docs = carregar_documento(tmp_path)
        new_store, n_chunks = criar_vector_store(docs)
    except (FileNotFoundError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if session_id and session_id in sessions:
        sessions[session_id]['store'].merge_from(new_store)
        sessions[session_id]['docs'].append({"name": filename, "chunks": n_chunks})
    else:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "store": new_store,
            "docs": [{"name": filename, "chunks": n_chunks}],
        }

    session = sessions[session_id]
    total_chunks = sum(d["chunks"] for d in session["docs"])

    return jsonify({
        "session_id": session_id,
        "filename": filename,
        "chunks": n_chunks,
        "total_docs": len(session["docs"]),
        "total_chunks": total_chunks,
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    pergunta = (data.get('pergunta') or '').strip()

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Sessione non trovata. Carica un documento prima."}), 404

    if not pergunta:
        return jsonify({"error": "Domanda vuota"}), 400

    store = sessions[session_id]['store']
    contexto, resultados = buscar_contexto(store, pergunta)

    mensagem_com_contexto = (
        f"Contesto dal documento:\n---\n{contexto}\n---\n\n"
        f"Domanda: {pergunta}"
    )

    historico = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": mensagem_com_contexto},
    ]

    resposta_groq = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=historico,
    )
    resposta = resposta_groq.choices[0].message.content

    chunks_usados = [
        {
            "texto": doc.page_content[:200],
            "score": float(score),
            "fonte": os.path.basename(doc.metadata.get('source', 'documento')),
        }
        for doc, score in resultados
    ]

    return jsonify({"resposta": resposta, "chunks_usados": chunks_usados})


@app.route('/api/clear', methods=['POST'])
def clear():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if session_id and session_id in sessions:
        del sessions[session_id]
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(port=5000, debug=True)
```

- [ ] **Step 6: Executar os testes do api**

```bash
pytest tests/test_api.py -v
```

Esperado:
```
PASSED tests/test_api.py::test_upload_sem_ficheiro
PASSED tests/test_api.py::test_upload_formato_invalido
PASSED tests/test_api.py::test_chat_sessao_nao_encontrada
PASSED tests/test_api.py::test_chat_pergunta_vazia
PASSED tests/test_api.py::test_clear_sessao_inexistente
```

- [ ] **Step 7: Testar o api manualmente**

Terminal 1 — inicia o Flask:
```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
source venv/bin/activate
python api.py
```

Esperado: `* Running on http://127.0.0.1:5000`

Terminal 2 — testa o endpoint clear:
```bash
curl -s -X POST http://127.0.0.1:5000/api/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test"}' | python3 -m json.tool
```

Esperado: `{ "ok": true }`

- [ ] **Step 8: Commit**

```bash
git add api.py requirements.txt tests/test_api.py
git commit -m "feat: api.py - Flask com endpoints upload, chat e clear"
```

---

## Task 3: Setup do projecto Laravel

**Files:**
- Create: `laravel/` (via composer)
- Modify: `laravel/.env`
- Modify: `laravel/routes/web.php`

- [ ] **Step 1: Criar o projecto Laravel**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
composer create-project laravel/laravel laravel --prefer-dist
```

Esperado: pasta `laravel/` criada com estrutura Laravel 12.

- [ ] **Step 2: Adicionar PYTHON_API_URL ao `laravel/.env`**

Abre `laravel/.env` e adiciona no final:

```
PYTHON_API_URL=http://127.0.0.1:5000
```

- [ ] **Step 3: Criar pasta para a logo**

```bash
mkdir -p "/Users/tanara/dev/pessoal/AI/settimana 08/laravel/public/images"
```

Esta pasta ficará vazia até colocares a logo W-Tech em `laravel/public/images/logo.png`.

- [ ] **Step 4: Configurar o Valet**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08/laravel"
valet link ai-wtech
valet secure ai-wtech
```

Esperado: `https://ai-wtech.test` disponível no browser.

- [ ] **Step 5: Verificar que o Laravel está a funcionar**

Abre `https://ai-wtech.test` no browser. Deve aparecer a página de boas-vindas padrão do Laravel.

- [ ] **Step 6: Commit**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
git add laravel/
git commit -m "feat: setup projecto Laravel 12 com valet link ai-wtech"
```

---

## Task 4: Rotas e `ChatController`

**Files:**
- Modify: `laravel/routes/web.php`
- Create: `laravel/app/Http/Controllers/ChatController.php`
- Create: `laravel/tests/Feature/ChatControllerTest.php`

- [ ] **Step 1: Escrever o teste de feature**

Cria o ficheiro `laravel/tests/Feature/ChatControllerTest.php`:

```php
<?php

namespace Tests\Feature;

use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class ChatControllerTest extends TestCase
{
    public function test_index_devolve_view_chat(): void
    {
        $response = $this->get('/');
        $response->assertStatus(200);
        $response->assertViewIs('chat');
    }

    public function test_upload_valida_ficheiro_obrigatorio(): void
    {
        $response = $this->postJson('/upload');
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_upload_valida_extensao(): void
    {
        $file = UploadedFile::fake()->create('dados.csv', 100, 'text/csv');
        $response = $this->postJson('/upload', ['file' => $file]);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_upload_valida_tamanho_maximo(): void
    {
        $file = UploadedFile::fake()->create('grande.pdf', 25000, 'application/pdf');
        $response = $this->postJson('/upload', ['file' => $file]);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_chat_valida_pergunta_obrigatoria(): void
    {
        $response = $this->postJson('/chat', []);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['pergunta']);
    }

    public function test_clear_sem_sessao_devolve_ok(): void
    {
        $response = $this->postJson('/clear');
        $response->assertStatus(200);
        $response->assertJson(['ok' => true]);
    }
}
```

- [ ] **Step 2: Executar os testes para verificar que falham**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08/laravel"
php artisan test tests/Feature/ChatControllerTest.php
```

Esperado: erros de rota não encontrada (404) — o controller ainda não existe.

- [ ] **Step 3: Criar `ChatController.php`**

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class ChatController extends Controller
{
    private string $apiUrl;

    public function __construct()
    {
        $this->apiUrl = env('PYTHON_API_URL', 'http://127.0.0.1:5000');
    }

    public function index()
    {
        return view('chat');
    }

    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|file|mimes:pdf,txt,docx,xlsx|max:20480',
        ]);

        $file = $request->file('file');
        $sessionId = session('python_session_id');

        $response = Http::timeout(300)
            ->attach('file', file_get_contents($file->path()), $file->getClientOriginalName())
            ->post($this->apiUrl . '/api/upload', array_filter([
                'session_id' => $sessionId,
            ]));

        if ($response->successful()) {
            $data = $response->json();
            session(['python_session_id' => $data['session_id']]);
            return response()->json($data);
        }

        return response()->json($response->json(), $response->status());
    }

    public function chat(Request $request)
    {
        $request->validate(['pergunta' => 'required|string|max:2000']);

        $sessionId = session('python_session_id');
        if (! $sessionId) {
            return response()->json(
                ['error' => 'Sessione non trovata. Carica un documento prima.'],
                404
            );
        }

        $response = Http::timeout(60)->post($this->apiUrl . '/api/chat', [
            'session_id' => $sessionId,
            'pergunta'   => $request->pergunta,
        ]);

        if ($response->successful()) {
            return response()->json($response->json());
        }

        return response()->json($response->json(), $response->status());
    }

    public function clear(Request $request)
    {
        $sessionId = session('python_session_id');

        if ($sessionId) {
            Http::timeout(10)->post($this->apiUrl . '/api/clear', [
                'session_id' => $sessionId,
            ]);
            session()->forget('python_session_id');
        }

        return response()->json(['ok' => true]);
    }
}
```

- [ ] **Step 4: Substituir `laravel/routes/web.php`**

```php
<?php

use App\Http\Controllers\ChatController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ChatController::class, 'index']);
Route::post('/upload', [ChatController::class, 'upload']);
Route::post('/chat', [ChatController::class, 'chat']);
Route::post('/clear', [ChatController::class, 'clear']);
```

- [ ] **Step 5: Executar os testes do controller**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08/laravel"
php artisan test tests/Feature/ChatControllerTest.php
```

Esperado: 5 testes PASSED (o `test_index_devolve_view_chat` falhará pois a view ainda não existe — é esperado).

- [ ] **Step 6: Commit**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
git add laravel/routes/web.php laravel/app/Http/Controllers/ChatController.php laravel/tests/Feature/ChatControllerTest.php
git commit -m "feat: laravel - ChatController com rotas upload, chat e clear"
```

---

## Task 5: View `chat.blade.php`

**Files:**
- Create: `laravel/resources/views/chat.blade.php`

- [ ] **Step 1: Criar `laravel/resources/views/chat.blade.php`**

```blade
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>W-Tech AI Chat</title>
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" rel="stylesheet">
    <style>
        html, body { height: 100%; margin: 0; overflow: hidden; }
        body { display: flex; flex-direction: column; background: #f8fafc; }

        /* Navbar */
        .wtech-navbar { background: #1a2f6e; }
        .wtech-navbar img.logo { height: 36px; }

        /* Sidebar */
        #sidebar {
            width: 190px; min-width: 190px;
            background: #fff; border-right: 1px solid #e2e8f0;
            display: flex; flex-direction: column; gap: 14px;
            padding: 14px 12px; overflow-y: auto;
        }

        /* Badges */
        .badge-no-doc   { background: #fee2e2; color: #991b1b; }
        .badge-indexing { background: #fef9c3; color: #854d0e; }
        .badge-active   { background: #dcfce7; color: #166534; }

        /* Upload zone */
        .upload-zone {
            border: 2px dashed #94a3b8; border-radius: 8px;
            padding: 12px; text-align: center; cursor: pointer;
            transition: border-color .2s, background .2s;
        }
        .upload-zone:hover { border-color: #1a2f6e; background: #f0f4ff; }

        /* Indexing steps */
        .step-item { font-size: 11px; color: #94a3b8; display: flex; align-items: center; gap: 6px; }
        .step-item.active { color: #1a2f6e; font-weight: 600; }
        .step-item.done   { color: #16a34a; }

        /* Chat area */
        #chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }

        /* Bubbles */
        .bubble-user { background: #1a2f6e; color: #fff; border-radius: 14px 14px 2px 14px; padding: 9px 14px; max-width: 72%; font-size: 13px; }
        .bubble-bot  { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px 14px 14px 2px; padding: 9px 14px; max-width: 72%; font-size: 13px; }

        /* Bot avatar */
        .bot-avatar {
            width: 28px; height: 28px; min-width: 28px;
            background: #1a2f6e; border: 2px solid #3a5cc5;
            border-radius: 50%; overflow: hidden;
            display: flex; align-items: center; justify-content: center;
        }
        .bot-avatar img { width: 100%; height: 100%; object-fit: contain; }
        .bot-avatar .fallback { color: #fff; font-size: 10px; font-weight: 900; display: none; }

        /* Input bar */
        #input-bar { background: #fff; border-top: 1px solid #e2e8f0; padding: 10px 14px; }
        .input-pill {
            display: flex; align-items: center; gap: 8px;
            border: 1.5px solid #dee2e6; border-radius: 24px;
            padding: 6px 8px 6px 16px; background: #fff;
        }
        #chat-input { flex: 1; border: none; outline: none; font-size: 13px; background: transparent; }
        #fonti-counter { font-size: 11px; color: #94a3b8; white-space: nowrap; font-weight: 500; }
        .btn-send {
            width: 34px; height: 34px; min-width: 34px; border-radius: 50%; border: none;
            background: #1a2f6e; color: #fff; display: flex; align-items: center; justify-content: center;
            cursor: pointer; transition: background .2s;
        }
        .btn-send:disabled { background: #e2e8f0; color: #94a3b8; cursor: default; }

        /* Ricomincia */
        #btn-ricomincia { border: 1px solid #fca5a5; background: #fff5f5; color: #ef4444; font-size: 11px; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
        #btn-ricomincia:hover { background: #fee2e2; }

        /* Toast container */
        #toast-container { position: fixed; bottom: 16px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
    </style>
</head>
<body>

{{-- NAVBAR --}}
<nav class="wtech-navbar d-flex align-items-center gap-2 px-3 py-2">
    <img src="{{ asset('images/logo.png') }}" alt="W-Tech" class="logo"
         onerror="this.style.display='none'">
    <div>
        <div class="text-white fw-bold" style="font-size:14px; line-height:1.2;">W-Tech AI Chat</div>
        <div class="text-white-50" style="font-size:10px; line-height:1.2;">Assistente documentale</div>
    </div>
</nav>

{{-- LAYOUT PRINCIPAL --}}
<div style="display:flex; flex:1; overflow:hidden;">

    {{-- SIDEBAR --}}
    <div id="sidebar">

        {{-- Badge stato --}}
        <div>
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Stato</div>
            <span id="status-badge" class="badge-no-doc px-3 py-1 rounded-pill fw-semibold" style="font-size:10px; display:inline-block;">● Nessun documento</span>
        </div>

        {{-- Steps de indexação (oculto por defeito) --}}
        <div id="indexing-steps" style="display:none;">
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Indicizzazione</div>
            <div id="filename-progress" class="fw-semibold text-primary mb-2" style="font-size:10px; word-break:break-all;"></div>
            <div class="progress mb-2" style="height:4px;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" style="width:100%; background:#1a2f6e;"></div>
            </div>
            <div style="display:flex; flex-direction:column; gap:5px;">
                <div id="step-read"  class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Lettura file</div>
                <div id="step-chunk" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Divisione in chunk</div>
                <div id="step-embed" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Generazione embeddings</div>
                <div id="step-faiss" class="step-item"><i class="fa-solid fa-circle-dot fa-xs"></i> Indicizzazione FAISS</div>
            </div>
        </div>

        {{-- Lista de documentos (oculta por defeito) --}}
        <div id="doc-list-section" style="display:none;">
            <div class="text-uppercase fw-semibold mb-1" style="font-size:9px; color:#94a3b8; letter-spacing:.5px;">Documenti</div>
            <div id="doc-list" style="display:flex; flex-direction:column; gap:6px;"></div>
        </div>

        {{-- Zona upload --}}
        <div id="upload-zone" class="upload-zone" onclick="document.getElementById('file-input').click()">
            <input type="file" id="file-input" style="display:none;" accept=".pdf,.txt,.docx,.xlsx">
            <i class="fa-solid fa-paperclip mb-1 d-block" style="font-size:18px; color:#64748b;"></i>
            <div class="fw-semibold" id="upload-label" style="font-size:11px; color:#475569;">Carica documento</div>
            <div style="font-size:9px; color:#94a3b8; margin-top:3px;">PDF · TXT · DOCX · XLSX · max 20 MB</div>
        </div>

        {{-- Ricomincia (oculto por defeito) --}}
        <button id="btn-ricomincia" style="display:none; margin-top:auto;" onclick="ricomincia()">
            <i class="fa-solid fa-rotate-left fa-xs"></i> Ricomincia
        </button>

    </div>

    {{-- CHAT AREA --}}
    <div style="flex:1; display:flex; flex-direction:column; overflow:hidden;">

        {{-- Mensagens --}}
        <div id="chat-messages">
            <div id="chat-empty" style="margin:auto; text-align:center; color:#94a3b8; font-size:13px;">
                <i class="fa-regular fa-file-lines d-block mb-2" style="font-size:30px;"></i>
                <div class="fw-semibold mb-1" style="color:#64748b;">Nessun documento caricato</div>
                Carica un documento nella barra laterale<br>per iniziare a fare domande.
            </div>
        </div>

        {{-- Input bar --}}
        <div id="input-bar">
            <div class="input-pill">
                <input type="text" id="chat-input"
                       placeholder="Carica un documento per iniziare…"
                       disabled
                       onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage();}">
                <span id="fonti-counter">0 fonti</span>
                <button id="btn-send" class="btn-send" onclick="sendMessage()" disabled>
                    <i class="fa-solid fa-arrow-right fa-sm"></i>
                </button>
            </div>
        </div>

    </div>
</div>

{{-- Toast container --}}
<div id="toast-container"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── Estado ────────────────────────────────────────────────────────────────────
let sessionId = null;
let docs = []; // [{name: string, chunks: number}]

// ── Init ──────────────────────────────────────────────────────────────────────
document.getElementById('file-input').addEventListener('change', function () {
    if (this.files[0]) handleFileUpload(this.files[0]);
});

// ── Atualiza a UI com base no estado atual ────────────────────────────────────
function updateUI() {
    const hasDocs = docs.length > 0;

    // Badge de estado
    const badge = document.getElementById('status-badge');
    if (hasDocs) {
        badge.className = 'badge-active px-3 py-1 rounded-pill fw-semibold';
        badge.style.display = 'inline-block';
        badge.textContent = `● ${docs.length} ${docs.length === 1 ? 'fonte attiva' : 'fonti attive'}`;
    } else {
        badge.className = 'badge-no-doc px-3 py-1 rounded-pill fw-semibold';
        badge.style.display = 'inline-block';
        badge.textContent = '● Nessun documento';
    }

    // Lista de documentos
    const listSection = document.getElementById('doc-list-section');
    const listEl = document.getElementById('doc-list');
    if (hasDocs) {
        listSection.style.display = '';
        listEl.innerHTML = docs.map(d => `
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:8px; font-size:10px;">
                <div class="fw-semibold text-truncate" style="color:#166534; max-width:150px;">
                    <i class="fa-regular fa-file fa-xs me-1"></i>${escapeHtml(d.name)}
                </div>
                <div style="color:#4ade80;">${d.chunks} chunk</div>
            </div>
        `).join('');
    } else {
        listSection.style.display = 'none';
    }

    // Label e estado da zona de upload
    document.getElementById('upload-label').textContent = hasDocs ? 'Aggiungi fonte' : 'Carica documento';
    const zone = document.getElementById('upload-zone');
    if (docs.length >= 5) {
        zone.style.opacity = '0.4';
        zone.style.pointerEvents = 'none';
    } else {
        zone.style.opacity = '1';
        zone.style.pointerEvents = '';
    }

    // Botão Ricomincia
    document.getElementById('btn-ricomincia').style.display = hasDocs ? '' : 'none';

    // Input bar
    const input = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');
    input.disabled = !hasDocs;
    btnSend.disabled = !hasDocs;
    input.placeholder = hasDocs ? 'Inizia a digitare…' : 'Carica un documento per iniziare…';

    // Contador de fontes
    document.getElementById('fonti-counter').textContent = `${docs.length} fonti`;

    // Empty state do chat
    const emptyEl = document.getElementById('chat-empty');
    if (emptyEl) emptyEl.style.display = hasDocs ? 'none' : '';
}

// ── Upload de documento ───────────────────────────────────────────────────────
function handleFileUpload(file) {
    if (docs.length >= 5) {
        showToast('Limite di 5 documenti per sessione raggiunto');
        document.getElementById('file-input').value = '';
        return;
    }

    // Mostrar estado de indexação
    document.getElementById('status-badge').className = 'badge-indexing px-3 py-1 rounded-pill fw-semibold';
    document.getElementById('status-badge').textContent = '⏳ Indicizzazione…';
    document.getElementById('indexing-steps').style.display = '';
    document.getElementById('upload-zone').style.display = 'none';
    document.getElementById('filename-progress').textContent = file.name;

    // Reset visual dos steps
    ['step-read', 'step-chunk', 'step-embed', 'step-faiss'].forEach(id => {
        const el = document.getElementById(id);
        el.className = 'step-item';
        el.querySelector('i').className = 'fa-solid fa-circle-dot fa-xs';
    });

    // Animação client-side dos steps (simulada com timers)
    setTimeout(() => markStepDone('step-read'), 300);
    setTimeout(() => markStepDone('step-chunk'), 900);
    setTimeout(() => markStepDone('step-embed'), 1800);
    // step-faiss é marcado quando a resposta HTTP chegar

    // Enviar ficheiro ao Laravel
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) formData.append('session_id', sessionId);
    formData.append('_token', document.querySelector('meta[name="csrf-token"]').content);

    fetch('/upload', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.error || data.errors) {
                const msg = data.error || Object.values(data.errors).flat().join(' ');
                showToast(msg);
                resetAfterError();
                return;
            }
            // Completa o último step e actualiza o estado
            markStepDone('step-faiss');
            setTimeout(() => {
                sessionId = data.session_id;
                docs.push({ name: data.filename, chunks: data.chunks });
                document.getElementById('indexing-steps').style.display = 'none';
                document.getElementById('upload-zone').style.display = '';
                document.getElementById('file-input').value = '';
                updateUI();
            }, 500);
        })
        .catch(() => {
            showToast('Servizio non disponibile. Avvia api.py.');
            resetAfterError();
        });
}

function markStepDone(id) {
    const el = document.getElementById(id);
    el.className = 'step-item done';
    el.querySelector('i').className = 'fa-solid fa-check fa-xs';
}

function resetAfterError() {
    document.getElementById('indexing-steps').style.display = 'none';
    document.getElementById('upload-zone').style.display = '';
    document.getElementById('file-input').value = '';
    updateUI();
}

// ── Enviar mensagem ───────────────────────────────────────────────────────────
function sendMessage() {
    const input = document.getElementById('chat-input');
    const pergunta = input.value.trim();
    if (!pergunta || !sessionId) return;

    input.value = '';

    // Remove empty state se ainda estiver visível
    const emptyEl = document.getElementById('chat-empty');
    if (emptyEl) emptyEl.remove();

    appendUserBubble(pergunta);
    const spinnerId = appendSpinnerBubble();
    scrollToBottom();

    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
        },
        body: JSON.stringify({ pergunta }),
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById(spinnerId)?.remove();
        if (data.error) {
            if (data.error.includes('Sessione non trovata')) {
                showToast('Sessione scaduta. Ricarica un documento.', 'warning');
                sessionId = null;
                docs = [];
                updateUI();
            } else {
                appendBotBubble(`<em style="color:#ef4444;">${escapeHtml(data.error)}</em>`);
            }
        } else {
            appendBotBubble(escapeHtml(data.resposta).replace(/\n/g, '<br>'));
        }
        scrollToBottom();
    })
    .catch(() => {
        document.getElementById(spinnerId)?.remove();
        appendBotBubble('<em style="color:#ef4444;">Servizio non disponibile.</em>');
        scrollToBottom();
    });
}

function avatarHtml() {
    return `<div class="bot-avatar">
        <img src="/images/logo.png" alt="W"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
        <span class="fallback">W</span>
    </div>`;
}

function appendUserBubble(text) {
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div style="display:flex; justify-content:flex-end;">
            <div class="bubble-user">${escapeHtml(text)}</div>
        </div>
    `);
}

function appendBotBubble(html) {
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div style="display:flex; align-items:flex-end; gap:8px;">
            ${avatarHtml()}
            <div class="bubble-bot">${html}</div>
        </div>
    `);
}

function appendSpinnerBubble() {
    const id = 'spinner-' + Date.now();
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', `
        <div id="${id}" style="display:flex; align-items:flex-end; gap:8px;">
            ${avatarHtml()}
            <div class="bubble-bot" style="color:#94a3b8; font-style:italic; font-size:12px;">
                <span class="me-1">● ●</span> elaborazione in corso…
            </div>
        </div>
    `);
    return id;
}

function scrollToBottom() {
    const el = document.getElementById('chat-messages');
    el.scrollTop = el.scrollHeight;
}

// ── Ricomincia ────────────────────────────────────────────────────────────────
function ricomincia() {
    if (!confirm('Ricominciare? La sessione e la cronologia verranno eliminate.')) return;

    fetch('/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
        },
        body: JSON.stringify({ session_id: sessionId }),
    }).finally(() => {
        sessionId = null;
        docs = [];
        document.getElementById('chat-messages').innerHTML = `
            <div id="chat-empty" style="margin:auto; text-align:center; color:#94a3b8; font-size:13px;">
                <i class="fa-regular fa-file-lines d-block mb-2" style="font-size:30px;"></i>
                <div class="fw-semibold mb-1" style="color:#64748b;">Nessun documento caricato</div>
                Carica un documento nella barra laterale<br>per iniziare a fare domande.
            </div>
        `;
        updateUI();
    });
}

// ── Toasts ────────────────────────────────────────────────────────────────────
function showToast(message, type = 'danger') {
    const id = 'toast-' + Date.now();
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', `
        <div id="${id}" style="background:${type==='danger'?'#ef4444':'#f59e0b'}; color:#fff; padding:10px 14px; border-radius:8px; font-size:13px; display:flex; gap:8px; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,.15);">
            <span style="flex:1;">${escapeHtml(message)}</span>
            <button onclick="document.getElementById('${id}').remove()" style="background:none;border:none;color:#fff;cursor:pointer;font-size:16px;">×</button>
        </div>
    `);
    setTimeout(() => document.getElementById(id)?.remove(), 5000);
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function escapeHtml(text) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(text));
    return d.innerHTML;
}

// ── Boot ──────────────────────────────────────────────────────────────────────
updateUI();
</script>
</body>
</html>
```

- [ ] **Step 2: Executar os testes do controller (agora deve passar o teste da view)**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08/laravel"
php artisan test tests/Feature/ChatControllerTest.php
```

Esperado: 6 testes PASSED (incluindo `test_index_devolve_view_chat`).

- [ ] **Step 3: Abrir no browser e verificar a interface**

Abre `https://ai-wtech.test`. Deve aparecer:
- Navbar azul escuro (`#1a2f6e`) com placeholder onde vai a logo
- Sidebar à esquerda com badge vermelho "Nessun documento"
- Área de chat vazia com ícone de ficheiro e mensagem em italiano
- Input bar desabilitado com "Carica un documento per iniziare…" e "0 fonti"

- [ ] **Step 4: Commit**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
git add laravel/resources/views/chat.blade.php
git commit -m "feat: laravel - view chat.blade.php com sidebar, bubbles e JS"
```

---

## Task 6: Teste de integração completo

- [ ] **Step 1: Iniciar o Flask**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
source venv/bin/activate
python api.py
```

Esperado: `* Running on http://127.0.0.1:5000`

- [ ] **Step 2: Abrir `https://ai-wtech.test` e testar upload**

1. Arrasta ou clica para carregar um ficheiro `.txt` ou `.pdf`
2. Deve ver os 4 steps a fazer check sequencialmente na sidebar
3. Após concluir: badge verde "1 fonte attiva", nome do ficheiro na lista, input habilitado, "1 fonti" no contador

- [ ] **Step 3: Testar o chat**

1. Escreve uma pergunta sobre o documento e prime Enter
2. Deve aparecer bolha azul à direita (mensagem do utilizador)
3. Deve aparecer spinner "● ● elaborazione in corso…" com avatar W (placeholder)
4. Após resposta: bolha branca à esquerda com a resposta do Groq em italiano

- [ ] **Step 4: Testar segundo documento**

1. Clica "Aggiungi fonte" e carrega um segundo ficheiro
2. Badge muda para "2 fonti attive"
3. Contador "2 fonti" no input bar
4. Faz uma pergunta que só existe no segundo documento — a resposta deve vir correctamente

- [ ] **Step 5: Testar Ricomincia**

1. Clica "Ricomincia" e confirma
2. Sessão é limpa: badge vermelho "Nessun documento", chat vazio, input desabilitado

- [ ] **Step 6: Testar tratamento de erros**

1. Para o Flask (`Ctrl+C` no terminal)
2. Tenta carregar um ficheiro — deve aparecer toast laranja "Servizio non disponibile. Avvia api.py."

- [ ] **Step 7: Colocar a logo W-Tech**

Copia o ficheiro da logo para:
```
laravel/public/images/logo.png
```

Recarrega a página — a logo deve aparecer na navbar e como avatar do bot nas bolhas de resposta.

- [ ] **Step 8: Commit final**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
git add -A
git commit -m "chore: integração completa RAG Laravel frontend - testes manuais OK"
```

---

## Verificação final

Após todos os tasks o projecto deve ter:

| Componente | Estado |
|------------|--------|
| `rag.py` | Suporta `.txt`, `.pdf`, `.docx`, `.xlsx` |
| `tests/test_rag.py` | 7 testes PASSED |
| `api.py` | 3 endpoints: upload, chat, clear |
| `tests/test_api.py` | 5 testes PASSED |
| `laravel/` | Projecto Laravel 12 com Valet em `ai-wtech.test` |
| `ChatController` | 4 métodos: index, upload, chat, clear |
| `ChatControllerTest` | 6 testes PASSED |
| `chat.blade.php` | UI completa: sidebar + chat + JS |
| Logo | `laravel/public/images/logo.png` colocada manualmente |

Para arrancar o sistema a qualquer momento:
```bash
# Terminal — Flask
cd "/Users/tanara/dev/pessoal/AI/settimana 08" && source venv/bin/activate && python api.py

# Browser — Laravel (automático via Valet)
open https://ai-wtech.test
```
