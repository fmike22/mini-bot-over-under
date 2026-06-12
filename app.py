import streamlit as st

st.set_page_config(page_title="Mini bot Over / Under", layout="wide")

def fmt_eur(x):
    return f"{x:.2f} €"

def fmt_pct(x):
    return f"{x:.2f} %"

def safe_div(a, b):
    return a / b if b not in (0, 0.0, None) else 0.0

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Mini bot Over / Under")
st.caption("Saisie du dernier pari + préparation du prochain pari")

with st.sidebar:
    st.header("Paramètres")

    bankroll_initiale = st.number_input(
        "Bankroll initiale",
        min_value=0.0,
        value=100.0,
        step=1.0,
        format="%.2f",
        key="bankroll_initiale",
    )

    mise_minimum = st.number_input(
        "Mise minimum",
        min_value=0.0,
        value=0.20,
        step=0.10,
        format="%.2f",
        key="mise_minimum",
    )

    st.divider()
    st.subheader("Dernier pari")

    cote_over_last = st.number_input(
        "Cote Over du dernier pari",
        min_value=1.0,
        value=1.90,
        step=0.01,
        format="%.2f",
        key="cote_over_last",
    )

    cote_under_last = st.number_input(
        "Cote Under du dernier pari",
        min_value=1.0,
        value=1.90,
        step=0.01,
        format="%.2f",
        key="cote_under_last",
    )

    resultat_last = st.selectbox(
        "Résultat du dernier pari",
        ["OVER", "UNDER"],
        key="resultat_last",
    )

    apport_bankroll = st.number_input(
        "Apport bankroll",
        min_value=0.0,
        value=0.0,
        step=0.10,
        format="%.2f",
        key="apport_bankroll",
    )

    retrait_bankroll = st.number_input(
        "Retrait bankroll",
        min_value=0.0,
        value=0.0,
        step=0.10,
        format="%.2f",
        key="retrait_bankroll",
    )

    st.divider()
    st.subheader("Prochain pari")

    cote_over_next = st.number_input(
        "Cote Over suivante",
        min_value=1.0,
        value=1.90,
        step=0.01,
        format="%.2f",
        key="cote_over_next",
    )

    cote_under_next = st.number_input(
        "Cote Under suivante",
        min_value=1.0,
        value=1.90,
        step=0.01,
        format="%.2f",
        key="cote_under_next",
    )

    st.divider()
    st.subheader("Infos instantanées")

    nb_paris = len(st.session_state.history)
    nb_over = sum(1 for p in st.session_state.history if p["resultat"] == "OVER")
    nb_under = sum(1 for p in st.session_state.history if p["resultat"] == "UNDER")
    gains = sum(p["gain"] for p in st.session_state.history)
    pertes = sum(p["perte"] for p in st.session_state.history)

    bankroll_actuelle = bankroll_initiale + gains - pertes + apport_bankroll - retrait_bankroll
    profit = bankroll_actuelle - bankroll_initiale
    roi = safe_div(profit, bankroll_initiale) * 100
    taux_over = safe_div(nb_over, nb_paris) * 100
    taux_under = safe_div(nb_under, nb_paris) * 100

    pertes_consecutives = 0
    for p in reversed(st.session_state.history):
        if p["resultat"] == "UNDER":
            pertes_consecutives += 1
        else:
            break

    st.metric("Bankroll instantané", fmt_eur(bankroll_actuelle))
    st.metric("Profit cumulé", fmt_eur(profit))
    st.metric("ROI global", fmt_pct(roi))
    st.metric("Taux Over", fmt_pct(taux_over))
    st.metric("Taux Under", fmt_pct(taux_under))
    st.metric("Pertes consécutives", pertes_consecutives)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Côtes du prochain pari")
    st.write(f"**Over suivant :** {cote_over_next:.2f}")
    st.write(f"**Under suivant :** {cote_under_next:.2f}")

with col2:
    st.subheader("Signal rapide")
    if cote_over_next > cote_under_next:
        st.success("Favori marché : UNDER")
    elif cote_under_next > cote_over_next:
        st.success("Favori marché : OVER")
    else:
        st.info("Marché équilibré")

st.divider()

mise_conseillee = max(mise_minimum, bankroll_actuelle * 0.02)

if st.button("Calculer le prochain pari"):
    if resultat_last == "OVER":
        gain = mise_conseillee * (cote_over_last - 1)
        perte = 0.0
    else:
        gain = 0.0
        perte = mise_conseillee

    bankroll_apres = bankroll_actuelle + gain - perte

    st.session_state.history.append(
        {
            "resultat": resultat_last,
            "gain": gain,
            "perte": perte,
            "bankroll_apres": bankroll_apres,
        }
    )

    st.success("Calcul effectué.")
    st.write(f"Mise conseillée : **{fmt_eur(mise_conseillee)}**")
    st.write(f"Bankroll estimée après pari : **{fmt_eur(bankroll_apres)}**")

st.subheader("Derniers calculs")
if st.session_state.history:
    for i, p in enumerate(reversed(st.session_state.history[-10:]), start=1):
        st.write(
            f"{i}. {p['resultat']} — gain: {fmt_eur(p['gain'])} — perte: {fmt_eur(p['perte'])} — bankroll après: {fmt_eur(p['bankroll_apres'])}"
        )
else:
    st.write("Aucun pari enregistré.")
