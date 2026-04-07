# RAG Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar suporte a documentos (.txt, .pdf, .docx) ao chatbot existente usando RAG (Retrieval-Augmented Generation), com feedback verbose no terminal para fins de aprendizado.

**Architecture:** O `main.py` existente será modificado para perguntar ao utilizador se quer carregar um documento. A lógica RAG fica em `rag.py` (funções puras e testáveis). O `main.py` orquestra o fluxo e imprime o feedback verbose. O chatbot responde sempre em italiano.

**Tech Stack:** Python, Groq API, LangChain, sentence-transformers (all-MiniLM-L6-v2), FAISS, pypdf, python-docx

---

## Estrutura de ficheiros

```
settimana 08/
├── main.py                  ← MODIFICAR: adicionar fluxo RAG + verbose output
├── rag.py                   ← CRIAR: funções de indexação e busca
├── tests/
│   └── test_rag.py          ← CRIAR: testes das funções RAG
└── .env                     ← existente (não modificar)
```

---

## Task 1: Instalar dependências

**Files:**
- No files to create/modify — só instalação de pacotes

- [ ] **Step 1: Instalar as bibliotecas necessárias**

```bash
pip install langchain-community sentence-transformers faiss-cpu pypdf python-docx pytest
```

- [ ] **Step 2: Verificar que instalaram corretamente**

```bash
python -c "from langchain_community.document_loaders import PyPDFLoader; print('OK')"
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
python -c "import faiss; print('OK')"
```

Esperado: três linhas com `OK`

- [ ] **Step 3: Commit**

```bash
# Nada para commitar — sem alterações em ficheiros
# (se tiveres requirements.txt, podes actualizar)
```

---

## Task 2: Criar `rag.py` — função `carregar_documento`

**Conceito educacional:** LangChain tem "Loaders" — classes especializadas para cada tipo de ficheiro. Cada Loader sabe como ler o formato e devolver uma lista de `Document` (objecto com `page_content` e `metadata`).

**Files:**
- Create: `rag.py`
- Create: `tests/test_rag.py`

- [ ] **Step 1: Criar ficheiro de testes `tests/test_rag.py`**

```python
# tests/test_rag.py

import pytest
import os
import sys

# Adiciona a pasta raiz ao path para importar rag.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import carregar_documento


def test_carrega_txt(tmp_path):
    # Cria um ficheiro .txt temporário para o teste
    ficheiro = tmp_path / "teste.txt"
    ficheiro.write_text("Este é o conteúdo do teste.", encoding="utf-8")

    docs = carregar_documento(str(ficheiro))

    # Deve devolver uma lista com pelo menos um documento
    assert len(docs) >= 1
    # O conteúdo deve estar presente
    assert "Este é o conteúdo do teste." in docs[0].page_content


def test_ficheiro_nao_existe():
    # Deve lançar erro se o ficheiro não existir
    with pytest.raises(FileNotFoundError):
        carregar_documento("ficheiro_que_nao_existe.txt")


def test_formato_nao_suportado(tmp_path):
    # Deve lançar erro para formatos não suportados
    ficheiro = tmp_path / "teste.xlsx"
    ficheiro.write_text("conteudo")

    with pytest.raises(ValueError):
        carregar_documento(str(ficheiro))
```

- [ ] **Step 2: Criar `rag.py` com a função `carregar_documento`**

```python
# rag.py

import os
from langchain_community.document_loaders import (
    TextLoader,      # para ficheiros .txt
    PyPDFLoader,     # para ficheiros .pdf
    Docx2txtLoader,  # para ficheiros .docx
)


def carregar_documento(caminho: str):
    """
    Lê um documento e devolve uma lista de objectos Document do LangChain.
    
    Cada Document tem:
      - page_content: o texto da página/secção
      - metadata: informação extra (ex: número de página, caminho do ficheiro)
    
    Parâmetros:
      caminho: caminho completo para o ficheiro (.txt, .pdf, .docx)
    
    Devolve:
      Lista de Document objects
    """
    # Verifica se o ficheiro existe
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Ficheiro não encontrado: {caminho}")

    # Determina o tipo de ficheiro pela extensão
    extensao = os.path.splitext(caminho)[1].lower()

    # Escolhe o Loader correcto conforme a extensão
    if extensao == ".txt":
        loader = TextLoader(caminho, encoding="utf-8")
    elif extensao == ".pdf":
        loader = PyPDFLoader(caminho)
    elif extensao == ".docx":
        loader = Docx2txtLoader(caminho)
    else:
        raise ValueError(
            f"Formato '{extensao}' não suportado. Use .txt, .pdf ou .docx"
        )

    # load() lê o ficheiro e devolve a lista de Documents
    docs = loader.load()
    return docs
```

