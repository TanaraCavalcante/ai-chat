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


def test_remove_doc_sessao_inexistente(client):
    """Deve retornar 404 se session_id não existir."""
    response = client.post('/api/remove-doc', json={'session_id': 'nao-existe', 'doc_id': 'qualquer'})
    assert response.status_code == 404
    assert 'Sessione non trovata' in response.get_json()['error']


def test_remove_doc_fluxo_completo(client, tmp_path):
    """Deve remover um documento da sessione e ricalcolare l'indice senza di esso."""
    ficheiro = tmp_path / "doc.txt"
    ficheiro.write_text("Questo e un documento di test per la rimozione.")

    with open(ficheiro, 'rb') as f:
        upload_resp = client.post('/api/upload', data={'file': (f, 'doc.txt')})
    upload_data = upload_resp.get_json()
    session_id = upload_data['session_id']
    doc_id = upload_data['doc_id']

    remove_resp = client.post('/api/remove-doc', json={'session_id': session_id, 'doc_id': doc_id})
    assert remove_resp.status_code == 200
    assert remove_resp.get_json()['ok'] is True
    assert remove_resp.get_json()['total_docs'] == 0

    # Sessione svuotata: una nuova chat deve restituire 404
    chat_resp = client.post('/api/chat', json={'session_id': session_id, 'pergunta': 'Ciao'})
    assert chat_resp.status_code == 404


def test_remove_doc_id_inesistente(client, tmp_path):
    """Deve retornar 404 se il doc_id non esiste nella sessione."""
    ficheiro = tmp_path / "doc.txt"
    ficheiro.write_text("Contenuto di test.")

    with open(ficheiro, 'rb') as f:
        upload_resp = client.post('/api/upload', data={'file': (f, 'doc.txt')})
    session_id = upload_resp.get_json()['session_id']

    response = client.post('/api/remove-doc', json={'session_id': session_id, 'doc_id': 'doc-id-fake'})
    assert response.status_code == 404
    assert 'Documento non trovato' in response.get_json()['error']
