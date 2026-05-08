# AI Chat — RAG: Documentação Técnica

**Stack:** Python · Flask · LangChain · FAISS · HuggingFace · Groq · LLaMA 3.3 70B · Laravel 12 · PHP 8.3  
**Preparado por:** Tanara Cavalcante · W-Tech · Maio 2026

---

## Índice

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Backend Python — Arquivos e Responsabilidades](#2-backend-python--arquivos-e-responsabilidades)
3. [Pipeline: do Documento à Resposta](#3-pipeline-do-documento-à-resposta)
4. [Persistência Sem Banco de Dados](#4-persistência-sem-banco-de-dados)
5. [Tipos de Documento Suportados](#5-tipos-de-documento-suportados)
6. [Frontend Laravel — Arquivos e Responsabilidades](#6-frontend-laravel--arquivos-e-responsabilidades)
7. [Integração Python ↔ Laravel](#7-integração-python--laravel)
8. [Testes e Qualidade de Código](#8-testes-e-qualidade-de-código)
9. [Glossário Técnico](#9-glossário-técnico)

---

## 1. Visão Geral da Arquitetura

O projeto é um **chatbot com RAG** (Retrieval-Augmented Generation): o usuário faz upload de documentos e o sistema responde perguntas baseadas **exclusivamente** no conteúdo desses documentos — sem inventar informações.

O sistema é dividido em **dois projetos independentes** que se comunicam via HTTP:

```
Navegador (HTML/JS)
       ↕  fetch POST
Laravel (PHP) — porta 8000    [AI-chat-frontend/]
       ↕  Http::facade (Guzzle)
Flask (Python) — porta 5001   [AI-chat/]
       ↕  HTTP REST
Groq API (LLaMA 3.3 70B)
```

### Estrutura de pastas

| Projeto | Stack | Responsabilidade |
|---------|-------|-----------------|
| `AI-chat/` | Python · Flask | Backend de IA: processamento de documentos, embeddings, FAISS, chamada ao LLM |
| `AI-chat-frontend/` | Laravel · PHP | Frontend: interface do usuário, proxy de requisições, sessão |

---

## 2. Backend Python — Arquivos e Responsabilidades

### `rag.py` — Núcleo de IA (~160 linhas)

É o **coração inteligente do projeto**. Contém toda a lógica de processamento de documentos e busca por similaridade. Não tem rotas HTTP — é uma biblioteca interna usada por `api.py` e `main.py`.

Exporta **3 funções**:

| Função | O que faz | Retorna |
|--------|-----------|---------|
| `carregar_documento(caminho)` | Lê um arquivo (.txt, .pdf, .docx, .xlsx) e transforma em objetos `Document` do LangChain | Lista de `Document` |
| `criar_vector_store(docs)` | Faz chunking → embeddings → indexação FAISS em sequência | FAISS store + nº de chunks |
| `buscar_contexto(store, pergunta)` | Converte pergunta em vetor e busca os 6 chunks mais similares | Texto concatenado + lista com scores |

> **PDF tem tratamento especial:** usa `pdfplumber` diretamente para extrair texto página por página com layout preservado, melhorando a qualidade dos chunks em documentos complexos.

---

### `api.py` — Servidor HTTP (Flask, porta 5001)

É o **servidor que o Laravel chama**. Recebe arquivos e perguntas via HTTP e orquestra as chamadas ao `rag.py` e à API do Groq.

Expõe **3 endpoints**:

| Método | Rota | Função |
|--------|------|--------|
| `POST` | `/api/upload` | Recebe arquivo → chama `carregar_documento` + `criar_vector_store` → salva sessão na memória |
| `POST` | `/api/chat` | Recebe pergunta + session_id → busca contexto → chama Groq API → retorna resposta |
| `POST` | `/api/clear` | Remove a sessão da memória (libera RAM) |

**Gerenciamento de sessões:** cada upload cria um `session_id` (UUID). O FAISS store correspondente fica salvo no dicionário `sessions = {}` em RAM. Múltiplos documentos da mesma sessão são mesclados via `store.merge_from()`.

---

### `main.py` — Interface Terminal

Versão **linha de comando** do chatbot — foi o ponto de partida do desenvolvimento, antes de existir o frontend Laravel.

```bash
# Sem documento: chatbot genérico em italiano
python main.py

# Com documento: modo RAG
python main.py relatorio.pdf
```

No modo RAG, exibe feedback visual em 4 passos:

```
[1/4] Leitura do documento 'relatorio.pdf'...
      ✓ 24 secção(ões) encontrada(s)
[2/4] Divisão em chunks...
[3/4] Geração dos embeddings (pode demorar um momento)...
[4/4] Indexação no FAISS...
      ✓ 87 chunks indexados
      ✓ Base de conhecimento pronta!
```

> O `main.py` acessa o `rag.py` **diretamente**, sem HTTP. Útil para testar rapidamente sem subir Flask ou Laravel.

---

### `requirements.txt` — Dependências do Projeto

Lista todos os pacotes Python necessários. Instalação com:

```bash
pip install -r requirements.txt
```

| Pacote | Para que serve |
|--------|---------------|
| `flask` | Framework web para criar os endpoints HTTP |
| `groq` | Cliente oficial da API Groq (LLaMA 3.3 70B) |
| `python-dotenv` | Carrega variáveis do `.env` (ex: chave da API) |
| `pdfplumber` | Extração de texto de PDFs com layout preservado |
| `langchain-community` | Loaders para .docx, .xlsx, .txt; integração FAISS |
| `langchain-huggingface` | Integração com modelos de embedding do HuggingFace |
| `sentence-transformers` | Modelo de embedding multilíngue (roda localmente, sem custo) |
| `faiss-cpu` | Biblioteca do Facebook para busca vetorial ultrarrápida |
| `docx2txt` | Extração de texto de arquivos .docx (Word) |
| `openpyxl` / `unstructured[xlsx]` | Leitura de planilhas Excel |
| `pytest` | Framework de testes automatizados |

> **Por que usar `requirements.txt`?** Garante que qualquer pessoa que baixar o projeto instale exatamente as mesmas versões — evita o problema "funciona na minha máquina".

---

## 3. Pipeline: do Documento à Resposta

Este é o fluxo central: o que acontece desde o momento em que o usuário escolhe um arquivo até receber a resposta.

### Fase 1 — Upload e Leitura

O usuário seleciona um arquivo. O JavaScript envia via `FormData` ao Laravel (`POST /upload`). O Laravel valida e repassa ao Flask (`POST /api/upload`). O Flask salva em arquivo temporário e chama `carregar_documento()`, que usa o loader correto para o formato. O resultado é uma lista de objetos `Document` do LangChain, cada um com:
- `page_content` — o texto
- `metadata` — número da página, caminho do arquivo

---

### Fase 2 — Chunking (Divisão em Pedaços)

Documentos longos não cabem inteiros no modelo de IA (limite de tokens). O `RecursiveCharacterTextSplitter` divide o texto em chunks de **1.200 caracteres** com **150 caracteres de sobreposição** entre pedaços consecutivos.

A sobreposição é fundamental: garante que uma frase na fronteira entre dois chunks não se perca.

O splitter divide de forma inteligente, na seguinte ordem de preferência:
1. Por parágrafos (`\n\n`)
2. Por linhas (`\n`)
3. Por frases
4. Por palavras

---

### Fase 3 — Embeddings (Vetorização)

Cada chunk é convertido em um **vetor numérico de 384 dimensões** pelo modelo `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace).

Um embedding captura o **significado semântico** do texto: frases com o mesmo sentido ficam próximas no espaço vetorial, mesmo usando palavras diferentes.

- Roda **localmente na máquina** — sem custo de API
- Download de ~120 MB na primeira execução; nas seguintes usa cache

---

### Fase 4 — FAISS (Indexação)

**FAISS** (Facebook AI Similarity Search) armazena todos os vetores em um índice otimizado para busca por similaridade.

Em vez de comparar a pergunta com cada chunk um por um (custo O(n)), usa estruturas de dados especiais para encontrar os mais similares em milissegundos, mesmo com milhares de chunks.

O índice fica **na memória RAM**, associado ao `session_id` do usuário.

---

### Fase 5 — RAG (Recuperação + Geração de Resposta)

Quando o usuário faz uma pergunta:

1. A pergunta é convertida em vetor (mesmo modelo de embedding)
2. FAISS busca os **6 chunks com menor distância L2** (= maior similaridade)
3. Esses chunks são concatenados e injetados como contexto no prompt do LLM
4. O Groq/LLaMA gera a resposta baseada **apenas** nesse contexto
5. Se a resposta não estiver no documento → mensagem padronizada (sem invenção)

```
Contesto dal documento:
---
[chunk 1]
---
[chunk 2]
---
...
Domanda: [pergunta do usuário]
```

> **Os 4 passos animados na sidebar** (Lettura file → Divisione in chunk → Generazione embeddings → Indicizzazione FAISS) espelham as fases 1 a 4. Os 3 primeiros usam timers simulados; o último só é marcado quando a resposta HTTP do Flask chega.

---

## 4. Persistência Sem Banco de Dados

O projeto **não usa banco de dados** (MySQL, PostgreSQL, SQLite). Os dados ficam em duas camadas de memória:

### Python — RAM

```python
sessions = {
    "uuid-da-sessao": {
        "store": <FAISS index>,
        "docs": [{"name": "relatorio.pdf", "chunks": 87}]
    }
}
```

- Vida útil: até o servidor Flask reiniciar ou chamar `/api/clear`
- Múltiplos documentos são mesclados via `store.merge_from(new_store)`
- Limite: memória RAM disponível

### Laravel — Session PHP

```php
session(['python_session_id' => $data['session_id']]);
```

- Persiste o `session_id` entre abas e recarregamentos
- Vincula cada navegador à sua sessão Python
- Expira automaticamente pela config de sessão do Laravel

> **Implicação:** se o Flask for reiniciado, todas as sessões são perdidas e o usuário precisa fazer upload novamente. Isso é intencional — simplifica enormemente a arquitetura.

### Limite de documentos por sessão

O sistema suporta até **5 documentos por sessão**. Os vetores de todos os documentos ficam no mesmo índice e são pesquisados juntos.

---

## 5. Tipos de Documento Suportados

| Formato | Extensão | Biblioteca | Observações |
|---------|----------|------------|-------------|
| PDF | `.pdf` | `pdfplumber` | Extração página a página com layout. Ideal para relatórios, manuais, contratos. |
| Word | `.docx` | `Docx2txtLoader` + `docx2txt` | Extrai texto de parágrafos e tabelas. |
| Excel | `.xlsx` | `UnstructuredExcelLoader` | Converte células em texto estruturado. |
| Texto | `.txt` | `TextLoader` | Leitura direta UTF-8. O mais simples e rápido. |

**Validação em 3 camadas:**
1. **Frontend** — atributo `accept=".pdf,.txt,.docx,.xlsx"` no `<input>`
2. **Laravel** — regra `mimes:pdf,txt,docx,xlsx|max:20480`
3. **Flask** — dicionário `EXTENSOES_PERMITIDAS` no `api.py`

---

## 6. Frontend Laravel — Arquivos e Responsabilidades

### `ChatController.php` — Intermediário Laravel ↔ Flask

É o **único ponto de contato** entre o browser e o backend Python. Age como proxy: recebe requisições do browser, valida, e repassa ao Flask. O browser nunca conhece o endereço do Flask.

| Método | Rota | O que faz |
|--------|------|-----------|
| `index()` | `GET /` | Renderiza `chat.blade.php` |
| `upload()` | `POST /upload` | Valida arquivo → envia ao Flask → salva `session_id` na sessão PHP |
| `chat()` | `POST /chat` | Valida pergunta → envia ao Flask com `session_id` → retorna resposta |
| `clear()` | `POST /clear` | Chama Flask para liberar RAM → limpa sessão PHP |

O endereço do Flask é configurado via `.env`:
```
PYTHON_API_URL=http://127.0.0.1:5001
```

---

### `chat.blade.php` + `sidebar.blade.php` — Interface Visual

- `chat.blade.php` — página principal: área de mensagens + barra de input
- `sidebar.blade.php` — upload, passos de indexação animados, lista de documentos, botão reiniciar

A sidebar exibe 4 etapas durante o upload que espelham o pipeline real de processamento.

---

### `public/js/chat.js` — Lógica JavaScript

Gerencia toda a interatividade sem recarregar a página:

- **Upload:** captura o arquivo, exibe animação de progresso, envia via `FormData`, atualiza estado
- **Chat:** envia pergunta, exibe spinner, renderiza resposta
- **Estado:** mantém `sessionId` e lista de documentos (`docs[]`) em memória
- **UI:** habilita/desabilita input, atualiza badge de status, exibe toasts de erro

---

## 7. Integração Python ↔ Laravel

A comunicação usa **HTTP REST** puro. O Laravel usa `Http::facade` (baseado em Guzzle) para chamar o Flask.

### Fluxo de Upload

```
Browser
  → POST /upload (FormData + CSRF token)
Laravel ChatController::upload()
  → valida mimes/tamanho
  → Http::attach('file')->post('http://127.0.0.1:5001/api/upload')
Flask /api/upload
  → salva arquivo temporário
  → carregar_documento() → criar_vector_store()
  → retorna {"session_id": "...", "chunks": 87}
Laravel
  → session(['python_session_id' => ...])
  → retorna JSON ao browser
Browser
  → armazena sessionId em JS
  → atualiza UI (marca FAISS como concluído)
```

### Fluxo de Chat

```
Browser
  → POST /chat {"pergunta": "..."}
Laravel ChatController::chat()
  → recupera session_id da sessão PHP
  → Http::post('/api/chat', {session_id, pergunta})
Flask /api/chat
  → buscar_contexto(store, pergunta) → top 6 chunks
  → monta prompt com contexto
  → Groq API → LLaMA 3.3 70B
  → retorna {"resposta": "...", "chunks_usados": [...]}
Browser
  → remove spinner
  → renderiza bolha de resposta
```

> **Por que o Laravel age como proxy?** O Flask roda na porta 5001 e nunca é acessado diretamente pelo browser. Todo o tráfego passa pelo Laravel, que adiciona validação, proteção CSRF e controle de sessão.

---

## 8. Testes e Qualidade de Código

Testes escritos com **pytest**, na pasta `tests/`. Executar com:

```bash
pytest tests/ -v
```

### `test_rag.py` — Testes Unitários

Testa cada função de `rag.py` isoladamente, usando arquivos temporários (`tmp_path` do pytest):

| Teste | O que verifica |
|-------|---------------|
| `test_carrega_txt` | Carregamento de `.txt` retorna ≥1 `Document` |
| `test_ficheiro_nao_existe` | Lança `FileNotFoundError` para caminho inválido |
| `test_formato_nao_suportado` | Lança `ValueError` para extensão `.csv` |
| `test_cria_vector_store` | FAISS store criado com sucesso a partir de Documents |
| `test_vector_store_busca_relevante` | Chunk sobre preço é retornado para pergunta sobre custo |
| `test_busca_contexto_devolve_texto_e_scores` | CEO correto encontrado para pergunta sobre diretor |
| `test_carrega_xlsx` | Carregamento de `.xlsx` detecta conteúdo das células |

### `test_api.py` — Testes de Integração

Testa os endpoints HTTP usando `app.test_client()` do Flask (sem subir servidor real):

| Teste | O que verifica |
|-------|---------------|
| `test_upload_sem_ficheiro` | Retorna HTTP 400 sem arquivo |
| `test_upload_formato_invalido` | Retorna HTTP 400 + mensagem para `.csv` |
| `test_chat_sessao_nao_encontrada` | Retorna HTTP 404 para `session_id` inexistente |
| `test_chat_pergunta_vazia` | Retorna HTTP 400 ou 404 para pergunta vazia |
| `test_clear_sessao_inexistente` | Retorna HTTP 200 mesmo sem sessão (idempotente) |

### Por que os testes foram importantes no desenvolvimento?

1. **Documentação executável** — cada teste descreve um comportamento esperado em linguagem próxima ao humano. Ler os testes é entender o que o sistema faz.

2. **Rede de segurança** — ao refatorar o `rag.py` (suporte a `.docx`, melhora no PDF), os testes apontaram imediatamente se algo quebrou.

3. **Contratos de interface** — os testes de `api.py` especificam exatamente quais códigos HTTP cada endpoint retorna, facilitando a integração com o Laravel.

---

## 9. Glossário Técnico

| Termo | Definição |
|-------|-----------|
| **RAG** | *Retrieval-Augmented Generation*. Técnica que combina busca de informação com geração de texto por IA. O modelo busca no documento antes de responder, em vez de usar apenas a memória de treinamento. |
| **Chunk** | Pedaço de texto extraído do documento. O documento é dividido em vários chunks para que o modelo processe apenas as partes relevantes. |
| **Embedding** | Representação numérica (vetor) de um texto. Textos com significados similares têm vetores próximos — permite busca por significado, não por palavra-chave. |
| **FAISS** | *Facebook AI Similarity Search*. Biblioteca que armazena vetores e encontra os mais similares a uma consulta de forma ultrarrápida. |
| **LLM** | *Large Language Model*. Modelo de linguagem de grande escala, como o LLaMA 3.3 70B. Responsável por gerar o texto da resposta. |
| **Groq** | Plataforma de inferência com hardware especializado (LPU), oferecendo respostas muito rápidas. Usada via API para rodar o LLaMA 3.3 70B. |
| **LangChain** | Framework Python que padroniza a integração entre loaders, modelos de embedding, vector stores e LLMs. Age como "cola" entre as partes do pipeline. |
| **Flask** | Microframework web em Python. Leve e simples, ideal para criar APIs HTTP rapidamente. |
| **Session ID** | Identificador único (UUID) gerado no primeiro upload. Associa o índice FAISS de um usuário às suas requisições subsequentes. |
| **Score L2** | Distância euclidiana entre dois vetores. Quanto menor, mais similar. Usado pelo FAISS para classificar chunks por relevância. |
| **CSRF Token** | Token de segurança do Laravel que previne ataques cross-site. O JavaScript o lê de uma meta tag e inclui em todas as requisições POST. |
| **Blade** | Motor de templates do Laravel. Permite escrever HTML com lógica PHP usando `{{ }}` e `@include`, gerando HTML puro no servidor. |

---

*AI Chat — Documentação Técnica · W-Tech · Tanara Cavalcante · Maio 2026*
