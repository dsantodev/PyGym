import streamlit as st
from pathlib import Path
from engine import QuizEngine
from datetime import datetime
from uuid import uuid4
from supabase import create_client
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

# ---------------------------------------------------------------------------
# CLIENT SUPABASE CON LE CREDENZIALI CARICATE DA .streamlit/secrets.toml
# ---------------------------------------------------------------------------


@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

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
        "result_saved":   False,
        "save_celebration_pending": False,
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


@st.dialog("Conferma abbandono quiz")
def confirm_abandon_quiz_dialog():
    st.write("Se abbandoni ora, i progressi del quiz in corso verranno persi.")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("❌ Abbandona Quiz", type="secondary", use_container_width=True):
            engine = get_engine()
            engine.reset()
            st.session_state.quiz_results = None
            st.session_state.last_answer = None
            st.session_state.answered = False
            st.session_state.result_saved = False
            st.session_state.save_celebration_pending = False
            st.session_state.phase = "home"
            st.rerun()
    with col_no:
        if st.button("✅ Continua", type="secondary", use_container_width=True):
            st.rerun()

# ----------------------------------------------------------------------------
# PAGINE
# ----------------------------------------------------------------------------


def page_home():
    """
    Pagina iniziale: immagine + messaggio di benvenuto.
    """
    if COVER_IMAGE.exists():
        # per rimuovere padding e margini attorno all'immagine
        load_css("styles.css")
        st.image(str(COVER_IMAGE), use_container_width=True)
    else:
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
            st.session_state.result_saved = False
            st.session_state.save_celebration_pending = False
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Visualizza la classifica")
        if st.button("🏆 Classifica", use_container_width=True, type="secondary"):
            st.session_state.phase = "leaderboard"
            st.rerun()


