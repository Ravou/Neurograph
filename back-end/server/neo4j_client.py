from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

load_dotenv()

class Neo4jConnector:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        
    def connect(self):
        """Établit la connexion à Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test de connexion
            self.driver.verify_connectivity()
            print("✅ Connecté à Neo4j!")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion Neo4j: {e}")
            return False
    
    def close(self):
        """Ferme la connexion"""
        if self.driver:
            self.driver.close()
            print("🔌 Connexion Neo4j fermée")
    
    def search_context(self, query: str, limit: int = 5):
        """
        FONCTION 1 : Chercher du contexte dans le graph
        
        Args:
            query: La requête de recherche
            limit: Nombre max de résultats
            
        Returns:
            dict: Résultats structurés avec contexte et relations
        """
        with self.driver.session() as session:
            # Query Cypher pour chercher des nœuds pertinents
            # Cherche dans toutes les propriétés string des nœuds
            cypher_query = """
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($query))
            RETURN n, labels(n) as node_type
            LIMIT $limit
            """
            
            try:
                result = session.run(cypher_query, parameters={"query": query, "limit": limit})
                
                nodes = []
                for record in result:
                    node = record["n"]
                    node_data = {
                        "id": node.element_id,
                        "type": record["node_type"],
                        "properties": dict(node)
                    }
                    nodes.append(node_data)
                
                return {
                    "query": query,
                    "found": len(nodes),
                    "results": nodes,
                    "status": "success"
                }
            except Exception as e:
                return {
                    "query": query,
                    "error": str(e),
                    "status": "error"
                }
    
    def get_relationships(self, node_id: str):
        """
        FONCTION 2 : Récupérer les relations d'un nœud
        
        Args:
            node_id: ID du nœud
            
        Returns:
            dict: Relations et nœuds connectés
        """
        with self.driver.session() as session:
            cypher_query = """
            MATCH (n)-[r]-(connected)
            WHERE elementId(n) = $node_id
            RETURN type(r) as relation_type, 
                   connected, 
                   labels(connected) as connected_type
            LIMIT 20
            """
            
            try:
                result = session.run(cypher_query, parameters={"node_id": node_id})
                
                relationships = []
                for record in result:
                    rel_data = {
                        "type": record["relation_type"],
                        "connected_node": {
                            "type": record["connected_type"],
                            "properties": dict(record["connected"])
                        }
                    }
                    relationships.append(rel_data)
                
                return {
                    "node_id": node_id,
                    "relationships": relationships,
                    "count": len(relationships),
                    "status": "success"
                }
            except Exception as e:
                return {
                    "node_id": node_id,
                    "error": str(e),
                    "status": "error"
                }
    
    def save_context(self, data: dict):
        """
        FONCTION 3 : Sauvegarder du nouveau contexte
        
        Args:
            data: Dict avec {type, properties, relations}
            
        Returns:
            dict: Confirmation de sauvegarde
        """
        with self.driver.session() as session:
            try:
                # Créer un nœud de type Context
                node_type = data.get("type", "Context")
                properties = data.get("properties", {})
                
                cypher_query = f"""
                CREATE (n:{node_type} $props)
                RETURN elementId(n) as node_id
                """
                
                result = session.run(cypher_query, parameters={"props": properties})
                record = result.single()
                
                if record:
                    node_id = record["node_id"]
                    
                    # Créer les relations si fournies
                    relations = data.get("relations", [])
                    for rel in relations:
                        self._create_relationship(
                            session,
                            node_id,
                            rel.get("target_id"),
                            rel.get("type", "RELATED_TO")
                        )
                    
                    return {
                        "node_id": node_id,
                        "status": "success",
                        "message": f"Nœud {node_type} créé avec succès"
                    }
                    
            except Exception as e:
                return {
                    "error": str(e),
                    "status": "error"
                }
    
    def _create_relationship(self, session, from_id: str, to_id: str, rel_type: str):
        """Helper pour créer une relation"""
        cypher_query = f"""
        MATCH (a), (b)
        WHERE elementId(a) = $from_id AND elementId(b) = $to_id
        CREATE (a)-[r:{rel_type}]->(b)
        RETURN r
        """
        session.run(cypher_query, parameters={"from_id": from_id, "to_id": to_id})

    # ---------------------------
    # Document / Retrieval helpers
    # ---------------------------
    def store_document(self, content: str, metadata: dict = None, embedding: list = None):
        """Stocke un document (ou chunk) dans le graphe sous le label Document.

        Args:
            content: Texte du document
            metadata: Métadonnées supplémentaires (source, title, etc.)
            embedding: Liste de floats (optionnel)

        Returns:
            dict: {doc_id: elementId}
        """
        with self.driver.session() as session:
            try:
                props = {"content": content}
                if metadata:
                    props.update(metadata)
                if embedding is not None:
                    props["embedding"] = embedding

                cypher = """
                CREATE (d:Document $props)
                RETURN elementId(d) as doc_id
                """
                result = session.run(cypher, parameters={"props": props})
                record = result.single()
                if record:
                    return {"doc_id": record["doc_id"], "status": "success"}
                return {"status": "error", "message": "no record returned"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

    def search_fulltext(self, query: str, limit: int = 10):
        """Recherche fulltext en utilisant l'index `incident_search` (ou document_search si ajouté).

        Retourne une liste d'objets avec id, labels, snippet, score.
        """
        with self.driver.session() as session:
            try:
                cypher = """
                CALL db.index.fulltext.queryNodes("incident_search", $query) YIELD node, score
                RETURN elementId(node) AS id, labels(node) AS labels, node.title AS title, node.description AS description, node.content AS content, score
                ORDER BY score DESC
                LIMIT $limit
                """
                result = session.run(cypher, parameters={"query": query, "limit": limit})
                hits = []
                for record in result:
                    node = {
                        "id": record["id"],
                        "labels": record["labels"],
                        "title": record.get("title"),
                        "description": record.get("description"),
                        "content": record.get("content"),
                        "score": record.get("score")
                    }
                    hits.append(node)
                return {"query": query, "results": hits, "count": len(hits), "status": "success"}
            except Exception as e:
                return {"query": query, "error": str(e), "status": "error"}

    def search_vector(self, query_embedding: list, k: int = 10):
        """Recherche vectorielle.

        Implémente deux stratégies :
        1) Essayer d'utiliser GDS `gds.knn.stream` si disponible dans l'instance Neo4j.
        2) En fallback, récupérer tous les documents avec embeddings et calculer
           la similarité cosine en Python (utile pour petits jeux de données).

        Args:
            query_embedding: liste de floats représentant l'embedding de la requête
            k: nombre de voisins retournés

        Returns:
            dict: {status, results: [ {id, labels, content, score} ... ]}
        """
        if not query_embedding:
            return {"status": "error", "message": "query_embedding required"}

        def _cosine(a, b):
            # a and b are lists/floats
            try:
                import math
                dot = sum(x * y for x, y in zip(a, b))
                na = math.sqrt(sum(x * x for x in a))
                nb = math.sqrt(sum(y * y for y in b))
                if na == 0 or nb == 0:
                    return 0.0
                return dot / (na * nb)
            except Exception:
                return 0.0

        with self.driver.session() as session:
            # 1) Try GDS KNN stream
            try:
                cypher_gds = """
                CALL gds.knn.stream({
                  nodeProjection: 'Document',
                  nodeProperties: ['embedding'],
                  topK: $k,
                  queryVector: $query_embedding
                }) YIELD nodeId, score
                RETURN elementId(gds.util.asNode(nodeId)) AS id,
                       labels(gds.util.asNode(nodeId)) AS labels,
                       gds.util.asNode(nodeId).content AS content,
                       score
                LIMIT $k
                """
                result = session.run(cypher_gds, parameters={"query_embedding": query_embedding, "k": k})
                hits = []
                for record in result:
                    hits.append({
                        "id": record["id"],
                        "labels": record["labels"],
                        "content": record.get("content"),
                        "score": record.get("score")
                    })
                return {"status": "success", "results": hits}
            except Exception as e_gds:
                # GDS not available or call failed -> fallback
                try:
                    cypher_all = """
                    MATCH (d:Document)
                    WHERE exists(d.embedding)
                    RETURN elementId(d) AS id, labels(d) AS labels, d.content AS content, d.embedding AS embedding
                    """
                    result = session.run(cypher_all)
                    docs = []
                    for record in result:
                        docs.append({
                            "id": record["id"],
                            "labels": record["labels"],
                            "content": record.get("content"),
                            "embedding": record.get("embedding")
                        })

                    # Compute cosine similarities
                    scored = []
                    for d in docs:
                        emb = d.get("embedding")
                        if not emb:
                            continue
                        score = _cosine(query_embedding, emb)
                        scored.append((score, d))

                    scored.sort(key=lambda x: x[0], reverse=True)
                    top = []
                    for score, d in scored[:k]:
                        top.append({"id": d["id"], "labels": d["labels"], "content": d.get("content"), "score": score})

                    return {"status": "success", "results": top, "fallback": "python_cosine", "error_gds": str(e_gds)}
                except Exception as e_all:
                    return {"status": "error", "message": f"gds_error: {e_gds}; fallback_error: {e_all}"}

    def get_neighbors_by_element_ids(self, ids: list, depth: int = 1, limit: int = 50):
        """Récupère voisins et relations pour une liste d'elementIds.

        Args:
            ids: liste d'elementId (string)
            depth: profondeur (actuellement non récursive — depth porche)
            limit: limite globale de résultats

        Returns:
            dict: mapping source_id -> list(neighbors)
        """
        with self.driver.session() as session:
            try:
                cypher = """
                UNWIND $ids AS eid
                MATCH (n) WHERE elementId(n) = eid
                MATCH (n)-[r]-(m)
                RETURN eid AS source_id, elementId(m) AS neighbor_id, labels(m) AS neighbor_labels, m AS properties, type(r) AS relation
                LIMIT $limit
                """
                result = session.run(cypher, parameters={"ids": ids, "limit": limit})
                neighbors = {}
                for record in result:
                    src = record["source_id"]
                    item = {
                        "id": record["neighbor_id"],
                        "labels": record["neighbor_labels"],
                        "properties": dict(record["properties"]),
                        "relation": record["relation"]
                    }
                    neighbors.setdefault(src, []).append(item)
                return {"sources": neighbors, "status": "success"}
            except Exception as e:
                return {"error": str(e), "status": "error"}
    
    def init_sample_data(self):
        """Créer des données de test rapides"""
        with self.driver.session() as session:
            # Nettoyer d'abord (ATTENTION en prod!)
            session.run("MATCH (n) DETACH DELETE n")
            
            # Créer des nœuds de test
            session.run("""
            CREATE (p1:Concept {name: 'GraphRAG', description: 'Graph-based Retrieval Augmented Generation'})
            CREATE (p2:Concept {name: 'MCP', description: 'Model Context Protocol'})
            CREATE (p3:Concept {name: 'Neo4j', description: 'Graph Database'})
            CREATE (p4:Technology {name: 'Python', type: 'Programming Language'})
            
            CREATE (p1)-[:USES]->(p3)
            CREATE (p1)-[:IMPLEMENTS]->(p2)
            CREATE (p2)-[:CODED_IN]->(p4)
            """)
            
            print("✅ Données de test créées!")

# Test rapide
if __name__ == "__main__":
    connector = Neo4jConnector()
    
    if connector.connect():
        # Test 1: Créer des données
        print("\n📝 Création de données de test...")
        connector.init_sample_data()
        
        # Test 2: Recherche
        print("\n🔍 Test de recherche...")
        results = connector.search_context("GraphRAG")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Test 3: Relations
        if results["found"] > 0:
            node_id = results["results"][0]["id"]
            print(f"\n🔗 Relations du nœud {node_id}...")
            rels = connector.get_relationships(node_id)
            print(json.dumps(rels, indent=2, ensure_ascii=False))
        
        connector.close()