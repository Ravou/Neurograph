# server.py
from neo4j_client import Neo4jConnector
from llm_host_rag import LLMHost, PerplexityTool

# ───────────────────────────────────────────────
# Initialisation Neo4j
# ───────────────────────────────────────────────
neo = Neo4jConnector()
connected = neo.connect()
if not connected:
    print("❌ Impossible de se connecter à Neo4j. Vérifiez le .env")
    exit(1)

# ───────────────────────────────────────────────
# Initialisation LLM Host (RAG-aware)
# ───────────────────────────────────────────────
llm_client = PerplexityTool()
llm_host = LLMHost(llm_client, neo)

# ───────────────────────────────────────────────
# Outils MCP (pour intégrations futures)
# ───────────────────────────────────────────────
def search_context(query: str, limit: int = 5):
    """Outil MCP : Chercher du contexte dans Neo4j"""
    return neo.search_context(query, limit)

def get_relationships(node_id: str):
    """Outil MCP : Récupérer les relations d'un nœud"""
    return neo.get_relationships(node_id)

def save_context(data: dict):
    """Outil MCP : Sauvegarder du nouveau contexte"""
    return neo.save_context(data)

def propose_incident(user_text: str):
    """Outil MCP : Proposer un incident via RAG"""
    context = neo.search_context(user_text)
    return llm_host.propose_incident(user_text, context)

def generate_incident_graph(incident_json: dict):
    """Outil MCP : Générer un graphe pour visualisation"""
    return llm_host.generate_incident_graph(incident_json)

# Export pour utilisation
__all__ = ['neo', 'llm_host', 'search_context', 'get_relationships', 'save_context', 'propose_incident', 'generate_incident_graph']
