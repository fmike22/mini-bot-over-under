import streamlit as st

st.set_page_config(page_title="Mini bot Over / Under", layout="wide")

def format_eur(x):
    return f"{x:.2f} €"

def format_pct(x):
    return f"{x:.2f} %"

if "historique" not in st.session_state:
    st.session_state.historique = []
if "bankroll_depart" not in st.session_state:
    st.session_state.bankroll_depart = 100.0

st.title("Mini bot Over / Under")
st.subheader("Saisie du dernier pari")

with st.sidebar:
    st.header("Paramètres")

    bankroll_initiale = st.number_input(
        "Bankroll initiale",
        min_value=0.0,
        value=float(st.session_state.bankroll_depart),
        step=1.0
    )

    mise_minimum = st.number_input(
        "Mise minimum",
        min_value=0.0,
        value=0.20,
        step=0.10
    )

    st.divider()
    st.subheader("Infos instantanées")

    nb_paris = len(st.session_state.historique)
    gains = sum(p["gain"] for p in st.session_state.historique)
    pertes = sum(p["perte"] for p in st.session_state.historique)

    bankroll_actuelle = bankroll_initiale + gains - pertes
    profit = bankroll_actuelle - bankroll_initiale
    roi = (profit / bankroll_initiale * 100) if bankroll_initiale > 0 else 0.0

    nb_over = sum(1 for p in st.session_state.historique if p["resultat"] == "OVER")
    taux_over = (nb_over / nb_paris * 100) if nb_paris > 0 else 0.0

    pertes_consecutives = 0
    for p in reversed(st.session_state.historique):
        if p["resultat"] == "UNDER":
            pertes_consecutives += 1
        else:
            break

    st.metric("Bankroll instantané", format_eur(bankroll_actuelle))
    st.metric("Profit cumulé", format_eur(profit))
    st.metric("ROI global", format_pct(roi))
    st.metric("Taux Over", format_pct(taux_over))
    st.metric("Pertes consécutives", pertes_consecutives)

    st.divider()
    st.subheader("Dernier pari")

    cote_over = st.number_input("Cote Over", min_value=1.0, value=1.90, step=0.01, format="%.2f")
    cote_under = st.number_input("Cote Under", min_value=1.0, value=1.90, step=0.01, format="%.2f")
    resultat = st.selectbox("Résultat", ["OVER", "UNDER"])
    apport_bankroll = st.number_input("Apport bankroll", min_value=0.0, value=0.0, step=0.10, format="%.2f")
    retrait_bankroll = st.number_input("Retrait bankroll", min_value=0.0, value=0.0, step=0.10, format="%.2f")

if "cote_over" not in st.session_state:
    st.session_state.cote_over = 1.90
if "cote_under" not in st.session_state:
    st.session_state.cote_under = 1.90

col1, col2 = st.columns(2)
with col1:
    st.text_input("Cote Over", value=f"{cote_over:.2f}", disabled=True)
with col2:
    st.text_input("Cote Under", value=f"{cote_under:.2f}", disabled=True)

if st.button("Calculer le prochain pari"):
    mise_base = max(mise_minimum, bankroll_actuelle * 0.02)
    if resultat == "OVER":
        gain = mise_base * (cote_over - 1)
        perte = 0.0
    else:
        gain = 0.0
        perte = mise_base

    bankroll_actuelle = bankroll_actuelle + apport_bankroll - retrait_bankroll + gain - perte

    st.session_state.historique.append({
        "resultat": resultat,
        "gain": gain,
        "perte": perte
    })

    st.session_state.bankroll_depart = bankroll_initiale

    st.success("Calcul effectué.")
    st.info(f"Mise conseillée: {format_eur(mise_base)}")
    st.write(f"Bankroll estimée: {format_eur(bankroll_actuelle)}")

st.divider()
st.subheader("Historique")
if st.session_state.historique:
    for i, p in enumerate(reversed(st.session_state.historique[-10:]), start=1):
        st.write(
            f"{i}. {p['resultat']} — gain: {format_eur(p['gain'])} — perte: {format_eur(p['perte'])}"
        )
else:
    st.write("Aucun pari enregistré.")
