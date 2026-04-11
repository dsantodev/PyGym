![Schermata_di_Configurazione](https://github.com/user-attachments/assets/83c8af7d-931e-4efd-99da-612397ad9341)
![quiz_in_azione_2](https://github.com/user-attachments/assets/8333dbb7-72dd-478e-ac8d-fbeabff9eefe)
![quiz_in_azione_1](https://github.com/user-attachments/assets/10c73a13-3e84-4553-864f-c1ef503044fb)
![pagina_risultati](https://github.com/user-attachments/assets/356a36a9-d53d-49d6-bbb3-880c755ea995)
# 🏋️ PyGym

> **Allenati ogni giorno con Python**

PyGym non è un semplice quiz a risposta multipla: è uno strumento pensato per lo **studio e il ripasso attivo** di Python. Dopo ogni risposta — giusta o sbagliata — viene mostrata la risposta corretta, una spiegazione testuale e un **esempio di codice funzionante**, così ogni sessione diventa un'occasione per imparare davvero.

---

## Funzionalità principali

### Modalità studio/ripasso

A differenza di un quiz classico, PyGym mostra sempre il feedback completo dopo ogni risposta:

- ✅ Se hai risposto **correttamente**: conferma e punti guadagnati
- ❌ Se hai risposto **sbagliando**: evidenzia la tua risposta, indica quella corretta
- 📖 In entrambi i casi si apre un expander con **spiegazione + esempio di codice Python**

Questo approccio permette di usare PyGym sia come test che come strumento di ripasso guidato.

### Categorie disponibili

Le domande sono organizzate in 10 categorie indipendenti:

| Categoria             | Argomenti                                   |
| --------------------- | ------------------------------------------- |
| Basi del linguaggio   | Tipi di dati, operatori, variabili          |
| Stringhe & Metodi     | Metodi, formattazione, slicing              |
| Liste                 | Metodi, comprehension, slicing              |
| Dizionari             | Accesso, iterazione, metodi                 |
| Tuple                 | Immutabilità, unpacking                    |
| Set e FrozenSet       | Operazioni insiemistiche, metodi            |
| OOP                   | Classi, ereditarietà, metodi speciali      |
| Funzioni avanzate     | Lambda, decoratori, generatori, closures    |
| Gestione degli errori | Try/except, eccezioni personalizzate, raise |
| Moduli standard       | os, sys, json, pathlib, datetime, logging   |

### Configurazione del quiz

Prima di ogni sessione è possibile scegliere:

- **Una o più categorie** da includere nel quiz
- **Numero di domande** tramite uno slider dinamico (min: 1 per categoria, max: tutte le domande disponibili)

Le domande vengono distribuite proporzionalmente tra le categorie selezionate e mescolate casualmente.

### Sistema di punteggio

Il punteggio dipende dalla difficoltà della domanda:

| Difficoltà  | Risposta corretta | Risposta sbagliata |
| ------------ | ----------------- | ------------------ |
| 🟢 Facile    | +1 pt             | 0 pt               |
| 🟡 Medio     | +2 pt             | 0 pt               |
| 🔴 Difficile | +3 pt             | 0 pt               |

### Risultati e riepilogo

Al termine del quiz viene mostrata una pagina riassuntiva con:

- Numero di risposte corrette e sbagliate
- Punteggio ottenuto sul punteggio massimo possibile
- Percentuale di successo
- Dettaglio domanda per domanda (con spiegazione e codice per ogni risposta)

### Classifica globale

I punteggi possono essere salvati con un nickname. La classifica mostra:

- Posizione con medaglie (🥇🥈🥉)
- Punteggio, percentuale, risposte corrette/sbagliate
- Categorie affrontate e data del quiz
- KPI aggregati: giocatori totali, quiz completati, media punteggio

---

## Provalo subito

L'app è online e pronta all'uso, non serve installare nulla:

**[quizpygym.streamlit.app](https://quizpygym.streamlit.app/)**
