# **Protocole d'Orchestration (WFGY-Core) : Moteur d'ETL Modulaire**

## **1\. Philosophie du Système**

Ce système est conçu pour être un **orchestrateur d'intention** basé sur des primitives atomiques en Rust, piloté par un cerveau Python. Il sépare strictement la logique de décision de la logique d'exécution.

* **Cerveau (Python) :** Analyse l'intention, planifie le graphe d'exécution (DAG), valide les types.  
* **Muscle (Rust) :** Exécute les primitives de données (I/O, Transformation, Réseau). Performance déterministe, sans garbage collector lourd.  
* **Chef d'Orchestre (LLM) :** Analyse les requêtes en langage naturel pour générer la "recette" (le plan d'exécution) que Python va orchestrer.



## **2\. Registre des Primitives (Registry.json)**

Le LLM doit utiliser exclusivement ces briques pour construire ses plans. Chaque primitive est une unité atomique.

| Primitive | Description | Paramètres   |
| :---- | :---- | :---- |
| **io.copy** | Copie un flux de données. | source, destination, mode |
| **io.move** | Déplace un fichier ou répertoire. | source, destination |
| **io.metadata** | Récupère les attributs de fichier. | path |
| **data.filter** | Filtre un flux de données. | column, operator, value |

## **3\. Protocole de la "Recette" (Plan d'exécution)**

Le LLM doit impérativement structurer ses réponses sous la forme d'une recette JSON. Le système d'orchestration Python consomme ce format pour déclencher les binaires Rust.  
`{`  
  `"plan_id": "uuid_unique",`  
  `"intent_analysis": "Analyse de la demande utilisateur",`  
  `"steps": [`  
    `{`  
      `"step": 1,`  
      `"primitive": "io.copy",`  
      `"args": {"source": "/path/a", "destination": "/path/b", "mode": "binary"}`  
    `}`  
  `]`  
`}`

## **4\. Règles Cognitives pour le Chef (LLM)**

1. **Génération de Plan :** Ne jamais exécuter de code directement. Ton rôle est de concevoir le plan d'assemblage des primitives.  
2. **Auto-Correction :** Si l'orchestrateur Python rapporte une erreur (ex: fichier introuvable), analyse l'erreur, identifie la cause, et régénère un plan corrigé.  
3. **Atomicité :** Décompose les requêtes complexes en étapes simples basées sur le registre.  
4. **Typage :** Assure-toi que le résultat d'une étape est compatible avec l'entrée de la suivante.

## **5\. Vision d'évolution**

* **Phase 1 :** Opérations fichiers locales (Copy, Move, Read).  
* **Phase 2 :** Primitives Réseau (HTTP, Sockets) pour déporter le traitement.  
* **Phase 3 :** Primitives de Transformation (Polars/Rust) pour le traitement de gros volumes de données.


# **6\. Front-End & Visualisation (WFGY-Workbench)**

### **6.1. Architecture Visuelle**

* **Technologie :** Vanilla JS avec Web Components (native). Pas de build, pas d'héritage lourd.  
* **Protocole de communication :** WebSockets full-duplex pour le streaming d'état.  
* **Paradigme UX :** "Intent-First". La saisie utilisateur génère dynamiquement le graphe d'exécution.

### **6.2. Spécification du Rendu (Visual Primitive)**

Le LLM doit enrichir le JSON de la recette avec des métadonnées optionnelles pour le rendu graphique :  
`{`  
  `"step": 1,`  
  `"primitive": "io.copy",`  
  `"ui": {`  
    `"label": "Copie Fichiers",`  
    `"color": "#4A90E2",`  
    `"position": {"x": 100, "y": 150}`  
  `},`  
  `"args": { ... }`  
`}`

### **6.3. Canevas de l'Interface**

Le Workbench est divisé en trois zones fonctionnelles :

1. **The Intent Bar (Zone A) :** Barre de commande unique en haut de page.  
2. **The Canvas (Zone B) :** Zone de dessin dynamique (Canvas/SVG). Chaque étape devient un workflow-node (Web Component). Les fils de connexion sont tracés par courbes de Bézier reliant les output d'une brique aux input de la suivante.  
3. **The Stream Log (Zone C) :** Volet latéral rétractable affichant les logs bruts du moteur Rust pour un diagnostic temps réel.

### **6.4. Comportement des flux (Wiring)**

* **États dynamiques :** Chaque workflow-node doit être capable de refléter son état (pending, running, success, error) via des classes CSS dynamiques.  
* **Auto-layout :** Le front-end doit être capable de recalculer automatiquement les positions des briques si le LLM insère une étape intermédiaire dans un plan existant.