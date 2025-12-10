# main.py
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from server import neo, llm_host
import json

# ───────────────────────────────────────────────
# Initialisation FastAPI
# ───────────────────────────────────────────────
app = FastAPI(title="Neurograph API", version="1.0.0")

# ───────────────────────────────────────────────
# Servir les fichiers statiques
# ───────────────────────────────────────────────
# Chemin absolu vers le dossier front
front_dir = Path(__file__).parent.parent / "front"
app.mount("/", StaticFiles(directory=str(front_dir), html=True), name="static")

# ───────────────────────────────────────────────
# Endpoints API
# ───────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Vérifier que l'API est en ligne"""
    return {"status": "ok", "message": "Neurograph API is running"}

@app.post("/api/mcp/query")
async def mcp_query(req: Request):
    """
    Endpoint principal : Recherche Neo4j + LLM
    Attend: { "query": "...", "type": "neo4j" }
    """
    try:
        data = await req.json()
        user_query = data.get("query", "")
        
        if not user_query.strip():
            return {"status": "error", "message": "Query is empty"}
        
        # Recherche contexte dans Neo4j
        context = neo.search_context(user_query)
        
        # Propose incident via LLM
        proposal = llm_host.propose_incident(user_query, context)
        
        # Génère graphe pour le front
        if proposal.get("status") == "success":
            graph = llm_host.generate_incident_graph(proposal.get("result", {}).get("llm_proposal", {}))
            return {
                "status": "success",
                "query": user_query,
                "report": json.dumps(proposal.get("result", {}), ensure_ascii=False),
                "graphData": graph.get("result", {}).get("graph", {})
            }
        else:
            return proposal
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/query_incident")
async def query_incident(req: Request):
    """Propose un incident basé sur une requête utilisateur"""
    try:
        data = await req.json()
        user_input = data.get("query")
        
        context = neo.search_context(user_input)
        result = llm_host.propose_incident(user_input, context)
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/validate_incident")
async def validate_incident(req: Request):
    """Valide et sauvegarde un incident dans Neo4j"""
    try:
        data = await req.json()
        incident_data = data.get("incident")
        
        result = neo.save_context(incident_data)
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate_graph")
async def generate_graph(req: Request):
    """Génère un graphe pour visualisation"""
    try:
        data = await req.json()
        incident_json = data.get("incident")
        
        graph_result = llm_host.generate_incident_graph(incident_json)
        
        return graph_result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/search")
async def search(q: str = "", limit: int = 5):
    """Recherche simple dans Neo4j"""
    try:
        if not q.strip():
            return {"status": "error", "message": "Query parameter is required"}
        
        result = neo.search_context(q, limit)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ───────────────────────────────────────────────
# Lancement du serveur
# ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("🚀 Neurograph API server starting...")
    print("📍 Frontend: http://localhost:8000")
    print("📍 API: http://localhost:8000/api")
    uvicorn.run(app, host="0.0.0.0", port=8000)
