import streamlit as st
import requests

from cryptobot.common.cryptoutils import get_env_value_fallback

# Deployement on local machine
BACKEND = f"""http://{get_env_value_fallback('API_HOST', 'localhost')}:{get_env_value_fallback('API_PORT',8000)}"""

st.set_page_config(page_title="Identification", page_icon="🔓")

st.markdown("# Identification avec mot de passe 🔓")
st.sidebar.success("Page: Identification")
st.write(
    "Affichage de la page identification avec un mot de passe \
    pour pouvoir utiliser les autres pages.\
    "
)

st.write("")
st.write("**Identification:**")
login = st.text_input('Entrez votre identifiant')
st.write("")
password = st.text_input('Entrez votre mot de passe', type = "password")

st.write("")
plot_spot = st.empty()
st.write("")

col1, col2 = st.columns([1,1])

with col1:
    if st.button('Valider'):
        data = {
            'username': login,
            'password': password
        }
        response = requests.post(BACKEND + '/signin', data)
        if response.status_code == 200:
            st.session_state['token_key'] = response.json()['access_token']
            with plot_spot:
                st.write("Identification validée")
        else:
            st.session_state['token_key'] = ""
            with plot_spot:
                st.write("Identification invalide")
with col2:
    if st.button('Annuler'):
        st.session_state['token_key'] = ""