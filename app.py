import json
from pathlib import Path
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Mini bot Over / Under", layout="wide")

DATA_FILE = Path("paris.json")

def fmt_eur(x):
    return f"{x:.2f} €"

def fmt_pct(x):
    return f"{x:.2f} %"

def safe_div(a, b):
    return a / b if b not in (0, 0.0, None) else 0.0

def load_paris():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_paris(paris):
    DATA_FILE.write_text(json.dumps(paris, ensure_ascii=False, indent=2), encoding="utf-8")

def calculer_mise_dynamique(paris, bankroll, mise_min):
    if not paris:
        return mise_min
    dernier = paris[-1]
    mise_precedente = float(dernier.get("mise", mise_min))
    if dernier.get("resultat") == "WIN":
        mise = mise_precedente * 1.20
    elif dernier.get("resultat") == "LOSS":
        mise = mise_precedente * 0.70
    else:
        mise = mise_precedente
    return max(mise_min, min(mise, bankroll * 0.10))

def calculer_marge(cote_over, cote_under):
    return safe_div(1, cote_over) + safe_div(1, cote_under) - 1

def proba_correction(cote_over, cote_under):
    inv_over = safe_div(1, cote_over)
    inv_under = safe_div(1, cote_under)
    total = inv_over + inv_under
    if total == 0:
        return 0.5, 0.5
    return inv_over / total, inv_under / total

if "paris" not in st.session_state:
    st.session_state.paris = load_paris()
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 100.0
if "mise_conseillee" not in st.session_state:
    st.session_state.mise_conseillee = 0.0
if "bankroll_apres" not in st.session_state:
    st.session_state.bankroll_apres = None

st.title("Mini bot Over / Under")
st.caption("Bankroll persistante, historique des paris, mise dynamique et plafond.")

with st.sidebar:
    st.header("Paramètres")

    bankroll_initiale = st.number_input("Bankroll initiale", min_value=0.0, value=float(st.session_state.bankroll), step=1.0, format="%.2f")
    mise_minimum = st.number_input("Mise minimum", min_value=0.0, value=0.20, step=0.10, format="%.2f")

    st.divider()
    st.subheader("Dernier pari")
    cote_over_last = st.number_input("Cote Over du dernier pari", min_value=1.0, value=1.90, step=0.01, format="%.2f")
    cote_under_last = st.number_input("Cote Under du dernier pari", min_value=1.0, value=1.90, step=0.01, format="%.2f")
    resultat_last = st.selectbox("Résultat du dernier pari", ["OVER", "UNDER"])
    apport_bankroll = st.number_input("Apport bankroll", min_value=0.0, value=0.0, step=0.10, format="%.2f")
    retrait_bankroll = st.number_input("Retrait bankroll", min_value=0.0, value=0.0, step=0.10, format="%.2f")

    st.divider()
    st.subheader("Prochain pari")
    cote_over_next = st.number_input("Cote Over suivante", min_value=1.0, value=1.90, step=0.01, format="%.2f")
    cote_under_next = st.number_input("Cote Under suivante", min_value=1.0, value=1.90, step=0.01, format="%.2f")

    st.divider()
    st.subheader("Protection")
    mode_protection = st.toggle("Activer le mode protection", value=True)

    nb_paris = len(st.session_state.paris)
    gains = sum(float(p.get("gain", 0)) for p in st.session_state.paris)
    pertes = sum(float(p.get("perte", 0)) for p in st.session_state.paris)
    bankroll_actuelle = bankroll_initiale + gains - pertes + apport_bankroll - retrait_bankroll
    profit = bankroll_actuelle - bankroll_initiale
    roi = safe_div(profit, bankroll_initiale) * 100
    nb_over = sum(1 for p in st.session_state.paris if p.get("resultat") == "WIN")
    nb_under = sum(1 for p in st.session_state.paris if p.get("resultat") == "LOSS")
    taux_over = safe_div(nb_over, nb_paris) * 100
    taux_under = safe_div(nb_under, nb_paris) * 100

    pertes_consecutives = 0
    for p in reversed(st.session_state.paris):
        if p.get("resultat") == "LOSS":
            pertes_consecutives += 1
        else:
            break

    mise_theorique = calculer_mise_dynamique(st.session_state.paris, bankroll_actuelle, mise_minimum)
    plafond = bankroll_actuelle * (0.05 if mode_protection else 0.10)
    mise_finale = max(mise_minimum, min(mise_theorique, plafond))

    marge = calculer_marge(cote_over_next, cote_under_next)
    proba_over, proba_under = proba_correction(cote_over_next, cote_under_next)
    ev_over = (proba_over * (cote_over_next - 1)) - (1 - proba_over)
    ev_under = (proba_under * (cote_under_next - 1)) - (1 - proba_under)

    st.divider()
    st.subheader("Infos instantanées")
    st.metric("Bankroll instantané", fmt_eur(bankroll_actuelle))
    st.metric("Profit cumulé", fmt_eur(profit))
    st.metric("ROI global", fmt_pct(roi))
    st.metric("Taux Over", fmt_pct(taux_over))
    st.metric("Taux Under", fmt_pct(taux_under))
    st.metric("Pertes consécutives", pertes_consecutives)
    st.metric("Mise conseillée", fmt_eur(mise_finale))
    st.metric("Plafond appliqué", fmt_eur(plafond))

