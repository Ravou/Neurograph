"""
Test MCP tools safely using sandbox nodes in Neo4j
"""

import asyncio
import json
from mcp_server import call_tool

sandbox_nodes = [
    {"type": "Concept", "properties": {"name": "sandbox_node_1"}, "relations": []},
    {"type": "Concept", "properties": {"name": "sandbox_node_2"}, "relations": []},
    {"type": "Concept", "properties": {"name": "sandbox_node_3"}, "relations": []},
]

async def main():
    created_node_ids = []

    # Create sandbox nodes
    for node in sandbox_nodes:
        result = await call_tool("save_graph_context", node)
        node_data = json.loads(result[0].text)
        created_node_ids.append(node_data.get("node_id"))
        print(f"Created {node['properties']['name']} -> {node_data.get('node_id')}")

    # Search sandbox nodes
    result_search = await call_tool("search_graph_context", {"query": "sandbox_node", "limit": 5})
    print("Search result:", json.dumps(result_search[0].text, indent=2))

    # Save a new node with a relation to first node
    new_node = {
        "type": "Concept",
        "properties": {"name": "sandbox_node_new"},
        "relations": [{"target_id": created_node_ids[0], "type": "RELATED_TO"}]
    }
    result_save = await call_tool("save_graph_context", new_node)
    print("Saved new node:", json.dumps(result_save[0].text, indent=2))

    # Get relationships of first sandbox node
    result_rel = await call_tool("get_node_relationships", {"node_id": created_node_ids[0]})
    print("Relationships:", json.dumps(result_rel[0].text, indent=2))

if __name__ == "__main__":
    asyncio.run(main())