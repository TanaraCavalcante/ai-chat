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
