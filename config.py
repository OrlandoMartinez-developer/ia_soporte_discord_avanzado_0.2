import os
import json
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURACIÓN === #
CLIENT_ID = os.getenv("ASANA_CLIENT_ID")
CLIENT_SECRET = os.getenv("ASANA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ASANA_REDIRECT_URI", "http://localhost:8000/callback")
EXCLUDED_PROJECT_IDS = os.getenv("EXCLUDED_PROJECT_IDS", "").split(",")
EXCLUDED_USER_IDS = os.getenv("EXCLUDED_USER_IDS", "").split(",")

AUTH_BASE_URL = 'https://app.asana.com/-/oauth_authorize'
TOKEN_URL = 'https://app.asana.com/-/oauth_token'
SCOPE = ['default']
TOKEN_PATH = "asana_token.json"

# === INICIAR SESIÓN OAUTH === #
def load_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            return json.load(f)
    return None

def save_token(token):
    with open(TOKEN_PATH, "w") as f:
        json.dump(token, f)

token_data = load_token()
if token_data:
    oauth = OAuth2Session(CLIENT_ID, token=token_data)
else:
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)

def get_authorization_url():
    authorization_url, _ = oauth.authorization_url(AUTH_BASE_URL)
    print(f"🔑 Abre esta URL en tu navegador y autoriza la app:\n{authorization_url}")
    return authorization_url

def fetch_token_from_callback(authorization_response):
    token = oauth.fetch_token(
        TOKEN_URL,
        authorization_response=authorization_response,
        client_secret=CLIENT_SECRET
    )
    save_token(token)
    return token

# === FUNCIONES DE DATOS === #
def get_workspaces():
    resp = oauth.get("https://app.asana.com/api/1.0/workspaces")
    return resp.json().get("data", [])

def get_default_workspace():
    workspaces = get_workspaces()
    return workspaces[0] if workspaces else None

def get_projects():
    ws = get_default_workspace()
    if not ws:
        return []
    resp = oauth.get(f"https://app.asana.com/api/1.0/workspaces/{ws['gid']}/projects")
    return [p for p in resp.json().get("data", []) if p["gid"] not in EXCLUDED_PROJECT_IDS]

def get_users():
    ws = get_default_workspace()
    if not ws:
        return []
    resp = oauth.get(f"https://app.asana.com/api/1.0/workspaces/{ws['gid']}/users")
    return [u for u in resp.json().get("data", []) if u["gid"] not in EXCLUDED_USER_IDS]

# === USO INTERACTIVO === #
def main():
    ws = get_default_workspace()
    if not ws:
        print("❌ No hay workspaces disponibles.")
        return

    print(f"\n🌐 Workspace seleccionado: {ws['name']} ({ws['gid']})")

    print("\n📁 Proyectos:")
    for p in get_projects():
        print(f" - {p['name']} ({p['gid']})")

    print("\n👥 Usuarios:")
    for u in get_users():
        print(f" - {u['name']} ({u['gid']})")

if __name__ == '__main__':
    if not token_data:
        get_authorization_url()
        response_url = input("🔁 Pega aquí el URL de redirección: ").strip()
        fetch_token_from_callback(response_url)

    # Mostrar datos
    main()
