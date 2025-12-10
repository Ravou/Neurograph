class Neo4jConnector:
    """
    Stub Neo4j connector for testing MCP server without a real database.
    """

    def connect(self):
        """Simulate connecting to Neo4j."""
        print("🔌 Stub: pretend connected to Neo4j")

    def search_context(self, query, limit=5):
        """Return fake nodes for testing search."""
        print(f"🔍 Stub: search_context called with query='{query}', limit={limit}")
        return [
            {"id": f"node_{i}", "labels": ["Concept"], "properties": {"name": f"Node {i}"}} 
            for i in range(1, limit + 1)
        ]

    def get_relationships(self, node_id):
        """Return fake relationships for testing."""
        print(f"🔗 Stub: get_relationships called with node_id='{node_id}'")
        return [
            {"from": node_id, "to": f"node_{i}", "type": "RELATED_TO", "properties": {}}
            for i in range(1, 4)
        ]

    def save_context(self, data):
        """Simulate saving a node."""
        print(f"💾 Stub: save_context called with data={data}")
        return {
            "node_id": "stub_node_1",
            "labels": [data.get("type", "Concept")],
            "properties": data.get("properties", {}),
            "created_relations": data.get("relations", [])
        }

    def close(self):
        """Simulate closing the connection."""
        print("🔌 Stub: pretend Neo4j connection closed")
