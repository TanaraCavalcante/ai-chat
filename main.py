# importa il client ufficiale di Groq
from groq import Groq
# importa la funzione per leggere il file .env
from dotenv import load_dotenv
# importa il modulo per accedere alle variabili d'ambiente
import os


# legge il file .env e carica le variabili nell'ambiente
load_dotenv()
# recupera la chiave API dal file .env
api_key = os.getenv("groq_api_key")
# crea il client Groq usando la chiave API
client = Groq(api_key=api_key)

# lista che memorizza tutta la conversazione
historico = []

# ciclo principale del chatbot
while True:
    # legge il messaggio dell'utente dal terminale
    mensagem = input("User: ")
    
    # se l'utente scrive 'sair', termina il programma
    if mensagem.lower() == "sair":
        break
    
    # aggiunge il messaggio dell'utente alla cronologia
    historico.append({"role": "user", "content": mensagem})

     # invia tutta la cronologia all'API di Groq e ottiene una risposta
    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # il modello AI da usare
        messages=historico,      # envia todo o histórico, não só a última mensagem
    )

    # extrai il testo della risposta
    conteudo = resposta.choices[0].message.content

    # aggiunge la risposta del bot alla cronologia
    historico.append({"role": "assistant", "content": conteudo})

    #mostra la risposta nel terminale 
    print(f"Bot: {conteudo}")

