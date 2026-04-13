# rag.py
#
# Módulo com as funções de RAG (Retrieval-Augmented Generation).
# Responsável por: carregar documentos, criar o vector store e buscar contexto.
#
# Funções exportadas:
#   - carregar_documento(caminho)      → lista de Documents
#   - criar_vector_store(docs)         → (FAISS store, n_chunks)
#   - buscar_contexto(store, pergunta) → (texto_contexto, resultados_com_score)

import os

from langchain_community.document_loaders import (
    TextLoader,      # lê ficheiros .txt
    PyPDFLoader,     # lê ficheiros .pdf (uma página = um Document)
    Docx2txtLoader,  # lê ficheiros .docx
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


# ─────────────────────────────────────────────
# FUNÇÃO 1: Carregar documento
# ─────────────────────────────────────────────

def carregar_documento(caminho: str) -> list:
    """
    Lê um documento e devolve uma lista de objectos Document do LangChain.

    Cada Document contém:
      - page_content : o texto da página ou secção
      - metadata     : informação extra (ex: número de página, caminho do ficheiro)

    Suporta: .txt · .pdf · .docx

    Parâmetros:
      caminho : caminho completo para o ficheiro

    Devolve:
      Lista de Document objects

    Lança:
      FileNotFoundError : se o ficheiro não existir
      ValueError        : se a extensão não for suportada
    """
    # Verifica se o ficheiro existe antes de tentar abri-lo
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Ficheiro não encontrado: {caminho}")

    # Extrai a extensão em minúsculas (ex: ".pdf")
    extensao = os.path.splitext(caminho)[1].lower()

    # Selecciona o Loader adequado conforme a extensão
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
    return loader.load()


# ─────────────────────────────────────────────
# FUNÇÃO 2: Criar vector store
# ─────────────────────────────────────────────

def criar_vector_store(docs: list, chunk_size: int = 500, chunk_overlap: int = 50):
    """
    Transforma uma lista de Documents num vector store pesquisável (FAISS).

    O processo tem 3 passos:
      1. Chunking   — divide o texto em pedaços de ~chunk_size caracteres,
                      com chunk_overlap de sobreposição para não perder
                      contexto nas bordas entre chunks
      2. Embeddings — converte cada chunk num vector de ~384 números usando
                      o modelo 'all-MiniLM-L6-v2' (leve, multilíngue, local)
      3. FAISS      — indexa os vectores para permitir busca por similaridade

    Parâmetros:
      docs         : lista de Documents (saída de carregar_documento)
      chunk_size   : tamanho máximo de cada chunk em caracteres (padrão: 500)
      chunk_overlap: sobreposição entre chunks consecutivos (padrão: 50)

    Devolve:
      (vector_store, n_chunks) onde:
        vector_store : índice FAISS pronto para pesquisa
        n_chunks     : número de chunks gerados (útil para o verbose output)
    """
    # ── PASSO 1: CHUNKING ──────────────────────────────────────────────────
    # RecursiveCharacterTextSplitter divide o texto de forma inteligente:
    # tenta primeiro por parágrafos (\n\n), depois por linhas (\n),
    # depois por frases, e por último por palavras.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    # ── PASSO 2: EMBEDDINGS ────────────────────────────────────────────────
    # Carrega o modelo localmente (sem necessidade de API key).
    # Na primeira execução, faz download do modelo (~80 MB) para cache.
    modelo_embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # ── PASSO 3: FAISS ─────────────────────────────────────────────────────
    # from_documents() faz o embed de cada chunk e armazena no índice FAISS.
    vector_store = FAISS.from_documents(chunks, modelo_embeddings)

    return vector_store, len(chunks)


# ─────────────────────────────────────────────
# FUNÇÃO 3: Buscar contexto
# ─────────────────────────────────────────────

def buscar_contexto(vector_store, pergunta: str, k: int = 3):
    """
    Busca os chunks mais relevantes para a pergunta dada.

    Como funciona:
      1. Converte a pergunta num vector usando o mesmo modelo de embedding
      2. Calcula a distância L2 entre o vector da pergunta e todos os chunks
      3. Devolve os k chunks com menor distância (= maior similaridade)

    Parâmetros:
      vector_store : índice FAISS criado por criar_vector_store()
      pergunta     : texto da pergunta do utilizador
      k            : número de chunks a devolver (padrão: 3)

    Devolve:
      contexto   (str)  : texto dos chunks concatenados, para enviar ao LLM
      resultados (list) : lista de (Document, score) para o verbose output
                          — score é distância L2: quanto menor, mais similar
    """
    # similarity_search_with_score devolve lista de (Document, score)
    resultados = vector_store.similarity_search_with_score(pergunta, k=k)

    # Concatena o texto de cada chunk com um separador visual
    textos = [doc.page_content for doc, score in resultados]
    contexto = "\n---\n".join(textos)

    return contexto, resultados
