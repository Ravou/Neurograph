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
        self.endpoint = "https://api.perplexity.ai/v1/ask"  # Adapter si nécessaire

    def ask(self, prompt: str) -> str:
        """Envoie un prompt au LLM et retourne la réponse brute."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get("answer", "")
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
            "Propose un JSON structuré pour l'incident avec :\n"
            "- type d'incident\n"
            "- services impactés\n"
            "- équipes responsables\n"
            "- runbooks éventuels\n"
            "- relations AFFECTS / OWNED_BY / HAS_RUNBOOK"
        )

    def propose_incident(self, user_text: str, context: dict) -> dict:
        """Appelle le LLM pour proposer un incident JSON (JSON-RPC)."""
        try:
            prompt = self.generate_prompt(user_text, context)
            llm_result_str = self.llm.ask(prompt)

            try:
                llm_json = json.loads(llm_result_str)
            except json.JSONDecodeError:
                llm_json = {"text": llm_result_str}

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