# server/llm_host.py

import os

import json

import requests

from dotenv import load_dotenv



load_dotenv()  # Charge les variables du .env



# ──────────────────────────────
# Wrapper LLM Perplexity
# ──────────────────────────────
class PerplexityTool:

    """Wrapper pour le LLM Perplexity."""

    def __init__(self):

        self.api_key = os.getenv("PERPLEXITY_API_KEY")

        if not self.api_key:

            raise ValueError("PERPLEXITY_API_KEY manquante dans .env")

        self.endpoint = "https://api.perplexity.ai/chat/completions"
        self.model = "sonar"  # ou "sonar" pour la version standard



    def ask(self, prompt: str) -> str:

        """Envoie un prompt au LLM et retourne la réponse brute."""

        headers = {

            "Authorization": f"Bearer {self.api_key}",

            "Content-Type": "application/json",

        }

        payload = {

            "model": self.model,

            "messages": [

                {"role": "user", "content": prompt}

            ],

            "temperature": 0.2,

            "max_tokens": 1000

        }

        try:

            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)

            response.raise_for_status()

            data = response.json()

            # Extraire la réponse du format chat completions

            if "choices" in data and len(data["choices"]) > 0:

                return data["choices"][0]["message"]["content"]

            return ""

        except requests.exceptions.RequestException as e:

            print(f"❌ Erreur Perplexity API: {e}")

            return f"Erreur LLM: {e}"



# ──────────────────────────────
# LLM Host
# ──────────────────────────────
class LLMHost:

    """

    Host pour LLM Perplexity + augmentation + génération

    Retourne toujours des réponses JSON-RPC

    """

    def __init__(self, llm_client):

        self.llm = llm_client



    def generate_prompt(self, user_text: str, context: dict) -> str:

        """Génère un prompt enrichi pour le LLM."""

        return (

            f"Utilisateur décrit un incident cloud:\n{user_text}\n\n"

            f"Contexte extrait de la DB graph:\n{json.dumps(context, indent=2)}\n\n"

            "IMPORTANT: Réponds UNIQUEMENT avec un objet JSON valide, sans markdown, sans texte avant ou après.\n\n"

            "Propose un JSON structuré pour l'incident avec cette structure exacte:\n"

            "{{\n"

            '  "id": "INC-XXX",\n'

            '  "type": "Incident",\n'

            '  "title": "Titre de l\'incident",\n'

            '  "description": "Description détaillée",\n'

            '  "status": "open",\n'

            '  "priority": "P1",\n'

            '  "services": ["service1", "service2"],\n'

            '  "teams": ["team1"],\n'

            '  "runbooks": ["runbook1"]\n'

            "}}\n\n"

            "Retourne uniquement le JSON, rien d'autre."

        )



    def propose_incident(self, user_text: str, context: dict) -> dict:

        """Appelle le LLM pour proposer un incident JSON (JSON-RPC)."""

        try:

            prompt = self.generate_prompt(user_text, context)

            llm_result_str = self.llm.ask(prompt)



            # Extraire le JSON de la réponse
            llm_json = None
            import re
            
            # 1. Chercher un bloc JSON dans markdown (```json ... ```)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_result_str, re.DOTALL)
            if json_match:
                try:
                    llm_json = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 2. Si pas trouvé, essayer de parser directement
            if llm_json is None:
                try:
                    llm_json = json.loads(llm_result_str.strip())
                except json.JSONDecodeError:
                    # 3. Chercher un objet JSON dans le texte (plus permissif)
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', llm_result_str, re.DOTALL)
                    if json_match:
                        try:
                            llm_json = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            # 4. Dernier recours : créer un objet avec la réponse brute
                            llm_json = {
                                "text": llm_result_str,
                                "raw_response": llm_result_str,
                                "error": "Could not parse JSON from LLM response"
                            }
                    else:
                        llm_json = {
                            "text": llm_result_str,
                            "raw_response": llm_result_str,
                            "error": "No JSON found in LLM response"
                        }



            return {

                "jsonrpc": "2.0",

                "result": {

                    "llm_proposal": llm_json,

                    "context": context

                },

                "status": "success"

            }

        except Exception as e:

            return {

                "jsonrpc": "2.0",

                "error": str(e),

                "status": "error"

            }



    def generate_incident_graph(self, incident_json: dict) -> dict:

        """

        Génère une version simplifiée du graphe pour le front.

        Nouvel incident au centre, services/équipes/runbooks liés.

        """

        try:

            nodes = []

            edges = []



            incident_id = incident_json.get("id", "incident_1")

            nodes.append({"id": incident_id, "label": incident_json.get("type", "Incident")})



            # Services

            for s in incident_json.get("services", []):

                nodes.append({"id": s, "label": "Service"})

                edges.append({"from": incident_id, "to": s, "type": "AFFECTS"})



            # Équipes

            for t in incident_json.get("teams", []):

                nodes.append({"id": t, "label": "Team"})

                edges.append({"from": t, "to": incident_id, "type": "OWNED_BY"})



            # Runbooks

            for r in incident_json.get("runbooks", []):

                nodes.append({"id": r, "label": "Runbook"})

                edges.append({"from": incident_id, "to": r, "type": "HAS_RUNBOOK"})



            return {

                "jsonrpc": "2.0",

                "result": {

                    "graph": {"nodes": nodes, "edges": edges}

                },

                "status": "success"

            }

        except Exception as e:

            return {

                "jsonrpc": "2.0",

                "error": str(e),

                "status": "error"

            }



# ──────────────────────────────
# Test rapide
# ──────────────────────────────
if __name__ == "__main__":

    llm_client = PerplexityTool()

    host = LLMHost(llm_client)



    user_text = "Le service Auth rencontre une panne critique"

    context = {"existing_incidents": []}



    proposal = host.propose_incident(user_text, context)

    print("=== Proposition LLM ===")

    print(json.dumps(proposal, indent=2, ensure_ascii=False))



    if proposal["status"] == "success":

        graph = host.generate_incident_graph(proposal["result"]["llm_proposal"])

        print("\n=== Graphe pour le front ===")

        print(json.dumps(graph, indent=2, ensure_ascii=False))
