"""Script Power BI Python — charge un dataset depuis l'API WFGY.
Utilisation dans Power BI : Obtenir des donnees > Autres > Script Python > Coller ce script"""
import urllib.request, json

WFGY_URL = "http://localhost:8766"
API_TOKEN = ""  # Optionnel: mettre votre token JWT ici

def get_primitives():
    req = urllib.request.Request(f"{WFGY_URL}/api/primitives")
    if API_TOKEN:
        req.add_header("Authorization", f"Bearer {API_TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_health():
    with urllib.request.urlopen(f"{WFGY_URL}/api/health") as r:
        return json.loads(r.read())

def get_run_history():
    with urllib.request.urlopen(f"{WFGY_URL}/api/run-history") as r:
        return json.loads(r.read())

# Charger les donnees
primitives = get_primitives()
health = get_health()
history = get_run_history()

# Creer les DataFrames Power BI
import pandas as pd

df_primitives = pd.DataFrame(primitives)
df_health = pd.DataFrame([health])
df_history = pd.DataFrame(history)
