import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mini bot Over/Under", layout="centered")

st.title("Mini bot Over / Under")

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "cote_over", "cote_under", "resultat", "apport", "retrait"
    ])

if "bankroll_init" not in st.session_state:
    st.session_state.bankroll_init = 100.0

if "mise_min" not in st.session_state:
    st.session_state.mise_min = 0.10

st.sidebar.header("Paramètres")
st.session_state.bankroll_init = st.sidebar.number_input("Bankroll initiale", min_value=0.0, value=100.0, step=10.0)
st.session_state.mise_min = st.sidebar.number_input("Mise minimum", min_value=0.01, value=0.10, step=0.01)

st.subheader("Saisie du dernier pari")
c1, c2 = st.columns(2)
with c1:
    cote_over = st.number_input("Cote Over", min_value=1.01, value=1.90, step=0.01)
    resultat = st.selectbox("Résultat", ["OVER", "UNDER"])
with c2:
    cote_under = st.number_input("Cote Under", min_value=1.01, value=1.90, step=0.01)
    apport = st.number_input("Apport bankroll", min_value=0.0, value=0.0, step=10.0)

retrait = st.number_input("Retrait bankroll", min_value=0.0, value=0.0, step=10.0)

def calc_bankroll(df, bankroll_init):
    profit = 0
    for _, r in df.iterrows():
        stake = r["mise"]
        if r["resultat"] == "OVER":
            profit += stake * (r["cote_over"] - 1)
        else:
            profit -= stake
    bankroll = bankroll_init + df["apport"].sum() - df["retrait"].sum() + profit
    return max(bankroll, 0)

def risk_pct(bankroll):
    if bankroll < 100:
        return 0.01
    elif bankroll <= 200:
        return 0.0125
    return 0.015

def coeff_mise(avantage):
    if avantage > 0.05:
        return 1.50
    elif avantage >= 0.03:
        return 1.30
    elif avantage >= 0.01:
        return 1.10
    elif avantage >= -0.01:
        return 1.00
    elif avantage >= -0.03:
        return 0.70
    return 0.10

def score_confiance(ev, avantage, roi_roulant, pertes):
    s = 0
    if ev > 0:
        s += 40
    elif ev > -0.02:
        s += 20
    if avantage > 0:
        s += 30
    elif avantage > -0.02:
        s += 15
    if roi_roulant > 0:
        s += 20
    elif roi_roulant > -0.03:
        s += 10
    if pertes < 5:
        s += 10
    elif pertes == 5:
        s += 5
    return s

