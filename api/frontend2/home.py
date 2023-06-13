import streamlit as st

def app():
    st.set_page_config(page_title="BTC Prédiction", page_icon="🔮", layout="wide")

    st.title('Bienvenue dans l\'application de Prédiction du Prix du BTC')

    st.write(
        "<div>Cette application a été conçue pour vous aider à comprendre les "
        "tendances futures du prix du Bitcoin en se basant sur des analyses "
        "prédictives avancées. Notre modèle utilise des données historiques "
        "pour prédire les prix du Bitcoin pour le lendemain. L'interface "
        "utilisateur est simple et intuitive, vous permettant d'envoyer des "
        "requêtes SQL pour récupérer les données que vous souhaitez analyser, "
        "et ensuite générer une prédiction en cliquant simplement sur un bouton.</div><br>"
    )

    st.write(
        "<div>Avant de commencer, il est important de noter que, bien que nos "
        "prédictions soient générées à partir de modèles mathématiques "
        "sophistiqués, elles restent intrinsèquement incertaines et doivent "
        "être utilisées à titre informatif uniquement. Les marchés financiers, "
        "et en particulier le marché des cryptomonnaies, sont extrêmement "
        "volatils et imprévisibles. Investir dans le Bitcoin ou toute autre "
        "cryptomonnaie comporte des risques, dont la perte totale de "
        "l'investissement. Nous vous conseillons vivement de ne jamais "
        "investir plus que ce que vous êtes prêt à perdre, et de toujours "
        "demander l'avis d'un conseiller financier professionnel avant de "
        "prendre des décisions d'investissement. Profitez de l'application, "
        "mais restez prudent et conscient des risques.</div>"
    )

if __name__ == "__main__":
    app()