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

    def _build_system_prompt(self) -> str:
        # Construct dynamic prompt containing registry specs
        registry_str = json.dumps(self.registry, indent=2, ensure_ascii=False)
        
        prompt = f"""Tu es le "Chef d'Orchestre" (LLM) du moteur d'ETL Modulaire WFGY-Core V3.
Ton rôle est d'analyser l'intention de l'utilisateur et de générer une "Recette" d'exécution structurée en JSON.

Voici le registre officiel des primitives disponibles :
{registry_str}

Tu dois IMPÉRATIVEMENT répondre uniquement sous la forme d'un objet JSON respectant la structure suivante. Ne mets aucune phrase d'explication ou d'introduction. Ne mets pas de bloc de code markdown. Réponds avec le JSON brut.

Structure du JSON attendu :
{{
  "plan_id": "chaîne_unique_generée_pour_le_plan",
  "intent_analysis": "Explication courte en une phrase de ce que fait ce plan",
  "steps": [
    {{
      "step": 1,
      "primitive": "nom_de_la_primitive",
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

4. Pour tout mot de passe, clé API, hôte, ou credentials sensibles (ex: mot de passe Snowflake, token API), utilise impérativement des placeholders sous la forme de variable d'environnement "${{SECRET_NOM_VARIABLE}}" (ex: "${{SECRET_SNOWFLAKE_PASSWORD}}"). Ne mets jamais de secret en clair dans le JSON.
"""
        return prompt

    def plan(self, user_intent: str, current_recipe: dict = None) -> dict:
        system_prompt = self._build_system_prompt()
        
        user_prompt = user_intent
        if current_recipe and current_recipe.get("steps"):
            recipe_context = json.dumps(current_recipe, indent=2, ensure_ascii=False)
            user_prompt = f"""Voici la recette actuelle du workflow :
{recipe_context}

Voici la nouvelle intention de l'utilisateur pour enrichir ou modifier cette recette :
"{user_intent}"

Tu dois intégrer cette nouvelle intention dans la recette actuelle. Modifie la recette existante (ajoute, supprime ou modifie des étapes) et renvoie la recette finale fusionnée et mise à jour au format JSON.
"""
        
        raw_response = self.client.generate_completion(system_prompt, user_prompt)
        
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
