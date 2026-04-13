# tests/test_rag.py
#
# Testes para as funções do módulo rag.py.
# Executar com: pytest tests/test_rag.py -v

import os
import sys
import pytest

# Adiciona a pasta raiz ao path para que o Python encontre o rag.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document

from rag import carregar_documento, criar_vector_store, buscar_contexto


# ─────────────────────────────────────────────
# Testes de carregar_documento
# ─────────────────────────────────────────────

def test_carrega_txt(tmp_path):
    """Deve carregar um ficheiro .txt e devolver pelo menos um Document."""
    ficheiro = tmp_path / "teste.txt"
    ficheiro.write_text("Este é o conteúdo do teste.", encoding="utf-8")

    docs = carregar_documento(str(ficheiro))

    assert len(docs) >= 1
    assert "Este é o conteúdo do teste." in docs[0].page_content


def test_ficheiro_nao_existe():
    """Deve lançar FileNotFoundError quando o caminho não existe."""
    with pytest.raises(FileNotFoundError):
        carregar_documento("ficheiro_que_nao_existe.txt")


def test_formato_nao_suportado(tmp_path):
    """Deve lançar ValueError para extensões não suportadas."""
    ficheiro = tmp_path / "teste.xlsx"
    ficheiro.write_text("conteudo")

    with pytest.raises(ValueError):
        carregar_documento(str(ficheiro))


# ─────────────────────────────────────────────
# Testes de criar_vector_store
# ─────────────────────────────────────────────

def test_cria_vector_store():
    """Deve criar um FAISS store a partir de uma lista de Documents."""
    docs = [
        Document(page_content="O gato está no jardim."),
        Document(page_content="O cão ladra à noite."),
        Document(page_content="A empresa foi fundada em 1990."),
    ]

    store, n_chunks = criar_vector_store(docs)

    # O store deve ser criado com sucesso
    assert store is not None
    # Deve ter gerado pelo menos um chunk
    assert n_chunks >= 1


def test_vector_store_busca_relevante():
    """O chunk mais relevante para a pergunta deve ser retornado primeiro."""
    docs = [
        Document(page_content="O produto custa 50 euros."),
        Document(page_content="A reunião é às 15h."),
        Document(page_content="O relatório tem 10 páginas."),
    ]

    store, _ = criar_vector_store(docs)

    # Pergunta sobre preço — deve encontrar o chunk sobre "50 euros"
    resultados = store.similarity_search("quanto custa?", k=1)
    assert "50 euros" in resultados[0].page_content


# ─────────────────────────────────────────────
# Testes de buscar_contexto
# ─────────────────────────────────────────────

def test_busca_contexto_devolve_texto_e_scores():
    """Deve devolver o contexto como string e a lista de resultados com score."""
    docs = [
        Document(page_content="O CEO da empresa chama-se Marco Rossi."),
        Document(page_content="O escritório fica em Milão."),
        Document(page_content="A empresa tem 200 funcionários."),
        Document(page_content="O produto principal é um software de gestão."),
    ]

    store, _ = criar_vector_store(docs)
    contexto, resultados = buscar_contexto(store, "Quem é o director?")

    # Deve devolver uma string não vazia
    assert isinstance(contexto, str)
    assert len(contexto) > 0

    # Deve devolver lista de (Document, score)
    assert len(resultados) > 0

    # O chunk mais relevante deve mencionar o CEO
    assert "Marco Rossi" in contexto
