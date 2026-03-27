import json
import random
from dataclasses import dataclass, field
from typing import Optional
from copy import deepcopy

# ---------------------------------------------------------------------------
# DATACLASS: rappresenta una singola risposta
# ---------------------------------------------------------------------------
# Un dataclass è come una classe normale ma pensata per contenere dati.
# Python genera automaticamente __init__, __repr__ ecc.


@dataclass
class Answer:
    text: str           # testo della risposta, es. "<class 'float'>"
    is_correct: bool    # True se è la risposta corretta


# ---------------------------------------------------------------------------
# DATACLASS: rappresenta una domanda completa
# ---------------------------------------------------------------------------
@dataclass
class Question:
    id: str                         # es. "basi_001"
    category_id: str                # es. "basi"
    text: str                       # testo della domanda
    difficulty: int                 # 1, 2 o 3
    answers: list[Answer]           # lista di oggetti Answer
    explanation: str                # spiegazione mostrata dopo la risposta
    code_example: str               # codice di esempio


# ---------------------------------------------------------------------------
# DATACLASS: tiene traccia di una risposta data dall'utente durante il quiz
# ---------------------------------------------------------------------------
@dataclass
class UserAnswer:
    question: Question      # la domanda a cui ha risposto
    # indice della risposta scelta (0-3) DOPO il mescolamento
    chosen_index: int
    # testo della risposta scelta (robusto al mescolamento)
    chosen_text: str
    is_correct: bool        # True se ha risposto correttamente
    # punti guadagnati/persi (+difficoltà o -difficoltà)
    points: int


