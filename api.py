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
        model="openai/gpt-oss-120b",
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
    app.run(port=5001, debug=False)
