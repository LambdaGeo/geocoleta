import os
import json
import requests
import pandas as pd

from core.registry import datasource
from core.datasources import DataSource

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

@datasource("Epicollect (Pesquisa Resíduos)")
class EpicollectResiduos(DataSource):

    def get_form_schema(self):
        """Carrega o schema local do formulário."""
        schema_path = "/home/sergio/dev/github/lambdageo/datmoze/pesquisaresiduos__diagnostico__form.json"

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        inputs = schema["data"]["form"]["inputs"]

        lista = ['ec5_uuid', 'created_at', 'uploaded_at', 'created_by', 'title']

        return extrair_questoes(inputs, lista)

    def load(self):
        """Organiza DataFrame final com colunas coerentes."""

        colunas = self.get_form_schema()
        
        with open("/home/sergio/dev/github/lambdageo/datmoze/dados.json", "r", encoding="utf-8") as f:
            dados = json.load(f)

        
        df = pd.DataFrame(dados["data"])
        # Ajustar colunas final
        df.columns = colunas
        print (df.head)
        print (df.columns)
        print("---------")
        print (colunas)

        return df