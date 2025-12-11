import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from epicollect_auth import load_token, initialize_tokens
from dotenv import load_dotenv
import os

# Carrega as variáveis do .env local (durante desenvolvimento)
load_dotenv()

# Inicializa os tokens
initialize_tokens()

# Carrega dados do .env
PROJECT_COMERCIO = os.getenv("PROJECT_COMERCIO")
FORM_COMERCIO_REF = os.getenv("FORM_COMERCIO_REF")
BASE_URL_COMERCIO = f"https://five.epicollect.net/api/export/entries/{PROJECT_COMERCIO}?form_ref={FORM_COMERCIO_REF}"

PROJECT_RESIDUOS = os.getenv("PROJECT_RESIDUOS")
FORM_RESIDUOS_REF = os.getenv("FORM_RESIDUOS_REF")
BASE_URL_RESIDUOS = f"https://five.epicollect.net/api/export/entries/{PROJECT_RESIDUOS}?form_ref={FORM_RESIDUOS_REF}"

# Busca dados da API
def fetch_data(form_name, base_url):
    token = load_token(form_name)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(base_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao buscar dados para '{form_name}': {response.status_code}")
        return {}

# Usando os dados
data_comercio = fetch_data("residuoscomercio", BASE_URL_COMERCIO)
data_residuos = fetch_data("residuos", BASE_URL_RESIDUOS)

# st.write("Dados do Comércio:")
# st.json(data_comercio)

# st.write("Dados dos Resíduos:")
# st.json(data_residuos)