- [ ] **Step 3: Executar os testes**

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
pytest tests/test_rag.py -v
```

Esperado:
```
PASSED tests/test_rag.py::test_carrega_txt
PASSED tests/test_rag.py::test_ficheiro_nao_existe
PASSED tests/test_rag.py::test_formato_nao_suportado
```

- [ ] **Step 4: Commit**

```bash
git add rag.py tests/test_rag.py
git commit -m "feat: rag - carregar_documento suporta txt, pdf, docx"
```

---

## Task 3: Adicionar `criar_vector_store` ao `rag.py`

**Conceito educacional:** Esta função faz três coisas em sequência:
1. **Chunking** — divide o texto em pedaços menores (o modelo tem limite de tokens; chunks permitem busca precisa)
2. **Embedding** — converte cada chunk num vector numérico (lista de ~384 números que representam o "significado" do texto)
3. **FAISS** — armazena os vectores numa estrutura que permite busca rápida por similaridade

**Files:**
- Modify: `rag.py`
- Modify: `tests/test_rag.py`

- [ ] **Step 1: Adicionar teste para `criar_vector_store` em `tests/test_rag.py`**

Adiciona no final do ficheiro `tests/test_rag.py`:

```python
from rag import criar_vector_store
from langchain.schema import Document


def test_cria_vector_store():
    # Cria documents de teste directamente (sem precisar de ficheiro)
    docs = [
        Document(page_content="O gato está no jardim."),
        Document(page_content="O cão ladra à noite."),
        Document(page_content="A empresa foi fundada em 1990."),
    ]

    store = criar_vector_store(docs)

    # O store deve ser criado com sucesso (não None)
    assert store is not None


def test_vector_store_busca_relevante():
    docs = [
        Document(page_content="O produto custa 50 euros."),
        Document(page_content="A reunião é às 15h."),
        Document(page_content="O relatório tem 10 páginas."),
    ]

    store = criar_vector_store(docs)

    # Busca algo relacionado com preço — deve encontrar o chunk certo
    resultados = store.similarity_search("quanto custa?", k=1)
    assert "50 euros" in resultados[0].page_content
```

- [ ] **Step 2: Adicionar `criar_vector_store` ao `rag.py`**

Primeiro, adiciona os imports novos **no topo de `rag.py`**, logo após os imports existentes:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
```

Depois, adiciona a função **no final de `rag.py`** (após `carregar_documento`):

```python
def criar_vector_store(docs, chunk_size=500, chunk_overlap=50):
    """
    Transforma uma lista de Documents num vector store pesquisável.
    
    Processo:
      1. Chunking: divide o texto em pedaços de ~500 caracteres
         (com 50 caracteres de sobreposição para não perder contexto nas bordas)
      2. Embedding: converte cada chunk num vector numérico usando
         o modelo all-MiniLM-L6-v2 (leve, multilíngue, grátis)
      3. FAISS: armazena os vectores para busca por similaridade
    
    Parâmetros:
      docs: lista de Document objects (saída de carregar_documento)
      chunk_size: tamanho máximo de cada chunk em caracteres
      chunk_overlap: sobreposição entre chunks consecutivos
    
    Devolve:
      FAISS vector store pronto para pesquisa
    """
    # PASSO 1: CHUNKING
    # RecursiveCharacterTextSplitter divide o texto de forma inteligente:
    # tenta dividir por parágrafos, depois frases, depois palavras
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    # PASSO 2: EMBEDDINGS
    # HuggingFaceEmbeddings carrega o modelo localmente (sem API key)
    # Na primeira execução, faz download do modelo (~80MB)
    modelo_embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # PASSO 3: FAISS
    # from_documents() faz embed de cada chunk e armazena no índice FAISS
    vector_store = FAISS.from_documents(chunks, modelo_embeddings)

    return vector_store, len(chunks)
```

