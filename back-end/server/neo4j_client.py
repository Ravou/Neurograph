import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import uuid

load_dotenv()

class Neo4jConnector:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self.session = None  # <- ajouté

    def connect(self):
        """Establish a connection to Neo4j."""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.session = self.driver.session()  # <- ajoute la session
        print("✅ Connected to Neo4j")

    def close(self):
        """Close the Neo4j connection."""
        if self.session:
            self.session.close()
            self.session = None
        if self.driver:
            self.driver.close()
            self.driver = None
        print("🔌 Neo4j connection closed")

    def run_query(self, query, params=None):
        """Run a Cypher query and return results as a list of dicts."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    # -------------------------------------------------------------------------
    # MCP TOOLS METHODS
    # -------------------------------------------------------------------------

    def search_context(self, query: str, limit: int = 5):
        cypher = """
        MATCH (n)
        UNWIND keys(n) AS k
        WITH n, k, n[k] AS v
        WHERE v IS NOT NULL AND (
            (v CONTAINS $query) OR
            (v = $query)
        )
        RETURN DISTINCT n LIMIT $limit
        """
        return self.run_query(cypher, {"query": query, "limit": limit})

    def get_relationships(self, element_id: str):
        query = """
        MATCH (n)-[r]->(m)
        WHERE n.elementId = $element_id
        RETURN n, r, m
        """
        result = self.session.run(query, {"element_id": element_id})

        relationships = []
        for record in result:
            n = record["n"]
            r = record["r"]
            m = record["m"]
            relationships.append({
                "from": n["elementId"],
                "to": m["elementId"],
                "type": type(r).__name__ if r else "RELATED_TO",
                "properties": dict(r) if r else {}
            })
        return relationships

    def save_context(self, data: dict):
        element_id = str(uuid.uuid4())
        labels = data.get("type")
        properties = data.get("properties", {})
        properties["elementId"] = element_id

        # Create node
        query = f"""
        CREATE (n:{labels} $properties)
        RETURN n
        """
        result = self.session.run(query, properties=properties)
        created_node = result.single()["n"]

        # Create relationships
        relations = []
        for rel in data.get("relations", []):
            target_id = rel.get("target_id")
            rel_type = rel.get("type", "RELATED_TO")
            if target_id:
                rel_query = f"""
                MATCH (a {{elementId: $source_id}}), (b {{elementId: $target_id}})
                CREATE (a)-[r:{rel_type}]->(b)
                RETURN r
                """
                self.session.run(rel_query, {"source_id": element_id, "target_id": target_id})
                relations.append([element_id, rel_type, target_id])

        return {
            "elementId": element_id,
            "labels": [labels],
            "properties": properties,
            "created_relations": relations
        }