# ---------------------------------------------------------------------------
# CLASSE PRINCIPALE: QuizEngine
# ---------------------------------------------------------------------------
class QuizEngine:
    """
    Gestisce tutta la logica del quiz.

    Flusso di utilizzo:
    1. engine = QuizEngine("questions.json")
    2. engine.start_quiz(category_id, num_questions)
    3. while not engine.is_finished():
           q = engine.current_question()
           engine.answer(chosen_index)
    4. results = engine.get_results()
    """

    def __init__(self, json_path: str):
        """
        Carica il file JSON e prepara le strutture dati interne.

        Args:
            json_path: percorso al file questions.json
        """
        self.json_path = json_path

        # Dizionario {category_id -> dict con nome e description}
        # es. {"basi": {"id": "basi", "name": "Basi ...", ...}, ...}
        self.categories: dict[str, dict] = {}

        # Dizionario {category_id -> lista di oggetti Question}
        # es. {"basi": [Question(...), Question(...), ...], ...}
        self.questions_by_category: dict[str, list[Question]] = {}

        # --- Stato del quiz in corso ---
        # domande selezionate per il quiz
        self._quiz_questions: list[Question] = []
        self._current_index: int = 0                # indice domanda corrente
        self._user_answers: list[UserAnswer] = []   # risposte dell'utente
        self._quiz_active: bool = False             # True se il quiz è in corso

        # Carica i dati dal JSON
        self._load_data()

    # -----------------------------------------------------------------------
    # METODI PRIVATI (uso interno, convenzione: nome inizia con _)
    # -----------------------------------------------------------------------

    def _load_data(self):
        """
        Legge il file JSON e popola self.categories e self.questions_by_category.
        Ogni domanda viene convertita in un oggetto Question (con oggetti Answer dentro).
        """
        with open(self.json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)  # raw è un dizionario Python

        # 1) Carica le categorie in un dizionario indicizzato per id
        for cat in raw["categories"]:
            self.categories[cat["id"]] = cat
            # inizializza lista vuota
            self.questions_by_category[cat["id"]] = []

        # 2) Carica le domande e le converte in oggetti Question
        for q_raw in raw["questions"]:

            # Converte ogni risposta da dict a oggetto Answer
            answers = [
                Answer(text=a["text"], is_correct=a["is_correct"])
                for a in q_raw["answers"]
            ]

            # Crea l'oggetto Question
            question = Question(
                id=q_raw["id"],
                category_id=q_raw["category_id"],
                text=q_raw["text"],
                difficulty=q_raw["difficulty"],
                answers=answers,
                explanation=q_raw["explanation"],
                code_example=q_raw["code_example"],
            )

            # Inserisce la domanda nel bucket della sua categoria
            self.questions_by_category[question.category_id].append(question)

    # -----------------------------------------------------------------------
    # METODI PUBBLICI - INFORMAZIONI SUL CATALOGO
    # -----------------------------------------------------------------------

    def get_categories(self) -> list[dict]:
        """
        Restituisce la lista delle categorie come lista di dizionari.
        Aggiunge anche il conteggio delle domande disponibili per ciascuna.

        Returns:
            Lista di dict con chiavi: id, name, description, question_count

        Esempio di output:
            [{"id": "basi", "name": "Basi ...", "description": "...", "question_count": 8}, ...]
        """
        result = []
        for cat_id, cat_info in self.categories.items():
            result.append({
                # copia tutte le chiavi originali (id, name, description)
                **cat_info,
                "question_count": len(self.questions_by_category[cat_id])
            })
        return result

    def get_question_count(self, category_id: str) -> int:
        """
        Restituisce il numero di domande disponibili per una categoria.

        Args:
            category_id: es. "basi"

        Returns:
            Numero intero di domande, 0 se la categoria non esiste
        """
        return len(self.questions_by_category.get(category_id, []))

    def get_max_questions_for(self, category_ids: list[str]) -> int:
        """
        Restituisce il numero massimo di domande selezionabili
        data una lista di categorie (somma delle domande disponibili).

        Esempio: ["basi", "oop"] → 8 + 6 = 14

        Args:
            category_ids: lista di id categoria, es. ["basi", "oop"]

        Returns:
            Somma delle domande disponibili in tutte le categorie richieste
        """
        return sum(
            len(self.questions_by_category.get(cat_id, []))
            for cat_id in category_ids
        )

    def get_total_questions(self) -> int:
        """Restituisce il numero totale di domande in tutto il JSON."""
        return sum(len(qs) for qs in self.questions_by_category.values())

    # -----------------------------------------------------------------------
    # METODI PUBBLICI - GESTIONE DEL QUIZ
    # -----------------------------------------------------------------------

    def start_quiz(self, category_ids: list[str], num_questions: int):
        """
        Avvia un nuovo quiz multi-categoria.

        Seleziona num_questions domande pescando proporzionalmente
        da ogni categoria nella lista category_ids, poi mescola tutto.

        Esempio con category_ids=["basi","oop"] e num_questions=7:
          basi ha 8 domande  → peso 8/(8+6) ≈ 57% → 4 domande
          oop  ha 6 domande  → peso 6/(8+6) ≈ 43% → 3 domande
          totale: 4+3 = 7 ✓

        La distribuzione proporzionale garantisce che ogni categoria
        sia rappresentata in modo equo rispetto alla sua dimensione.
        Ogni categoria contribuisce con ALMENO 1 domanda.

        Args:
            category_ids:  lista di id categoria, es. ["basi", "oop"]
            num_questions: numero totale di domande nel quiz

        Raises:
            ValueError: se una categoria non esiste, la lista è vuota,
                        o num_questions è fuori dal range valido
        """
        # --- Validazioni ---
        if not category_ids:
            raise ValueError("Seleziona almeno una categoria.")

        for cat_id in category_ids:
            if cat_id not in self.questions_by_category:
                raise ValueError(f"Categoria '{cat_id}' non trovata.")

        min_q = len(category_ids)           # almeno 1 per categoria
        max_q = self.get_max_questions_for(category_ids)

        if num_questions < min_q:
            raise ValueError(
                f"Con {len(category_ids)} categorie servono almeno {min_q} domande "
                f"(1 per categoria)."
            )
        if num_questions > max_q:
            raise ValueError(
                f"Richieste {num_questions} domande ma le categorie scelte "
                f"ne hanno solo {max_q} in totale."
            )

        # --- Distribuzione proporzionale ---
        # Calcola quante domande prendere da ogni categoria.
        #
        # Algoritmo "largest remainder":
        #   1. Calcola la quota ideale (float) per ogni categoria
        #   2. Assegna la parte intera a ciascuna (floor)
        #   3. I posti rimanenti vanno alle categorie con il resto più alto
        #
        # Questo garantisce che la somma sia esattamente num_questions
        # e che ogni categoria abbia almeno 1 domanda.

        sizes = {
            cat_id: len(self.questions_by_category[cat_id])
            for cat_id in category_ids
        }
        total_available = sum(sizes.values())

        # Quote ideali (float)
        ideal = {
            cat_id: num_questions * size / total_available
            for cat_id, size in sizes.items()
        }

        # Parte intera (floor), minimo 1 per categoria
        allocation = {cat_id: max(1, int(q)) for cat_id, q in ideal.items()}

        # Correzione: aggiusta il totale se non corrisponde a num_questions
        # (causato dall'arrotondamento verso il basso)
        diff = num_questions - sum(allocation.values())

        if diff > 0:
            # Ordina per resto decrescente e distribuisce i posti rimasti
            remainders = sorted(
                category_ids,
                key=lambda c: ideal[c] - int(ideal[c]),
                reverse=True,
            )
            for i in range(diff):
                cat_to_bump = remainders[i % len(remainders)]
                # Non superare il numero di domande disponibili
                if allocation[cat_to_bump] < sizes[cat_to_bump]:
                    allocation[cat_to_bump] += 1

        elif diff < 0:
            # Raro ma possibile: riduci le categorie con più domande
            for cat_id in sorted(category_ids, key=lambda c: allocation[c], reverse=True):
                if diff == 0:
                    break
                if allocation[cat_id] > 1:
                    allocation[cat_id] -= 1
                    diff += 1

        # --- Selezione casuale per ogni categoria ---
        selected: list[Question] = []
        for cat_id, n in allocation.items():
            available = self.questions_by_category[cat_id]
            # random.sample non modifica la lista originale
            selected.extend(random.sample(available, n))

        # Mescola le domande di tutte le categorie insieme
        random.shuffle(selected)

        # Mescola le risposte di ogni domanda.
        # Usiamo deepcopy per non modificare le domande originali in
        # self.questions_by_category — così ogni quiz riparte da zero.

        shuffled: list[Question] = []
        for q in selected:
            q_copy = deepcopy(q)
            random.shuffle(q_copy.answers)
            shuffled.append(q_copy)

        self._quiz_questions = shuffled

        # Reset stato
        self._current_index = 0
        self._user_answers = []
        self._quiz_active = True

    def current_question(self) -> Optional[Question]:
        """
        Restituisce la domanda corrente del quiz.

        Returns:
            Oggetto Question, oppure None se il quiz è finito o non avviato
        """
        if not self._quiz_active or self.is_finished():
            return None
        return self._quiz_questions[self._current_index]

    def answer(self, chosen_index: int) -> UserAnswer:
        """
        Registra la risposta dell'utente alla domanda corrente.
        NON avanza all'indice successivo: serve chiamare next_question()
        esplicitamente quando si vuole procedere.

        Questo è il motivo della separazione:
          - answer()        → salva la risposta, rimane sulla domanda corrente
          - next_question() → avanza all'indice successivo

        In Streamlit, tra answer() e next_question() c'è un intero rerun:
          1. utente clicca risposta  → answer() salva, rerun
          2. Streamlit mostra feedback (answered=True, indice fermo)
          3. utente clicca "Continua" → next_question(), rerun
          4. Streamlit mostra la domanda successiva

        Senza questa separazione, al punto 2 l'indice sarebbe già avanzato
        e Streamlit mostrerebbe contemporaneamente feedback E domanda successiva.

        Args:
            chosen_index: indice (0-3) della risposta scelta dall'utente

        Returns:
            Oggetto UserAnswer con is_correct e points calcolati

        Raises:
            RuntimeError: se non c'è un quiz attivo o è già finito
            IndexError: se chosen_index è fuori range
        """
        if not self._quiz_active or self.is_finished():
            raise RuntimeError("Nessun quiz attivo o quiz già terminato.")

        question = self.current_question()

        if chosen_index < 0 or chosen_index >= len(question.answers):
            raise IndexError(f"Indice risposta {chosen_index} non valido.")

        chosen_answer = question.answers[chosen_index]
        is_correct = chosen_answer.is_correct

        # Calcolo punti:
        # corretta  → +difficulty  (es. difficoltà 3 → +3 pt)
        # sbagliata → -difficulty  (es. difficoltà 3 → -3 pt)
        points = question.difficulty if is_correct else -question.difficulty

        user_answer = UserAnswer(
            question=question,
            chosen_index=chosen_index,
            chosen_text=chosen_answer.text,
            is_correct=is_correct,
            points=points,
        )

        self._user_answers.append(user_answer)
        # NON incrementiamo _current_index qui — lo fa next_question()

        return user_answer

    def next_question(self):
        """
        Avanza alla domanda successiva.
        Da chiamare DOPO aver mostrato il feedback all'utente (answered=True)
        e DOPO che l'utente ha cliccato "Continua" / "Prossima domanda".

        Raises:
            RuntimeError: se non c'è una risposta registrata per la domanda corrente
        """
        # Sicurezza: verifica che la domanda corrente sia già stata risposta
        # confrontando il numero di risposte salvate con l'indice corrente
        if len(self._user_answers) <= self._current_index:
            raise RuntimeError(
                "Rispondi prima alla domanda corrente prima di avanzare."
            )
        self._current_index += 1

    def is_finished(self) -> bool:
        """
        Restituisce True se tutte le domande del quiz sono state risposte
        E l'utente ha già avanzato oltre l'ultima (next_question() chiamato).

        Tecnicamente: finito quando _current_index >= numero totale domande.
        """
        return self._current_index >= len(self._quiz_questions)

    def progress(self) -> tuple[int, int]:
        """
        Restituisce lo stato di avanzamento del quiz.

        Returns:
            Tupla (domanda_corrente, totale_domande)
            es. (3, 8) significa "sei alla domanda 3 di 8"

        Nota: usa _current_index + 1 per avere il numero human-friendly (parte da 1)
        """
        return (self._current_index + 1, len(self._quiz_questions))

    # -----------------------------------------------------------------------
    # METODI PUBBLICI - RISULTATI FINALI
    # -----------------------------------------------------------------------

    def get_results(self) -> dict:
        """
        Calcola e restituisce i risultati finali del quiz.
        Da chiamare solo quando is_finished() è True.

        Returns:
            Dizionario con tutte le statistiche del quiz:
            {
                "total_questions": int,
                "correct": int,
                "wrong": int,
                "score": int,          # punteggio netto (può essere negativo)
                "max_score": int,      # punteggio massimo ottenibile
                "percentage": float,   # % risposte corrette (0-100)
                "answers": list[UserAnswer]  # dettaglio ogni risposta
            }
        """
        correct = sum(1 for ua in self._user_answers if ua.is_correct)
        wrong = len(self._user_answers) - correct
        score = sum(ua.points for ua in self._user_answers)

        # Punteggio massimo = somma delle difficoltà di tutte le domande
        max_score = sum(q.difficulty for q in self._quiz_questions)

        # Percentuale di risposte corrette (evita divisione per zero)
        total = len(self._user_answers)
        percentage = (correct / total * 100) if total > 0 else 0.0

        return {
            "total_questions": total,
            "correct": correct,
            "wrong": wrong,
            "score": score,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "answers": self._user_answers,
        }

    def reset(self):
        """
        Resetta completamente lo stato del quiz.
        Utile per tornare alla schermata iniziale senza ricaricare il JSON.
        """
        self._quiz_questions = []
        self._current_index = 0
        self._user_answers = []
        self._quiz_active = False
