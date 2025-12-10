import asyncio
import json
from mcp_server import call_tool  # ton serveur MCP renommé
from neo4j_client import Neo4jConnector

async def test_tool_calls():
    # On simule la connexion Neo4j
    connector = Neo4jConnector()
    connector.connect()

    # Liste des tool calls à tester
    tests = [
        {
            "name": "search_graph_context",
            "arguments": {"query": "test", "limit": 3}
        },
        {
            "name": "get_node_relationships",
            "arguments": {"node_id": "node_1"}
        },
        {
            "name": "save_graph_context",
            "arguments": {"type": "Concept", "properties": {"name": "New Node"}, "relations": []}
        }
    ]

    for t in tests:
        print(f"\n🛠 Testing tool: {t['name']}")
        result = await call_tool(t['name'], t['arguments'])
        for r in result:
            print(json.dumps(r.text, indent=2, ensure_ascii=False))

asyncio.run(test_tool_calls())