col1, col2 = st.columns(2)
with col1:
    st.subheader("Côtes du prochain pari")
    st.write(f"**Over suivant :** {cote_over_next:.2f}")
    st.write(f"**Under suivant :** {cote_under_next:.2f}")
    st.write(f"**Marge bookmaker :** {fmt_pct(marge * 100)}")
    st.write(f"**Probabilité Over corrigée :** {fmt_pct(proba_over * 100)}")
    st.write(f"**EV Over :** {fmt_pct(ev_over * 100)}")
with col2:
    st.subheader("Signal rapide")
    if mode_protection and pertes_consecutives >= 3:
        st.warning("Mode protection activé : mise réduite.")
    elif cote_over_next > cote_under_next:
        st.success("Favori marché : UNDER")
    elif cote_under_next > cote_over_next:
        st.success("Favori marché : OVER")
    else:
        st.info("Marché équilibré")

st.divider()

if st.button("Calculer le prochain pari"):
    bankroll_avant = bankroll_actuelle
    mise = calculer_mise_dynamique(st.session_state.paris, bankroll_avant, mise_minimum)

    if mode_protection:
        mise = min(mise, bankroll_avant * 0.05)

    st.session_state.mise_conseillee = mise

    if resultat_last == "OVER":
        gain = mise * (cote_over_last - 1)
        perte = 0.0
        outcome = "WIN"
    else:
        gain = 0.0
        perte = mise
        outcome = "LOSS"

    bankroll_apres = bankroll_avant + gain - perte
    st.session_state.bankroll_apres = bankroll_apres
    st.session_state.bankroll = bankroll_apres

    nouveau_pari = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resultat": outcome,
        "mise": mise,
        "gain": gain,
        "perte": perte,
        "bankroll_avant": bankroll_avant,
        "bankroll_apres": bankroll_apres,
        "cote_over": cote_over_last,
        "cote_under": cote_under_last,
    }

    st.session_state.paris.append(nouveau_pari)
    save_paris(st.session_state.paris)

    st.success("Calcul effectué et pari sauvegardé.")
    st.write(f"Mise conseillée : **{fmt_eur(mise)}**")
    st.write(f"Bankroll estimée après pari : **{fmt_eur(bankroll_apres)}**")

st.subheader("Derniers paris")
if st.session_state.paris:
    for i, p in enumerate(reversed(st.session_state.paris[-10:]), start=1):
        st.write(
            f"{i}. {p.get('date', '')} — {p.get('resultat', '')} — mise: {fmt_eur(float(p.get('mise', 0)))} — bankroll après: {fmt_eur(float(p.get('bankroll_apres', 0)))}"
        )
else:
    st.write("Aucun pari enregistré.")
