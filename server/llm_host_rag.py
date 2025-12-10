# llm_host_rag.py
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
        self.endpoint = os.getenv("PERPLEXITY_ENDPOINT", "https://api.perplexity.ai/v1/ask")  # Adapter si nécessaire

    def ask(self, prompt: str) -> str:
        """Envoie un prompt au LLM et retourne la réponse brute."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Adapter selon le shape de la réponse du provider
            return data.get("answer", data.get("text", json.dumps(data)))
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur Perplexity API: {e}")
            return f"Erreur LLM: {e}"


# ──────────────────────────────
# LLM Host (RAG)
# ──────────────────────────────
class LLMHost:
    """
    Host pour LLM Perplexity + augmentation + génération
    Retourne toujours des réponses JSON-RPC
    """
    def __init__(self, llm_client, neo_client=None):
        self.llm = llm_client
        self.neo = neo_client

    # -----------------------------
    # RAG helpers
    # -----------------------------
    def embed_text(self, text: str):
        """Stub d'embedding.

        Tente d'utiliser une implémentation d'embeddings définie par les vars d'env
        (ex: OPENAI_API_KEY). Si aucune clé présente, retourne None.
        Remplacez/implémentez selon votre fournisseur d'embeddings.
        """
        embedding_key = os.getenv("OPENAI_API_KEY")
        if not embedding_key:
            # Pas de provider configuré — retourner None pour indiquer fallback
            print("⚠️ No embedding API key found (OPENAI_API_KEY). Falling back to lexical retrieval.")
            return None

        try:
            headers = {"Authorization": f"Bearer {embedding_key}", "Content-Type": "application/json"}
            body = {"input": text, "model": os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")}
            resp = requests.post(os.getenv("EMBEDDING_ENDPOINT", "https://api.openai.com/v1/embeddings"), headers=headers, json=body, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            emb = data.get("data", [])[0].get("embedding")
            return emb
        except Exception as e:
            print(f"⚠️ Embedding request failed: {e}")
            return None

    def retrieve_documents(self, text: str, top_k: int = 8):
        """Retrieval hybride: fulltext fallback -> (vector si disponible).

        Renvoie une liste de documents (dictionnaires) triés par pertinence.
        """
        # Calculer embedding si possible
        emb = self.embed_text(text)

        # Try vector search if we have an embedding
        docs = []
        if emb is not None and self.neo is not None:
            vec_res = self.neo.search_vector(emb, k=top_k * 3)
            if vec_res.get("status") == "success":
                docs = vec_res.get("results", [])
            else:
                # fallback vers fulltext
                docs = self.neo.search_fulltext(text, limit=top_k * 3).get("results", [])
        else:
            if self.neo is not None:
                docs = self.neo.search_fulltext(text, limit=top_k * 3).get("results", [])
            else:
                docs = []

        # Simple truncation / dedup and pick top_k
        seen = set()
        out = []
        for d in docs:
            doc_id = d.get("id")
            if doc_id in seen:
                continue
            seen.add(doc_id)
            out.append(d)
            if len(out) >= top_k:
                break

        return out

    def expand_with_graph(self, node_ids: list, hops: int = 1):
        """Recupère voisins depuis Neo4j pour enrichir le contexte."""
        if not node_ids:
            return {"sources": {}, "status": "empty"}
        if self.neo is None:
            return {"sources": {}, "status": "no_neo_client"}
        return self.neo.get_neighbors_by_element_ids(node_ids, depth=hops)

    def build_prompt(self, user_text: str, docs: list, graph_ctx: dict, token_limit: int = 2000) -> str:
        """Construit un prompt d'augmentation à partir des documents et du graph context.

        Cette fonction doit être prudente sur la taille (tronquer les documents si nécessaire).
        """
        pieces = ["System: Vous êtes un assistant qui doit synthétiser un incident à partir du contexte fourni."]
        pieces.append(f"Utilisateur: {user_text}")

        pieces.append("-- CONTEXTE : Documents pertinents --")
        for i, d in enumerate(docs, start=1):
            content = d.get("content") or d.get("description") or d.get("title") or ""
            # Truncate to ~1000 chars to avoid very long prompts
            if len(content) > 1000:
                content = content[:1000] + "..."
            pieces.append(f"[DOC {i}] {content}")

        pieces.append("-- CONTEXTE : Graph neighbours --")
        try:
            pieces.append(json.dumps(graph_ctx, indent=2, ensure_ascii=False))
        except Exception:
            pieces.append(str(graph_ctx))

        pieces.append("Répondez par un JSON structuré contenant: type, services, teams, runbooks, relations.")

        prompt = "\n\n".join(pieces)
        return prompt

    def propose_incident(self, user_text: str, context: dict) -> dict:
        """Pipeline RAG complet : embed -> retrieve -> expand -> prompt -> LLM."""
        try:
            # 1) Retrieval
            docs = self.retrieve_documents(user_text, top_k=8)

            # 2) Expand via graph neighbors
            node_ids = [d.get("id") for d in docs if d.get("id")]
            graph_ctx = self.expand_with_graph(node_ids, hops=1)

            # 3) Build prompt
            prompt = self.build_prompt(user_text, docs, graph_ctx)

            # 4) Call LLM
            llm_result_str = self.llm.ask(prompt)

            # 5) Try to parse JSON, else return raw text in the 'text' field
            try:
                llm_json = json.loads(llm_result_str)
            except json.JSONDecodeError:
                llm_json = {"text": llm_result_str}

            return {
                "jsonrpc": "2.0",
                "result": {
                    "llm_proposal": llm_json,
                    "documents": docs,
                    "graph_context": graph_ctx
                },
                "status": "success"
            }
        except Exception as e:
            return {"jsonrpc": "2.0", "error": str(e), "status": "error"}

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
