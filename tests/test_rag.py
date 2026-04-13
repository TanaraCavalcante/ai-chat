# tests/test_rag.py
#
# Testes para as funções do módulo rag.py.
# Executar com: pytest tests/test_rag.py -v

import os
import sys
import pytest

# Adiciona a pasta raiz ao path para que o Python encontre o rag.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import carregar_documento


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
