# [WFGY] Zone: SAFE | λ: 0.3 | Action: LLM Recipe Planner implementation
import json
import re
import sys
from pathlib import Path
from llm_client import OpenAICompatibleClient, GeminiAPIClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

class RecipePlanner:
    """
    Component translating user natural language intent to a structured recipe JSON.
    """
    def __init__(self, env_config: dict):
        self.root_dir = Path(__file__).parent
        
        # Load registry
        with open(self.root_dir / "registry.json", "r", encoding="utf-8") as f:
            self.registry = json.load(f)
            
        # Instantiate LLM Client based on environment configuration
        provider = env_config.get("LLM_PROVIDER", "openai_compatible")
        model = env_config.get("LLM_MODEL", "gemma")
        base_url = env_config.get("LLM_BASE_URL", "http://localhost:1234/v1")
        import os
        api_key = env_config.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
        
        disable_json = env_config.get("LLM_DISABLE_JSON_FORMAT", "false").lower() == "true"
        
        if provider == "gemini":
            self.client = GeminiAPIClient(api_key=api_key, model=model)
        else:
            self.client = OpenAICompatibleClient(
                base_url=base_url, 
                model=model, 
                api_key=api_key, 
                disable_json_format=disable_json
            )

    def _build_succinct_registry(self) -> str:
        # Construit une version ultra-compacte du registre : uniquement les clés et les descriptions de haut niveau
        succinct = {}
        for k, v in self.registry.get("primitives", {}).items():
            succinct[k] = v.get("description", "")
        return json.dumps(succinct, indent=2, ensure_ascii=False)

    def _build_phase1_system_prompt(self, succinct_registry_str: str) -> str:
        return f"""Tu es un sélecteur d'outils ultra-rapide et précis pour un orchestrateur ETL.
Ton rôle est d'analyser l'intention de l'utilisateur et d'identifier UNIQUEMENT les identifiants des outils (primitives) requis pour accomplir la tâche.

Voici les outils disponibles et leur description :
{succinct_registry_str}

Tu dois IMPÉRATIVEMENT répondre uniquement sous la forme d'un tableau JSON contenant les IDs des outils requis. Ne mets aucune explication.
Exemple de réponse : ["io.copy", "s3.upload"]
"""

    def _build_phase2_system_prompt(self, filtered_registry: dict) -> str:
        registry_str = json.dumps(filtered_registry, indent=2, ensure_ascii=False)
        return f"""Tu es le "Chef d'Orchestre" (LLM) du moteur d'ETL Modulaire WFGY-Core V3.
Ton rôle est d'analyser l'intention de l'utilisateur et de générer une "Recette" d'exécution structurée en JSON.

Voici les spécifications détaillées des primitives dont tu as besoin pour ce plan :
{registry_str}

Tu devez IMPÉRATIVEMENT répondre uniquement sous la forme d'un objet JSON respectant la structure suivante. Ne mets aucune phrase d'explication. Réponds avec le JSON brut.

Structure du JSON attendu :
{{
  "plan_id": "chaîne_unique_generée_pour_le_plan",
  "intent_analysis": "Explication courte en une phrase de ce que fait ce plan",
  "steps": [
    {{
      "step": 1,
      "primitive": "nom_de_la_primitive",
      "depends_on": [], // Tableau des IDs d'étapes (integer) dont dépend cette étape. Exemple: [1] si cette étape doit attendre l'étape 1. IMPORTANT: Si l'étape B utilise un fichier produit par l'étape A, alors B doit avoir "depends_on": [A] pour éviter les accès concurrents.
      "ui": {{
        "label": "Titre convivial pour l'étape (ex: Copie source)",
        "color": "#4A90E2",
        "position": {{"x": 150, "y": 200}}
      }},
      "args": {{
         // Les arguments requis pour la primitive selon la spécification du registre
      }}
    }}
  ]
}}

Pour tout mot de passe, clé API, hôte, ou credentials sensibles (ex: mot de passe Snowflake, token API), utilise impérativement des placeholders sous la forme de variable d'environnement "${{SECRET_NOM_VARIABLE}}" (ex: "${{SECRET_SNOWFLAKE_PASSWORD}}"). Ne mets jamais de secret en clair dans le JSON.

Si le plan requiert une transformation XML personnalisée (primitive `data.xml_transform`) et qu'aucun fichier de feuille de style XSLT existant n'est fourni par l'utilisateur, tu dois concevoir et générer la feuille de style XSLT. Pour ce faire, crée une étape préliminaire utilisant la primitive `io.write_file` pour écrire le contenu de ton XSLT dans un fichier temporaire (ex: "stylesheet.xslt"), puis référence ce fichier dans l'étape `data.xml_transform`.
"""

    def _build_study_system_prompt(self) -> str:
        # Registre succint pour l'analyse des capacités
        succinct = self._build_succinct_registry()
        return f"""Tu es un Ingénieur Systèmes Senior en mode "Étude de Flux" (Phase de clarification).
Ton but est d'analyser l'intention de l'utilisateur pour un pipeline ETL complexe et de formuler une réponse structurée en JSON contenant des questions ciblées de clarification (de 1 à 3 questions maximum) et son analyse initiale.

Voici les primitives disponibles dans notre moteur :
{succinct}

Tu dois identifier s'il y a des ambiguïtés, des risques (conflits de fichiers, sécurité, volumes de données) ou des dépendances complexes, puis poser tes questions pour guider l'utilisateur.

Réponds IMPÉRATIVEMENT sous la forme d'un objet JSON strict avec cette structure :
{{
  "is_complex": true,
  "analysis": "Ton analyse succincte de l'intention et de ce que le flux va accomplir.",
  "questions": [
    "Première question de clarification...",
    "Deuxième question..."
  ]
}}
"""

    def study(self, user_intent: str, chat_history: list = None) -> dict:
        """
        Analyzes the intent and prompts the user with clarifying questions if it is complex.
        """
        system_prompt = self._build_study_system_prompt()
        
        user_prompt = f"Intention utilisateur : {user_intent}"
        if chat_history:
            history_str = json.dumps(chat_history, indent=2, ensure_ascii=False)
            user_prompt += f"\n\nHistorique de la discussion d'étude :\n{history_str}\n\nFormule tes nouvelles questions de clarification ou résume les réponses."

        print(f"[PLANNER] Mode Étude - Analyse de l'intention complexe...")
        raw_response = self.client.generate_completion(system_prompt, user_prompt)
        
        clean = raw_response.strip()
        if clean.startswith("```json"): clean = clean[7:]
        if clean.startswith("```"): clean = clean[3:]
        if clean.endswith("```"): clean = clean[:-3]
        clean = clean.strip()
        
        try:
            return json.loads(clean)
        except Exception as e:
            print(f"[PLANNER ERROR] Failed to parse JSON in study mode: {e}. Raw response: {raw_response}")
            return {
                "is_complex": False,
                "analysis": "Analyse standard",
                "questions": []
            }

    def plan(self, user_intent: str, current_recipe: dict = None) -> dict:
        # --- PHASE 1 : Identification succincte des primitives requises ---
        succinct_registry_str = self._build_succinct_registry()
        phase1_sys = self._build_phase1_system_prompt(succinct_registry_str)
        
        user_prompt_1 = f"Intention utilisateur : {user_intent}"
        if current_recipe and current_recipe.get("steps"):
            existing_primitives = list(set(s.get("primitive") for s in current_recipe.get("steps", []) if s.get("primitive")))
            user_prompt_1 += f"\n primitives déjà présentes dans la recette actuelle : {existing_primitives}"
            
        print(f"[PLANNER] Phase 1 - Identification des primitives requises pour l'intention...")
        raw_phase1 = self.client.generate_completion(phase1_sys, user_prompt_1)
        
        # Nettoyage et parsing des IDs identifiés
        clean_p1 = raw_phase1.strip()
        if clean_p1.startswith("```json"): clean_p1 = clean_p1[7:]
        if clean_p1.startswith("```"): clean_p1 = clean_p1[3:]
        if clean_p1.endswith("```"): clean_p1 = clean_p1[:-3]
        clean_p1 = clean_p1.strip()
        
        required_ids = []
        try:
            required_ids = json.loads(clean_p1)
            if not isinstance(required_ids, list):
                required_ids = []
        except Exception:
            # Fallback regex simple si le LLM n'a pas renvoyé de JSON valide
            required_ids = re.findall(r'"([a-zA-Z0-9_\-\.]+)"', clean_p1)

        # S'assurer d'inclure aussi les primitives déjà présentes dans la recette si on fusionne
        if current_recipe and current_recipe.get("steps"):
            for s in current_recipe.get("steps", []):
                prim = s.get("primitive")
                if prim and prim not in required_ids:
                    required_ids.append(prim)

        print(f"[PLANNER] Phase 1 terminées. Primitives retenues : {required_ids}")

        # Extraire uniquement les schémas complets des primitives requises (Just-In-Time)
        filtered_registry = {"primitives": {}}
        for pid in required_ids:
            if pid in self.registry.get("primitives", {}):
                filtered_registry["primitives"][pid] = self.registry["primitives"][pid]

        # Si aucune primitive trouvée, mettre le registre entier par sécurité pour éviter un plan vide
        if not filtered_registry["primitives"]:
            filtered_registry = self.registry

        # --- PHASE 2 : Génération de la recette paramétrée avec les schémas requis ---
        phase2_sys = self._build_phase2_system_prompt(filtered_registry)
        
        user_prompt_2 = user_intent
        if current_recipe and current_recipe.get("steps"):
            recipe_context = json.dumps(current_recipe, indent=2, ensure_ascii=False)
            user_prompt_2 = f"""Voici la recette actuelle du workflow :
{recipe_context}

Voici la nouvelle intention de l'utilisateur pour enrichir ou modifier cette recette :
"{user_intent}"

Tu dois intégrer cette nouvelle intention dans la recette actuelle. Modifie la recette existante (ajoute, supprime ou modifie des étapes) et renvoie la recette finale fusionnée et mise à jour au format JSON.
"""
        
        print(f"[PLANNER] Phase 2 - Génération de la recette paramétrée...")
        raw_response = self.client.generate_completion(phase2_sys, user_prompt_2)
        
        # Clean response if LLM wrapped it in markdown code blocks
        clean_response = raw_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        # Parse JSON
        try:
            recipe = json.loads(clean_response)
            return recipe
        except json.JSONDecodeError as e:
            print(f"[PLANNER ERROR] Failed to parse JSON from LLM response: {e}")
            print(f"Raw response was:\n{raw_response}")
            # Return a fallback recipe structure showing the error
            return {
                "plan_id": "error_plan",
                "intent_analysis": "Erreur de génération du plan par le LLM.",
                "steps": []
            }

if __name__ == "__main__":
    # Test execution CLI
    import sys
    from orchestrator import load_env
    
    intent = "Copier le fichier local source.txt vers destination.txt en mode texte"
    if len(sys.argv) > 1:
        intent = sys.argv[1]
        
    config = load_env("dev")
    planner = RecipePlanner(config)
    
    print(f"Planning for intent: '{intent}'")
    recipe = planner.plan(intent)
    print("\nGenerated Recipe:")
    print(json.dumps(recipe, indent=2, ensure_ascii=False))
