Necessario installare uv
- nel pc del lab conda init nella root del progetto e riavviare la shell
- sul portatile pip install uv 

Supponiamo di avere un dispositivo già connesso via mqtt a un broker.
Attacchiamo ditto al broker per ricevere i messaggi dal dispositivo.

docker compose up nella root a sua volta chiama il docker compose file della dir \ditto
vediamo tanti servizi coinvolti --> su docker hub abbiamo molte immagini per ditto
ditto è un microservizio che richiede un database mongoDB (nosql)

localhost:8080 

possiamo visualizzare un UI (dashboard) che una API doc

Consideriamo come PA un pump motor
Una "Thing" contiene 
un thingID che lo identifica univocamente
revision --> versione 
attributi : proprietà statiche 
feature : a sua volta composta da una lista di valori

es. motor
{
  "rpm": 0,
  "temperature_C": 20,
  "status": "stopped"
}

es. feature 
{
  "x_ms2": 0,
  "y_ms2": 0,
  "z_ms2": 0
}

facciamo partire le configurazioni tra 1 a 3 e poi runniamo il file python di mock
Dalla ui posso vedere la "storia" nel tempo

Finora abbiamo una connessione monodirezionale con la cosa.
Raccolgo dati e li visualizzo sulla web UI
A ogni dato raccolto, la versione si aggiorna
thing --> mqtt broker --> eclipse ditto

Ora vorremmo avere una comunicazione bi-direzionale col dispositivo

Proviamo ad aggiungere ora una nuova feature con nuove proprietà
script 04
e a creare una connessione bidirezionale
script 05

ora se faccio ri-runnare il dispositivo posso modificare la parte json della feature control e cambiare running in stopped