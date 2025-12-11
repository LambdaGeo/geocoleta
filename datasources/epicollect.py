import os
import json
import requests
import pandas as pd

from core.registry import datasource
from core.datasources import DataSource
from core.epicollect_tokens import load_token   # <-- USANDO O NOVO TOKEN

from dotenv import load_dotenv
load_dotenv()


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
        """Busca entradas da API com tratamento de erros e token persistente."""

        token = load_token(self.FORM_NAME)  # <-- USA O TOKEN AUTOMATICAMENTE

        form_ref = os.getenv("FORM")
        if not form_ref:
            raise ValueError("FORM não definido no .env")

        url = (
            "https://five.epicollect.net/api/export/entries/"
            f"pesquisaresiduos?sort_order=ASC&per_page=9999&form_ref={form_ref}"
        )

        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        r = requests.get(url, headers=headers)
        data = r.json()

        # Tratamento de erros
        if "errors" in data:
            erro = data["errors"][0]

            if erro.get("code") == "ec5_335":
                raise RuntimeError(
                    "🚫 Limite máximo de registros excedido no Epicollect.\n\n"
                    "💡 Soluções:\n"
                    "• Reduzir o per_page\n"
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
        df = df[colunas]

        return df