def page_config():
    """
    Pagina configurazione: l'utente sceglie difficoltà, categorie
    e il numero di domande totali da includere nel quiz.
    """
    engine = get_engine()

    with st.sidebar:
        st.title("🏋️ PyGym")

        st.divider()

        # --- Info punteggio ---
        st.info(
            "💡 **Sistema di punteggio**  \n\n"
            "• Domanda facile = 1 punto  \n"
            "• Domanda media = 2 punti  \n"
            "• Domanda difficile = 3 punti  \n\n"
            "✅ Se rispondi correttamente, guadagni i punti della domanda  \n"
            "❌ Se sbagli, nessuna penalità, l’obiettivo è imparare.\n"
        )
        st.divider()
        st.header("Configura il tuo quiz")

        # --- Selezione difficoltà ---
        difficulty_map = {
            "Tutte le difficoltà": None,
            "Facile (1 pt)": 1,
            "Media (2 pt)": 2,
            "Difficile (3 pt)": 3,
        }
        diff_label = st.radio(
            "🎯 Difficoltà",
            options=list(difficulty_map.keys()),
            index=0,
        )
        selected_difficulty = difficulty_map[diff_label]

        # --- Multiselect categorie (filtrate per difficoltà) ---
        categories = engine.get_categories(difficulty=selected_difficulty)
        cat_labels = [
            f"{c['name']} - ({c['question_count']})" for c in categories]
        label_to_id = {
            f"{c['name']} - ({c['question_count']})": c["id"]
            for c in categories
        }

        selected_labels = st.multiselect(
            "📚 Categorie",
            options=cat_labels,
            default=[],
            placeholder="Scegli una o più categorie...",
            key=f"cats_{selected_difficulty}",
        )

        # Ricava la lista di category_id dalle etichette selezionate
        selected_ids = [label_to_id[lbl] for lbl in selected_labels]

        # --- Numero di domande con +/− ---
        max_q = 0
        if selected_ids:
            min_q = len(selected_ids)
            max_q = engine.get_max_questions_for(
                selected_ids, difficulty=selected_difficulty)
            default_q = max(min_q, min(5, max_q))

            num_q = int(st.number_input(
                "🔢 Numero di domande",
                min_value=min_q,
                value=default_q,
                step=1,
                help=(
                    f"Minimo(1 per categoria) · "
                    f"Massimo(tutte le domande disponibili)"
                ),
            ))
            if num_q > max_q:
                st.error(f"Il valore deve essere ≤ {max_q} (domande disponibili)")
            else:
                st.info(
                    f"Minimo {min_q} domande (1 per categoria) · Massimo {max_q} domande")
        else:
            num_q = 0
            st.number_input(
                "🔢 Numero di domande",
                min_value=0,
                max_value=1,
                value=0,
                step=1,
                disabled=True,
                help="Seleziona almeno una categoria per abilitare questo campo",
            )

        st.divider()

        # --- Bottone avvia ---
        avvia_disabled = len(selected_ids) == 0 or (bool(selected_ids) and num_q > max_q)
        if st.button("▶ Avvia Quiz", use_container_width=True,
                     type="primary",
                     disabled=avvia_disabled):
            st.session_state.category_ids = selected_ids
            st.session_state.num_questions = num_q
            st.session_state.quiz_results = None
            st.session_state.result_saved = False
            st.session_state.save_celebration_pending = False

            # Avvia il quiz nell'engine con la lista di categorie
            engine.start_quiz(selected_ids, num_q,
                              difficulty=selected_difficulty)

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
        st.markdown(
            "### Stai Configurando il Quiz... Le singole categorie contengono varie domande:")
        st.markdown("<br>", unsafe_allow_html=True)
        max_cols_per_row = 4
        cat_info_map = {c["id"]: c for c in categories}
        for i in range(0, len(selected_ids), max_cols_per_row):
            row_ids = selected_ids[i:i + max_cols_per_row]
            cols = st.columns(len(row_ids), gap="xsmall")
            for col, cat_id in zip(cols, row_ids):
                cat = cat_info_map[cat_id]
                with col:
                    st.metric(
                        label=cat["description"],
                        value=f"{cat['name']}",
                        delta=f"{cat['question_count']}",
                        border=False,
                    )
                    st.markdown("\n---\n")


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
            st.success(f"✅ Risposta corretta!  Vale **+{ua.points} pt**")
        else:
            correct_text = next(
                a.text for a in display_question.answers if a.is_correct
            )
            st.error(
                f"👉 Hai risposto: `{ua.chosen_text}`  \n"
                f"❌ Risposta sbagliata.  **{ua.points} pt**  \n"
                f"💡 La risposta corretta era: `{correct_text}`"
            )

        with st.expander("📖 Spiegazione e esempio di codice"):
            st.markdown(ua.question.explanation)
            if ua.question.code_example:
                st.code(ua.question.code_example, language="python")

        st.divider()

        # Label dinamico del bottone dipende se il quiz è finito o no
        # se siamo alla fine, mostriamo "Vedi risultati", altrimenti "Prossima domanda"
        all_answered = engine.is_finished()
        label = "📊 Vedi i risultati" if all_answered else "➡️ Prossima domanda"

        _, col_next, col_abandon, _ = st.columns([2, 1, 1, 2])

        with col_next:
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

        with col_abandon:
            if st.button("⚠️ Abbandona", type="secondary"):
                confirm_abandon_quiz_dialog()


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
        if st.button(
            "💾 Salva",
            type="primary",
            disabled=not nome.strip() or st.session_state.result_saved,
        ):
            # Salva il risultato SOLO se non è già stato salvato in questa sessione
            if not st.session_state.result_saved:
                _save_result(nome.strip(), results)
                st.session_state.result_saved = True
                st.session_state.save_celebration_pending = True
                st.rerun()

    if st.session_state.result_saved:
        if st.session_state.save_celebration_pending:
            st.balloons()
            st.session_state.save_celebration_pending = False
        st.success("✅ Punteggio salvato con successo! 🎉")

    st.markdown("<br>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🔁 Nuovo Quiz", use_container_width=True):
            engine = get_engine()
            engine.reset()
            st.session_state.quiz_results = None
            st.session_state.result_saved = False
            st.session_state.save_celebration_pending = False
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

        # KPI sintetici per leggere la classifica a colpo d'occhio
        total_quiz = len(records_sorted)
        unique_players = len({r["name"] for r in records_sorted})
        avg_score = round(sum(r["score"]
                          for r in records_sorted) / total_quiz, 2)
        avg_percentage = round(
            sum(float(r["percentage"]) for r in records_sorted) / total_quiz,
            1,
        )
        best = records_sorted[0]

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("👥 Giocatori", unique_players)
        kpi2.metric("🧩 Quiz completati", total_quiz)
        kpi3.metric("📈 Media punteggio", avg_score)
        kpi4.metric("🎯 Media %", f"{avg_percentage}%")

        st.divider()

        st.success(
            f"Miglior risultato: **{best['name']}** con "
            f"**{best['score']} pt** ({best['percentage']}%)"
        )

        table_rows = []
        for rank, r in enumerate(records_sorted, start=1):
            medal = {1: "🥇",
                     2: "🥈",
                     3: "🥉",
                     4: "🐍",
                     5: "🐼",
                     6: "🐘",
                     7: "🦎",
                     8: "🐢",
                     9: "🐜",
                     10: "🐣", }.get(rank, "🥚")
            table_rows.append(
                {
                    "Pos": rank,
                    "Podio": medal,
                    "Nome": r["name"],
                    "Punteggio": r["score"],
                    "Max": r["max_score"],
                    "%": float(r["percentage"]),
                    "Corrette": r["correct"],
                    "Sbagliate": r["wrong"],
                    "Categorie": r["categories"],
                    "Data": r["date"],
                }
            )

        st.subheader("Classifica completa")
        st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pos": st.column_config.NumberColumn(width="small"),
                "Podio": st.column_config.TextColumn(width="small"),
                "Nome": st.column_config.TextColumn(width="medium"),
                "Punteggio": st.column_config.NumberColumn(format="%d pt"),
                "Max": st.column_config.NumberColumn(format="%d pt"),
                "%": st.column_config.NumberColumn(format="%.1f%%"),
                "Corrette": st.column_config.NumberColumn(width="small"),
                "Sbagliate": st.column_config.NumberColumn(width="small"),
                "Categorie": st.column_config.TextColumn(width="large"),
                "Data": st.column_config.TextColumn(width="medium"),
            },
        )

    if st.button("← Torna alla Home"):
        st.session_state.phase = "home"
        st.rerun()


# ---------------------------------------------------------------------------
# FUNZIONI DI SUPPORTO PER LA CLASSIFICA - CON SALVATAGGIO SU SUPABASE
# ---------------------------------------------------------------------------

def _save_result(name: str, results: dict):
    """
    Salva un risultato nella tabella Supabase 'results'.
    """
    new_record = {
        "id":         uuid4().hex,
        "name":       name,
        "score":      results["score"],
        "max_score":  results["max_score"],
        "percentage": results["percentage"],
        "correct":    results["correct"],
        "wrong":      results["wrong"],
        "categories": ", ".join(
            get_engine().categories.get(cid, {}).get("name", cid)
            for cid in st.session_state.get("category_ids", [])
        ) or "N/A",
        "date":       datetime.now().strftime("%d/%m/%Y %H:%M"),
        "saved_at":   datetime.now().isoformat(timespec="seconds"),
    }
    get_supabase().table("results").insert(new_record).execute()


def _load_results() -> list[dict]:
    """
    Legge tutti i risultati dalla tabella Supabase 'results'.
    """
    response = get_supabase().table("results").select("*").execute()
    return response.data or []


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
main()
