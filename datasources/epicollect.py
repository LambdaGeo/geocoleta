import os
import json
import requests
import pandas as pd

from core.registry import datasource
from core.datasources import DataSource
#from core.epicollect_tokens import load_token   # <-- USANDO O NOVO TOKEN

from dotenv import load_dotenv
load_dotenv()

from api import fetch_data


PROJECT_COMERCIO = os.getenv("PROJECT_COMERCIO")
FORM_COMERCIO_REF = os.getenv("FORM_COMERCIO_REF")
BASE_URL_COMERCIO = f"https://five.epicollect.net/api/export/entries/{PROJECT_COMERCIO}?form_ref={FORM_COMERCIO_REF}"

PROJECT_RESIDUOS = os.getenv("PROJECT_RESIDUOS")
FORM_RESIDUOS_REF = os.getenv("FORM_RESIDUOS_REF")
BASE_URL_RESIDUOS = f"https://five.epicollect.net/api/export/entries/{PROJECT_RESIDUOS}?form_ref={FORM_RESIDUOS_REF}"


def extrair_questoes(inputs, lista):
    for item in inputs:

        tipo = item.get("type")

        if tipo not in ("readme", "group"):
            if "question" in item and item["question"]:
                lista.append(item["question"])

        if "group" in item and isinstance(item["group"], list):
            extrair_questoes(item["group"], lista)

    return lista



#@datasource("Epicollect (Pesquisa Resíduos)")
class EpicollectResiduos(DataSource):

    FORM_NAME = "residuos"   # nome usado no token.json e nas variáveis de ambiente

    def get_form_schema(self):
        """Carrega o schema local do formulário."""
        schema_path = "/home/sergio/dev/github/lambdageo/datmoze/pesquisaresiduos__diagnostico__form.json"

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        inputs = schema["data"]["form"]["inputs"]

        lista = ['ec5_uuid', 'created_at', 'uploaded_at', 'created_by', 'title']

        return extrair_questoes(inputs, lista)


    def get_entries(self):
        data = fetch_data(self.FORM_NAME, BASE_URL_RESIDUOS)

        # Tratamento de erros
        if "errors" in data:
            erro = data["errors"][0]

            if erro.get("code") == "ec5_335":
                raise RuntimeError(
                    "🚫 Limite máximo de registros excedido no Epicollect.\n\n"
                    "💡 Soluções:\n"
                    "• Reduzirrr o per_page\n"
                    "• Paginar\n"
                    "• Aumentar limite no projeto Epicollect"
                )

            raise RuntimeError(f"Erro da API Epicollect: {erro.get('title')}")

        return pd.DataFrame(data["data"]["entries"])



    def load(self):
        """Organiza DataFrame final com colunas coerentes."""

        colunas = self.get_form_schema()
        df = self.get_entries()

        # Ajustar colunas final
        #df = df[colunas]

        return df
