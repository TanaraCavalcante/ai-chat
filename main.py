# main.py
#
# Chatbot com suporte a RAG (Retrieval-Augmented Generation).
#
# Uso:
#   python main.py              → chatbot normal em italiano
#   python main.py relatorio.pdf → chatbot com RAG usando o documento
#
# Quando um documento é fornecido:
#   - as respostas baseiam-se exclusivamente no conteúdo do documento
#   - se a resposta não constar no documento, o bot informa o utilizador

import os
import sys

from groq import Groq
from dotenv import load_dotenv

from rag import carregar_documento, criar_vector_store, buscar_contexto


# ── Configuração inicial ───────────────────────────────────────────────────────

# Lê o ficheiro .env e carrega as variáveis de ambiente
load_dotenv()

# Inicializa o cliente Groq com a chave API do .env
client = Groq(api_key=os.getenv("groq_api_key"))


# ── Funções auxiliares ─────────────────────────────────────────────────────────

def indexar_documento(caminho: str):
    """
    Lê o documento e cria o vector store com feedback visual.

    Mostra o progresso em 4 passos para que o utilizador perceba
    o que está a acontecer em cada fase do processo RAG.

    Parâmetros:
      caminho : caminho para o ficheiro (.txt, .pdf, .docx)

    Devolve:
      FAISS vector store pronto para pesquisa, ou None em caso de erro.
    """
    print(f"\n[1/4] Leitura do documento '{os.path.basename(caminho)}'...")

    try:
        docs = carregar_documento(caminho)
    except FileNotFoundError as e:
        print(f"      ✗ Erro: {e}")
        return None
    except ValueError as e:
        print(f"      ✗ Erro: {e}")
        return None

    print(f"      ✓ {len(docs)} secção(ões) encontrada(s)")
    print("\n[2/4] Divisão em chunks...")
    print("[3/4] Geração dos embeddings (pode demorar um momento)...")
    print("[4/4] Indexação no FAISS...")

    # criar_vector_store faz os 3 passos internamente: chunking, embeddings, FAISS
    vector_store, n_chunks = criar_vector_store(docs)

    print(f"      ✓ {n_chunks} chunks indexados")
    print("      ✓ Base de conhecimento pronta!\n")

    return vector_store


def construir_mensagem_com_contexto(pergunta: str, contexto: str) -> str:
    """
    Monta a mensagem que será enviada ao LLM quando há documento carregado.

    O contexto é injectado antes da pergunta para que o modelo saiba
    exactamente em que informação deve basear a resposta.

    Parâmetros:
      pergunta : texto original do utilizador
      contexto : chunks relevantes concatenados (saída de buscar_contexto)

    Devolve:
      String formatada com contexto + pergunta
    """
    return (
        f"Contesto dal documento:\n---\n{contexto}\n---\n\n"
        f"Domanda: {pergunta}"
    )


def chat(historico: list) -> str:
    """
    Envia o histórico completo ao Groq e devolve o texto da resposta.

    O histórico contém todas as mensagens da conversa (system, user, assistant),
    o que permite ao modelo manter contexto entre turnos.

    Parâmetros:
      historico : lista de dicionários {"role": ..., "content": ...}

    Devolve:
      Texto da resposta do modelo
    """
    resposta = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=historico,
    )
    return resposta.choices[0].message.content


# ── Ponto de entrada ───────────────────────────────────────────────────────────

def main():
    # Verifica se o utilizador passou um documento como argumento
    # Exemplo: python main.py relatorio.pdf
    caminho_documento = sys.argv[1] if len(sys.argv) > 1 else None

    vector_store = None

    if caminho_documento:
        # Modo RAG: indexa o documento antes de iniciar o chat
        vector_store = indexar_documento(caminho_documento)
        if vector_store is None:
            # Erro ao carregar o documento — termina o programa
            sys.exit(1)

        print("Puoi fare domande sul documento. Scrivi 'esci' per uscire.\n")
        print("─" * 50)

        # System prompt restritivo: responde apenas com base no documento
        system_prompt = (
            "Sei un assistente utile. Rispondi sempre in italiano. "
            "Rispondi esclusivamente in base al contesto fornito dal documento. "
            "Se la risposta non è presente nel documento, rispondi esattamente: "
            "'Non è presente nel documento una risposta alla domanda posta.'"
        )
    else:
        # Modo normal: chatbot em italiano sem documento
        print("\n=== Chatbot ===")
        print("Scrivi 'esci' per uscire.\n")

        # System prompt aberto: responde em italiano sobre qualquer tema
        system_prompt = (
            "Sei un assistente utile. Rispondi sempre in italiano."
        )

    # O histórico começa com o system prompt (instrução invisível para o modelo)
    historico = [{"role": "system", "content": system_prompt}]

    # ── Ciclo principal do chatbot ─────────────────────────────────────────
    while True:
        mensagem = input("\nUser: ").strip()

        if not mensagem:
            continue

        if mensagem.lower() in ("esci", "sair", "exit"):
            print("Arrivederci!")
            break

        if vector_store is not None:
            # Modo RAG: busca os chunks mais relevantes para a pergunta
            print("\n[RAG] Ricerca chunks rilevanti...")
            contexto, resultados = buscar_contexto(vector_store, mensagem)

            # Mostra os chunks encontrados com o respectivo score de similaridade
            for i, (doc, score) in enumerate(resultados, 1):
                # score é distância L2 — menor = mais similar
                preview = doc.page_content[:60].replace("\n", " ")
                print(f"      → Chunk {i} (score: {score:.2f}): \"{preview}...\"")

            # Injeta o contexto dentro da mensagem do utilizador
            mensagem_para_llm = construir_mensagem_com_contexto(mensagem, contexto)
            historico.append({"role": "user", "content": mensagem_para_llm})
        else:
            # Modo normal: envia a mensagem directamente
            historico.append({"role": "user", "content": mensagem})

        # Envia ao Groq e obtém a resposta
        resposta = chat(historico)

        # Guarda a resposta limpa no histórico (sem o contexto injectado)
        historico.append({"role": "assistant", "content": resposta})

        print(f"\nBot: {resposta}")


if __name__ == "__main__":
    main()