if st.button("Calculer le prochain pari"):
    new_row = pd.DataFrame([{
        "cote_over": cote_over,
        "cote_under": cote_under,
        "resultat": resultat,
        "apport": apport,
        "retrait": retrait
    }])

    df = pd.concat([st.session_state.history, new_row], ignore_index=True)

    bankroll = st.session_state.bankroll_init + df["apport"].sum() - df["retrait"].sum()
    profits = []
    bankrolls = []
    mises = []
    rois = []
    over_wins = 0
    pertes_cons = 0

    for i, r in df.iterrows():
        marge = (1/r["cote_over"]) + (1/r["cote_under"]) - 1
        p_over_corr = (1/r["cote_over"]) / ((1/r["cote_over"]) + (1/r["cote_under"]))
        total_paris = i + 1
        over_wins = over_wins + (1 if r["resultat"] == "OVER" else 0)
        taux_global = over_wins / total_paris
        rolling_start = max(0, i - 49)
        rolling_df = df.iloc[rolling_start:i+1]
        taux_roulant = (rolling_df["resultat"] == "OVER").mean()
        taux_utilise = 0.7 * taux_roulant + 0.3 * taux_global
        avantage = taux_utilise - p_over_corr
        ev = taux_utilise * (r["cote_over"] - 1) - (1 - taux_utilise)
        rbank = bankroll
        pct = risk_pct(rbank)
        coeff = coeff_mise(avantage)
        mise_over = max(st.session_state.mise_min, rbank * pct * coeff)

        if ev <= 0 or avantage < -0.03 or taux_roulant < -0.03 or pertes_cons >= 5:
            mise_over = st.session_state.mise_min

        mise_under = min(mise_over * 0.30, mise_over)

        if r["resultat"] == "OVER":
            profit = mise_over * (r["cote_over"] - 1)
            pertes_cons = 0
        else:
            profit = -mise_over
            pertes_cons += 1

        bankroll = bankroll + profit
        bankrolls.append(bankroll)
        profits.append(profit)
        mises.append(mise_over)
        roi = sum(profits) / sum(mises) if sum(mises) > 0 else 0
        rois.append(roi)

    dernier = df.iloc[-1]
    marge = (1/dernier["cote_over"]) + (1/dernier["cote_under"]) - 1
    p_over_corr = (1/dernier["cote_over"]) / ((1/dernier["cote_over"]) + (1/dernier["cote_under"]))
    over_global = (df["resultat"] == "OVER").mean()
    rolling_df = df.iloc[max(0, len(df)-50):]
    over_roulant = (rolling_df["resultat"] == "OVER").mean()
    taux_utilise = 0.7 * over_roulant + 0.3 * over_global
    avantage = taux_utilise - p_over_corr
    ev = taux_utilise * (dernier["cote_over"] - 1) - (1 - taux_utilise)
    pct = risk_pct(bankroll)
    coeff = coeff_mise(avantage)
    mise_over = max(st.session_state.mise_min, bankroll * pct * coeff)
    if ev <= 0 or avantage < -0.03 or over_roulant < -0.03 or (df["resultat"].tail(5) != "OVER").all():
        mise_over = st.session_state.mise_min

    mise_under = min(mise_over * 0.30, mise_over)
    pertes5 = 5 if (df["resultat"].tail(5) != "OVER").all() else min(4, (df["resultat"].tail(5) != "OVER").sum())
    score = score_confiance(ev, avantage, rois[-1], pertes5)

    if ev <= 0 or avantage < -0.03 or over_roulant < -0.03 or pertes5 >= 5:
        decision = "PROTECTION"
        mise_over = st.session_state.mise_min
        mise_under = st.session_state.mise_min
    elif score > 70:
        decision = "MISE NORMALE"
    elif score >= 50:
        decision = "75% MISE"
        mise_over *= 0.75
        mise_under *= 0.75
    elif score >= 30:
        decision = "50% MISE"
        mise_over *= 0.50
        mise_under *= 0.50
    else:
        decision = "0,10€"
        mise_over = st.session_state.mise_min
        mise_under = st.session_state.mise_min

    pari_suivant = "OVER" if taux_utilise >= 0.50 else "UNDER"
    projection_gagne = bankroll + (mise_over * (dernier["cote_over"] - 1) if pari_suivant == "OVER" else mise_over * (dernier["cote_under"] - 1))
    projection_perdu = bankroll - mise_over

    st.success("Calcul terminé")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Bankroll réelle", f"{bankroll:.2f} €")
        st.metric("EV", f"{ev:.4f}")
        st.metric("Avantage corrigé", f"{avantage*100:.2f} %")
        st.metric("Score confiance", f"{score}")
    with col2:
        st.metric("Mise Over", f"{mise_over:.2f} €")
        st.metric("Mise Under", f"{mise_under:.2f} €")
        st.metric("Décision", decision)
        st.metric("Pari suivant", pari_suivant)

    st.write("### Résumé")
    st.write(f"- Marge bookmaker : **{marge:.4f}**")
    st.write(f"- Probabilité Over corrigée : **{p_over_corr*100:.2f} %**")
    st.write(f"- Taux Over global : **{over_global*100:.2f} %**")
    st.write(f"- Taux Over roulant : **{over_roulant*100:.2f} %**")
    st.write(f"- Taux réel utilisé : **{taux_utilise*100:.2f} %**")
    st.write(f"- Projection si gagnant : **{projection_gagne:.2f} €**")
    st.write(f"- Projection si perdant : **{projection_perdu:.2f} €**")

    st.session_state.history = df
    st.dataframe(df[["cote_over", "cote_under", "resultat", "apport", "retrait"]], use_container_width=True)
