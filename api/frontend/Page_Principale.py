import streamlit as st

st.set_page_config(
        page_title = "Page principale",
        page_icon="👋"
    )

st.title("Bienvenue sur le  projet CryptoBot avec Binance - DataScientest 👋")


st.sidebar.success("Selectionner une page ci-dessus")

st.write("")
st.markdown(
    """
    Le but du projet est de prédire les futures valeurs sur le cours d'un marché crypto
    afin d'aider pour une décision d'achat ou non.\n
    Les données du cours de la crypto sont récoltées sur la plateforme Binance,
    et sont ensuite stockées dans une base de données SQL.\n
    La prédiction se fera via un algo de Deep Learning, algo LSTM.\n
    Les données affichées sur ces pages proviennent d'une API qui a été faite dans le cadre de ce projet.
    ### Projet Datascientest
    ### Equipe
    - Sadia ABCHICHE
    - Mohamed Mehdi YOUSSEF
    - Walid SABER-CHERIF
    - Alain VONGVILAY
    """
    )

