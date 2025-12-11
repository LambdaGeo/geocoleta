import requests
import time
import json
import os

TOKEN_FILE = "token.json"

def get_token(form_name):
    client_id = os.environ.get(f"{form_name.upper()}_CLIENT_ID")
    client_secret = os.environ.get(f"{form_name.upper()}_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise Exception(f"Variáveis de ambiente não definidas para {form_name.upper()}")

    url = "https://five.epicollect.net/api/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 7200)
        expiration_time = time.time() + expires_in

        try:
            with open(TOKEN_FILE, "r") as f:
                all_tokens = json.load(f)
        except:
            all_tokens = {}

        all_tokens[form_name] = {
            "access_token": access_token,
            "expires_at": expiration_time
        }

        with open(TOKEN_FILE, "w") as f:
            json.dump(all_tokens, f)

        return access_token
    else:
        raise Exception(f"Erro ao obter token para '{form_name}': {response.json()}")

def load_token(form_name):
    try:
        with open(TOKEN_FILE, "r") as f:
            all_tokens = json.load(f)
            if form_name in all_tokens:
                token_data = all_tokens[form_name]
                if time.time() < token_data["expires_at"]:
                    return token_data["access_token"]
    except:
        pass
    return get_token(form_name)

def initialize_tokens():
    for form_name in ["residuoscomercio", "residuos"]:
        print (form_name)
        load_token(form_name)


