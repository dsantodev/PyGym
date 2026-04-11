

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
| Tuple                 | Immutabilità, unpacking                     |
| Set e FrozenSet       | Operazioni insiemistiche, metodi            |
| OOP                   | Classi, ereditarietà, metodi speciali       |
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

| Difficoltà   | Risposta corretta | Risposta sbagliata |
| ------------ | ----------------- | ------------------ |
| 🟢 Facile    | +1 pt             | 0 pt               |
| 🟡 Medio     | +2 pt             | 0 pt               |
| 🔴 Difficile | +3 pt             | 0 pt               |

### Quiz in azione

Seleziona una risposta e ricevi subito il feedback: se hai sbagliato viene mostrata la risposta corretta. In entrambi i casi puoi aprire la spiegazione con l'esempio di codice.

### Risultati e classifica

Al termine del quiz viene mostrata una pagina riassuntiva con punteggio, percentuale e dettaglio domanda per domanda. Puoi salvare il risultato con un nickname e consultare la classifica globale.

--- 

## Video della Schermata iniziale e configurazione del PyQuiz:

![Schermata_di_Configurazione](https://github.com/user-attachments/assets/2d6b3c11-8364-45c0-9506-c4c518dfe05b)

--- 

## Video del PyQuiz in azione:

![quiz_in_azione_2](https://github.com/user-attachments/assets/53a29476-f5d3-4b41-9790-a3f68fac9dd3)

![quiz_in_azione_1](https://github.com/user-attachments/assets/d545c480-91a1-4b7f-9650-e1c7773ff3aa)

---

## Video della pagina dei Risultati e Classifica:

![pagina_risultati](https://github.com/user-attachments/assets/2ba5aa6f-8e15-4345-a32f-1015d3e1399a)

---

## Provalo subito

L'app è online e pronta all'uso, non serve installare nulla:

**[quizpygym.streamlit.app](https://quizpygym.streamlit.app/)**