- [ ] **Step 3: Actualizar o teste `test_cria_vector_store` para o novo retorno**

A função agora devolve `(store, n_chunks)`. Actualiza os testes em `tests/test_rag.py`:

```python
def test_cria_vector_store():
    docs = [
        Document(page_content="O gato está no jardim."),
        Document(page_content="O cão ladra à noite."),
        Document(page_content="A empresa foi fundada em 1990."),
    ]

    store, n_chunks = criar_vector_store(docs)

    assert store is not None
    assert n_chunks >= 1


def test_vector_store_busca_relevante():
    docs = [
        Document(page_content="O produto custa 50 euros."),
        Document(page_content="A reunião é às 15h."),
        Document(page_content="O relatório tem 10 páginas."),
    ]

    store, _ = criar_vector_store(docs)

    resultados = store.similarity_search("quanto custa?", k=1)
    assert "50 euros" in resultados[0].page_content
```

- [ ] **Step 4: Executar os testes**

```bash
pytest tests/test_rag.py -v
```

Esperado:
```
PASSED tests/test_rag.py::test_carrega_txt
PASSED tests/test_rag.py::test_ficheiro_nao_existe
PASSED tests/test_rag.py::test_formato_nao_suportado
PASSED tests/test_rag.py::test_cria_vector_store
PASSED tests/test_rag.py::test_vector_store_busca_relevante
```

Nota: `test_cria_vector_store` e `test_vector_store_busca_relevante` são lentos na primeira execução (download do modelo ~80MB). Nas seguintes, usam cache.

- [ ] **Step 5: Commit**

```bash
git add rag.py tests/test_rag.py
git commit -m "feat: rag - criar_vector_store com chunking, embeddings e FAISS"
```

---

## Task 4: Adicionar `buscar_contexto` ao `rag.py`

**Conceito educacional:** Esta função recebe a pergunta do utilizador, converte-a no mesmo espaço vectorial dos chunks (usando o mesmo modelo de embedding), e encontra os chunks cujos vectores são mais "próximos" do vector da pergunta. "Próximo" aqui significa similaridade coseno — chunks semanticamente relacionados ficam próximos no espaço vectorial.

**Files:**
- Modify: `rag.py`
- Modify: `tests/test_rag.py`

- [ ] **Step 1: Adicionar teste para `buscar_contexto` em `tests/test_rag.py`**

```python
from rag import buscar_contexto


def test_busca_contexto_devolve_texto_e_scores():
    docs = [
        Document(page_content="O CEO da empresa chama-se Marco Rossi."),
        Document(page_content="O escritório fica em Milão."),
        Document(page_content="A empresa tem 200 funcionários."),
        Document(page_content="O produto principal é um software de gestão."),
    ]

    store, _ = criar_vector_store(docs)
    contexto, resultados = buscar_contexto(store, "Quem é o director?")

    # Deve devolver texto (string não vazia)
    assert isinstance(contexto, str)
    assert len(contexto) > 0

    # Deve devolver lista de resultados com score
    assert len(resultados) > 0

    # O chunk mais relevante deve mencionar o CEO
    assert "Marco Rossi" in contexto
```

- [ ] **Step 2: Adicionar `buscar_contexto` ao `rag.py`**

Adiciona a função **no final de `rag.py`** (após `criar_vector_store`). Não são necessários imports novos.

