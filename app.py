import streamlit as st
from pathlib import Path
from engine import QuizEngine
import json
from datetime import datetime
# ---------------------------------------------------------------------------
# CONFIGURAZIONE PAGINA
# Deve essere la PRIMA chiamata Streamlit in assoluto
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PyGym",
    page_icon="🏋️",
    layout="wide"
)

# ---------------------------------------------------------------------------
# PERCORSI
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
COVER_IMAGE = ASSETS_DIR / "cover_image.png"
QUESTIONS_FILE = DATA_DIR / "questions.json"
RESULTS_FILE = DATA_DIR / "results.json"

# ---------------------------------------------------------------------------
# CARICAMENTO CSS PER LA COVER IMG
# ---------------------------------------------------------------------------


def load_css(file_name: str):
    css_path = BASE_DIR / file_name
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# INIZIALIZZAZIONE SESSION_STATE
# ---------------------------------------------------------------------------


def init_session_state():
    """
    Chiavi e significati:
    phase           → quale pagina mostrare 
    engine          → istanza di QuizEngine (caricata una sola volta)
    category_id     → categoria scelta dall'utente nella config
    num_questions   → numero domande scelto nella config
    last_answer     → UserAnswer dell'ultima risposta (per mostrare feedback)
    answered        → True se l'utente ha già risposto alla domanda corrente
                    (serve per bloccare il tasto e mostrare spiegazione)
    quiz_results    → dizionario risultati finali (da engine.get_results())
    """
    defaults = {
        "phase":          "home",  # (home/config/quiz/result/leaderboard)
        "engine":         None,
        "category_ids":   [],       # lista di category_id selezionati
        "num_questions":  5,
        "last_answer":    None,
        "answered":       False,
        "quiz_results":   None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_engine() -> QuizEngine:
    """
    Restituisce l'istanza di QuizEngine, creandola se non esiste.
    Salvandola nel session_state, il JSON viene letto una volta sola.
    """
    if st.session_state.engine is None:
        st.session_state.engine = QuizEngine(str(QUESTIONS_FILE))
    return st.session_state.engine


# ---------------------------------------------------------------------------
# PAGINE
# ---------------------------------------------------------------------------
def page_home():
    """
    Pagina iniziale: immagine + messaggio di benvenuto.
    """
    # Immagine di copertina a tutta larghezza
    if COVER_IMAGE.exists():
        # per rimuovere padding e margini attorno all'immagine
        load_css("styles.css")
        st.image(str(COVER_IMAGE), use_container_width=True)
    else:
        # Placeholder testuale se l'immagine non c'è ancora
        st.markdown(
            """
            <div style='text-align:center; padding: 60px 0'>
                <h1 style='font-size: 4rem'>🏋️ PyGym</h1>
                <p style='font-size: 1.4rem; color: gray'>
                    Allenati ogni giorno con Python
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.title("🏋️ PyGym")
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Inizia il tuo allenamento")

        if st.button("🚀 Inizia il Quiz", use_container_width=True, type="primary"):
            st.session_state.phase = "config"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Visualizza la classifica")
        if st.button("🏆 Classifica", use_container_width=True, type="secondary"):
            st.session_state.phase = "leaderboard"
            st.rerun()


def page_config():
    """
    Pagina configurazione: l'utente sceglie una o più categorie
    e il numero di domande totali da includere nel quiz.

    Logica dello slider:
      - minimo = numero di categorie selezionate (almeno 1 per categoria)
      - massimo = somma delle domande disponibili nelle categorie selezionate
      - se non è selezionata nessuna categoria, lo slider è disabilitato
    """
    engine = get_engine()
    categories = engine.get_categories()

    with st.sidebar:
        st.title("🏋️ PyGym")
        st.divider()
        st.markdown("### Configura il quiz")

        # --- Multiselect categorie ---
        cat_labels = [
            f"{c['name']} - ({c['question_count']})" for c in categories]
        label_to_id = {
            f"{c['name']} - ({c['question_count']})": c["id"]
            for c in categories
        }

        selected_labels = st.multiselect(
            "📚 Categorie",
            options=cat_labels,
            default=[],           # nessuna pre-selezionata: l'utente sceglie
            placeholder="Scegli una o più categorie...",
        )

        # Ricava la lista di category_id dalle etichette selezionate
        selected_ids = [label_to_id[lbl] for lbl in selected_labels]

        # --- Slider dinamico ---
        # Il range dipende dalle categorie scelte:
        #   min = 1 per ogni categoria selezionata (es. 3 categorie → min=3)
        #   max = totale domande disponibili nelle categorie scelte
        if selected_ids:
            min_q = len(selected_ids)
            max_q = engine.get_max_questions_for(selected_ids)

            # Calcola un default sensato: 5 domande o il max disponibile
            # ma comunque non meno del minimo richiesto
            default_q = max(min_q, min(5, max_q))

            num_q = st.slider(
                "🔢 Numero di domande",
                min_value=min_q,
                max_value=max_q,
                value=default_q,
                help=(
                    f"Minimo {min_q} (1 per categoria) · "
                    f"Massimo {max_q} (tutte le domande disponibili)"
                ),
            )

            # Riepilogo visivo di quante domande per categoria
            st.caption("📊 Distribuzione stimata:")
            total_avail = engine.get_max_questions_for(selected_ids)
            for cat_id in selected_ids:
                cat_name = next(c["name"]
                                for c in categories if c["id"] == cat_id)
                cat_size = engine.get_question_count(cat_id)
                # Stima proporzionale (la stessa logica dell'engine)
                estimated = max(1, round(num_q * cat_size / total_avail))
                st.caption(f"  • {cat_name}: ~{estimated} domande")

        else:
            # Nessuna categoria selezionata: slider placeholder disabilitato
            num_q = 0
            st.slider(
                "🔢 Numero di domande",
                min_value=0,
                max_value=1,
                value=0,
                disabled=True,
                help="Seleziona almeno una categoria per abilitare lo slider",
            )

        st.divider()

        # --- Info punteggio ---
        st.info(
            "💡 **Punteggio:**  \n"
            "✅ Corretta → **+difficoltà** pt  \n"
            "❌ Sbagliata → **-difficoltà** pt  \n"
            "_(difficoltà da 1 a 3)_"
        )

        st.divider()

        # --- Bottone avvia ---
        avvia_disabled = len(selected_ids) == 0
        if st.button(
            "▶ Avvia Quiz",
            use_container_width=True,
            type="primary",
            disabled=avvia_disabled,
        ):
            st.session_state.category_ids = selected_ids
            st.session_state.num_questions = num_q

            # Avvia il quiz nell'engine con la lista di categorie
            engine.start_quiz(selected_ids, num_q)

            # Reset stato risposta per la pagina quiz
            st.session_state.last_answer = None
            st.session_state.answered = False
            st.session_state.phase = "quiz"
            st.rerun()

        if st.button("← Home", use_container_width=True):
            st.session_state.phase = "home"
            st.rerun()

    # --- Area principale: istruzioni / anteprima ---
    st.title("🏋️ PyGym")
    st.markdown("*Allenati ogni giorno con Python*")
    st.divider()

    if not selected_ids:
        st.info("👈 Seleziona almeno una categoria dalla sidebar per iniziare.")
    else:
        # Mostra un riepilogo delle categorie scelte
        st.markdown("## Stai Configurando il Quiz...")
        st.markdown("### Le singole categorie contengono varie domande:")
        cols = st.columns(len(selected_ids), gap="xsmall")
        for col, cat_id in zip(cols, selected_ids):
            cat = next(c for c in categories if c["id"] == cat_id)
            with col:
                st.metric(
                    label=cat["description"],
                    value=f"{cat['name']}",
                    delta=f"{cat['question_count']}",
                    border=True,
                )


def page_quiz():

    engine = get_engine()

    question = engine.current_question()

    if question is None and not st.session_state.answered:
        # Se il quiz è finito e siamo finiti su page_quiz (es. reload), passa
        # alla pagina risultati se possibile, altrimenti torna alla config.
        if st.session_state.quiz_results is not None:
            st.session_state.phase = "result"
        elif engine.is_finished():
            st.session_state.quiz_results = engine.get_results()
            st.session_state.phase = "result"
        else:
            st.session_state.phase = "config"
        st.rerun()

    # --- Header con progresso ---
    current, total = engine.progress()
    st.markdown(f"### Domanda {current} di {total}")
    st.progress(current / total)

    difficulty_labels = {1: "🟢 Facile", 2: "🟡 Medio", 3: "🔴 Difficile"}

    # Quando siamo in RERUN B dopo l'ultima domanda, question è None
    # ma last_answer conserva la domanda appena risposta — la usiamo.
    display_question = question or (
        st.session_state.last_answer.question
        if st.session_state.last_answer else None
    )

    if display_question is None:
        st.session_state.phase = "config"
        st.rerun()

    st.markdown(
        f"**{difficulty_labels.get(display_question.difficulty, '')}** — "
        f"vale **{display_question.difficulty} pt**"
    )
    st.divider()

    # --- Testo della domanda ---
    st.markdown(f"#### {display_question.text}")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Bottoni risposta ---
    for i, ans in enumerate(display_question.answers):
        if st.button(
            ans.text,
            key=f"answer_{i}",
            disabled=st.session_state.answered,
            use_container_width=True,
        ):
            # salva risposta, NON avanza indice
            ua = engine.answer(i)
            st.session_state.last_answer = ua
            st.session_state.answered = True
            st.rerun()

    # --- Feedback  ---
    if st.session_state.answered and st.session_state.last_answer:
        ua = st.session_state.last_answer

        if ua.is_correct:
            st.success(f"✅ Risposta corretta!  **+{ua.points} pt**")
        else:
            correct_text = next(
                a.text for a in display_question.answers if a.is_correct
            )
            st.error(
                f"❌ Risposta sbagliata.  **{ua.points} pt**  \n"
                f"La risposta corretta era: **{correct_text}**"
            )

        with st.expander("📖 Spiegazione e esempio di codice"):
            st.markdown(ua.question.explanation)
            if ua.question.code_example:
                st.code(ua.question.code_example, language="python")

        st.divider()

        # Label dinamico del bottone dipende se il quiz è finito o no
        # se siamo alla fine, mostriamo "Vedi risultati", altrimenti "Prossima domanda"
        all_answered = engine.is_finished() or (
            st.session_state.answered and current == total
        )
        label = "📊 Vedi i risultati" if all_answered else "➡️ Prossima domanda"

        if st.button(label, type="primary"):
            if all_answered:
                # Raccoglie i risultati PRIMA di resettare lo stato
                st.session_state.quiz_results = engine.get_results()
                st.session_state.phase = "result"
            else:
                # avanza l'indice nell'engine
                engine.next_question()

            # Reset stato risposta per la prossima domanda (o per la pagina result)
            st.session_state.last_answer = None
            st.session_state.answered = False
            st.rerun()


def page_result():
    """
    Pagina risultati: mostra il riepilogo finale e permette di salvare il punteggio.
    """
    results = st.session_state.quiz_results

    if results is None:
        st.session_state.phase = "home"
        st.rerun()

    st.title("📊 Risultati")
    st.divider()

    # --- Metriche principali ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Corrette",   results["correct"])
    col2.metric("❌ Sbagliate",  results["wrong"])
    col3.metric("🏆 Punteggio",
                f"{results['score']} / {results['max_score']} pt")
    col4.metric("📈 Percentuale", f"{results['percentage']}%")

    st.divider()

    # --- Riepilogo domanda per domanda ---
    st.markdown("#### Dettaglio risposte")
    for ua in results["answers"]:
        icon = "✅" if ua.is_correct else "❌"
        delta = f"+{ua.points}" if ua.points > 0 else str(ua.points)
        with st.expander(f"{icon} {ua.question.text[:60]}...  ({delta} pt)"):
            chosen = ua.chosen_text
            correct = next(a.text for a in ua.question.answers if a.is_correct)
            st.markdown(f"**La tua risposta:** {chosen}")
            if not ua.is_correct:
                st.markdown(f"**Risposta corretta:** {correct}")
            st.markdown(f"**Spiegazione:** {ua.question.explanation}")
            if ua.question.code_example:
                st.code(ua.question.code_example, language="python")

    st.divider()

    # --- Salvataggio in classifica ---
    st.markdown("#### 💾 Salva il tuo punteggio")
    nome = st.text_input("Il tuo nome o nickname", placeholder="es. Mario")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Salva", type="primary", disabled=not nome.strip()):
            _save_result(nome.strip(), results)
            st.success(f"Punteggio di **{nome}** salvato! 🎉")

    st.markdown("<br>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🔁 Nuovo Quiz", use_container_width=True):
            engine = get_engine()
            engine.reset()
            st.session_state.quiz_results = None
            st.session_state.phase = "config"
            st.rerun()
    with col4:
        if st.button("🏆 Classifica", use_container_width=True):
            st.session_state.phase = "leaderboard"
            st.rerun()


def page_leaderboard():
    """
    Pagina classifica: legge results.json e mostra la top 10.
    """
    st.title("🏆 Classifica")
    st.divider()

    records = _load_results()

    if not records:
        st.info(
            "Nessun punteggio salvato ancora. Completa un quiz per essere il primo!")
    else:
        # Ordina per punteggio decrescente, poi per percentuale
        records_sorted = sorted(
            records,
            key=lambda r: (r["score"], r["percentage"]),
            reverse=True,
        )

        # Mostra top 10
        for rank, r in enumerate(records_sorted[:10], start=1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
            st.markdown(
                f"{medal} **{r['name']}** — "
                f"{r['score']} pt ({r['percentage']}%)  "
                f"· {r['category']} · {r['date']}"
            )
            st.divider()

    if st.button("← Torna alla Home"):
        st.session_state.phase = "home"
        st.rerun()


# ---------------------------------------------------------------------------
# FUNZIONI DI SUPPORTO PER LA CLASSIFICA
# ---------------------------------------------------------------------------

def _save_result(name: str, results: dict):
    """
    Aggiunge un risultato al file results.json.
    Se il file non esiste, lo crea.

    Formato di ogni record:
    {
        "name":       "Mario",
        "score":      7,
        "max_score":  10,
        "percentage": 80.0,
        "correct":    4,
        "wrong":      1,
        "category":   "basi",
        "date":       "2024-03-15 14:32"
    }
    """

    # Leggi records esistenti (o lista vuota se il file non esiste)
    records = _load_results()

    # Crea il nuovo record
    new_record = {
        "name":       name,
        "score":      results["score"],
        "max_score":  results["max_score"],
        "percentage": results["percentage"],
        "correct":    results["correct"],
        "wrong":      results["wrong"],
        "category":   ", ".join(st.session_state.get("category_ids", [])) or "N/A",
        "date":       datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    records.append(new_record)

    # Salva su file (crea la directory se non esiste)
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def _load_results() -> list[dict]:
    """
    Legge results.json e restituisce la lista dei record.
    Restituisce lista vuota se il file non esiste o è corrotto.
    """
    import json

    if not RESULTS_FILE.exists():
        return []
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


# ---------------------------------------------------------------------------
# ROUTER PRINCIPALE
# ---------------------------------------------------------------------------

def main():
    """
    Punto di ingresso dell'app.
    Inizializza lo stato e instrada verso la pagina corretta.
    """
    init_session_state()

    # Mappa fase -> funzione di pagina
    pages = {
        "home":        page_home,
        "config":      page_config,
        "quiz":        page_quiz,
        "result":      page_result,
        "leaderboard": page_leaderboard,
    }

    # Recupera e chiama la funzione della pagina corrente
    current_phase = st.session_state.phase
    page_fn = pages.get(current_phase, page_home)
    page_fn()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__" or True:
    # Il 'or True' serve perché Streamlit non esegue il blocco __main__
    # nel modo classico; con questa forma il main() viene sempre chiamato
    main()