```python
def buscar_contexto(vector_store, pergunta: str, k: int = 3):
    """
    Busca os chunks mais relevantes para a pergunta dada.
    
    Como funciona:
      1. Converte a pergunta num vector (usando o mesmo modelo de embedding)
      2. Calcula a similaridade entre o vector da pergunta e todos os chunks
      3. Devolve os k chunks com maior similaridade
    
    Parâmetros:
      vector_store: FAISS store criado por criar_vector_store()
      pergunta: texto da pergunta do utilizador
      k: número de chunks a devolver (padrão: 3)
    
    Devolve:
      contexto (str): texto dos chunks concatenados, para enviar ao LLM
      resultados (list): lista de (Document, score) para mostrar no verbose
    """
    # similarity_search_with_score devolve lista de (Document, score)
    # score é a distância L2 — quanto MENOR, mais similar
    resultados = vector_store.similarity_search_with_score(pergunta, k=k)

    # Concatena o texto dos chunks encontrados
    textos = [doc.page_content for doc, score in resultados]
    contexto = "\n---\n".join(textos)

    return contexto, resultados
```

- [ ] **Step 3: Executar os testes**

```bash
pytest tests/test_rag.py -v
```

Esperado: todos os testes PASSED (6 no total)

- [ ] **Step 4: Commit**

```bash
git add rag.py tests/test_rag.py
git commit -m "feat: rag - buscar_contexto com similaridade vectorial"
```

---

## Task 5: Modificar `main.py` para integrar o RAG

**Conceito educacional:** O `main.py` é o "maestro" — usa as funções do `rag.py` e adiciona o feedback verbose que mostra o processo em tempo real. O system prompt instrui o modelo a responder em italiano e a usar o contexto do documento.

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Substituir o conteúdo de `main.py`**

```python
# main.py

# importa il client ufficiale di Groq
from groq import Groq
# importa la funzione per leggere il file .env
from dotenv import load_dotenv
# importa il modulo per accedere alle variabili d'ambiente
import os

# importa le funzioni RAG dal nostro modulo rag.py
from rag import carregar_documento, criar_vector_store, buscar_contexto


# legge il file .env e carica le variabili nell'ambiente
load_dotenv()
# recupera la chiave API dal file .env
api_key = os.getenv("groq_api_key")
# crea il client Groq usando la chiave API
client = Groq(api_key=api_key)


def chat(historico):
    """
    Envia o histórico completo ao Groq e devolve a resposta.
    Igual ao main.py original — não muda nada aqui.
    """
    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=historico,
    )
    return resposta.choices[0].message.content


def indexar_documento():
    """
    Pergunta ao utilizador o caminho do documento,
    carrega-o e cria o vector store.
    
    Devolve o vector store pronto para pesquisa, ou None se o utilizador
    não quiser carregar documento.
    """
    print("\n=== Chatbot con RAG ===\n")
    escolha = input("Vuoi caricare un documento? (s/n): ").strip().lower()

    if escolha != "s":
        print("\nModalità chatbot normale attivata.\n")
        return None

    caminho = input("Percorso del documento: ").strip()

    # PASSO 1: Leitura
    print("\n[1/4] Lettura del documento...")
    try:
        docs = carregar_documento(caminho)
    except FileNotFoundError as e:
        print(f"      ✗ Errore: {e}")
        return None
    except ValueError as e:
        print(f"      ✗ Errore: {e}")
        return None

    # Conta páginas/secções encontradas
    print(f"      ✓ {len(docs)} sezione/i trovata/e")

    # PASSO 2: Chunking + Embeddings + FAISS (tudo dentro de criar_vector_store)
    print("\n[2/4] Divisione in chunks...")
    print("\n[3/4] Generazione degli embeddings (può richiedere un momento)...")
    print("\n[4/4] Indicizzazione in FAISS...")

    vector_store, n_chunks = criar_vector_store(docs)

    print(f"      ✓ {n_chunks} chunks indicizzati")
    print(f"      ✓ Base di conoscenza pronta!\n")
    print("Ora puoi fare domande sul documento.")
    print("Digita 'esci' per uscire.\n")
    print("─" * 50)

    return vector_store


def main():
    # Tenta indexar documento (devolve None se utilizador recusar)
    vector_store = indexar_documento()

    # System prompt: instrui o modelo a responder sempre em italiano
    # e a usar o contexto do documento quando disponível
    system_prompt = (
        "Sei un assistente utile. Rispondi sempre in italiano. "
        "Quando viene fornito un contesto dal documento, basati su di esso "
        "per rispondere. Se la risposta non si trova nel documento, dillo "
        "chiaramente all'utente."
    )

    # Histórico começa com o system prompt
    # O system prompt não aparece no chat — é uma instrução "invisível" para o modelo
    historico = [{"role": "system", "content": system_prompt}]

    # Ciclo principal do chatbot
    while True:
        mensagem = input("\nUser: ")

        if mensagem.lower() in ("esci", "sair", "exit"):
            print("Arrivederci!")
            break

        # Se há vector store carregado, usa RAG
        if vector_store is not None:
            print("\n[RAG] Ricerca chunks rilevanti...")

            contexto, resultados = buscar_contexto(vector_store, mensagem)

            # Mostra os chunks encontrados (feedback educacional)
            for i, (doc, score) in enumerate(resultados, 1):
                # score é distância L2 — convertemos para "similaridade" visual
                # (valores menores = mais similar, então invertemos para exibição)
                preview = doc.page_content[:60].replace("\n", " ")
                print(f"      → Chunk {i} (score: {score:.2f}): \"{preview}...\"")

            # Monta a mensagem com contexto para o LLM
            # O contexto é injectado DENTRO da mensagem do utilizador
            mensagem_com_contexto = (
                f"Contesto dal documento:\n---\n{contexto}\n---\n\n"
                f"Domanda: {mensagem}"
            )
            historico.append({"role": "user", "content": mensagem_com_contexto})
        else:
            # Sem documento — chatbot normal
            historico.append({"role": "user", "content": mensagem})

        # Envia ao Groq e obtém resposta
        conteudo = chat(historico)

        # Adiciona resposta ao histórico
        # Nota: guardamos a resposta limpa (sem o contexto injectado)
        historico.append({"role": "assistant", "content": conteudo})

        print(f"\nBot: {conteudo}")


# Ponto de entrada do programa
if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Testar manualmente com um ficheiro .txt de teste**

Cria um ficheiro `teste.txt` na pasta do projecto:

```
Settimana 08 - Documento di test

L'azienda si chiama W Tech.
Il CEO è Marco Rossi.
Il prodotto principale è un software di gestione aziendale.
L'ufficio si trova a Milano, in Via Roma 42.
L'azienda ha 200 dipendenti.
Il fatturato annuo è di 5 milioni di euro.
```

Depois executa:

```bash
cd "/Users/tanara/dev/pessoal/AI/settimana 08"
python main.py
```

Fluxo esperado:
```
=== Chatbot con RAG ===

Vuoi caricare un documento? (s/n): s
Percorso del documento: teste.txt

[1/4] Lettura del documento...
      ✓ 1 sezione/i trovata/e

[2/4] Divisione in chunks...

[3/4] Generazione degli embeddings (può richiedere un momento)...

[4/4] Indicizzazione in FAISS...
      ✓ 3 chunks indicizzati
      ✓ Base di conoscenza pronta!

User: Chi è il CEO?

[RAG] Ricerca chunks rilevanti...
      → Chunk 1 (score: 0.45): "Settimana 08 - Documento di test L'azienda si..."
      → Chunk 2 (score: 0.67): "Il CEO è Marco Rossi. Il prodotto principale..."
      → Chunk 3 (score: 0.89): "L'ufficio si trova a Milano..."

Bot: Il CEO dell'azienda è Marco Rossi.
```

- [ ] **Step 3: Executar todos os testes para confirmar que nada quebrou**

```bash
pytest tests/test_rag.py -v
```

Esperado: todos PASSED

- [ ] **Step 4: Commit final**

```bash
git add main.py
git commit -m "feat: integra RAG no main.py com verbose output e system prompt italiano"
```

---

## Verificação final

Após todos os tasks, o projecto deve ter:

- `rag.py` com 3 funções: `carregar_documento`, `criar_vector_store`, `buscar_contexto`
- `tests/test_rag.py` com 6 testes todos a passar
- `main.py` com fluxo RAG completo, verbose output e chatbot em italiano
- 4 commits com mensagens descritivas

Para testar o modo sem documento:
```bash
python main.py
# Vuoi caricare un documento? (s/n): n
# → chatbot normal em italiano
```
