"""
MCP SERVER - GraphRAG with Neo4j
================================

This server exposes a set of graph-related tools over MCP.
It acts as a bridge between an LLM and a Neo4j knowledge graph.
"""
from mcp.server import Server
from neo4j_client import Neo4jConnector
from mcp.types import Tool, TextContent
import json
import asyncio

# MCP server instance
server = Server("graphrag-neo4j-server")

# Global Neo4j connection
neo4j_conn = None

def get_connector():
    """Retrieve or create the global Neo4j connector."""
    global neo4j_conn
    if neo4j_conn is None:
        neo4j_conn = Neo4jConnector()
        neo4j_conn.connect()
    return neo4j_conn

# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available MCP tools.
    """
    return [
        Tool(
            name="search_graph_context",
            description="Searches for contextual information in the Neo4j graph based on user-provided keywords or concepts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search phrase or keywords."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of returned results.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        
        Tool(
            name="get_node_relationships",
            description="Retrieves all relationships of a specific node.",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Unique identifier of the node."
                    }
                },
                "required": ["node_id"]
            }
        ),
        
        Tool(
            name="save_graph_context",
            description="Adds a new node and optional relationships to the graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Label/type of the new node."
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties attached to the node."
                    },
                    "relations": {
                        "type": "array",
                        "description": "Optional list of relationships to create.",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["type", "properties"]
            }
        )
    ]

# ============================================================================
# TOOL EXECUTION LOGIC
# ============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Executes the requested tool with the provided arguments.
    """
    
    connector = get_connector()
    
    try:
        if name == "search_graph_context":
            query = arguments.get("query")
            limit = arguments.get("limit", 5)
            
            print(f"🔍 Search request: '{query}' (limit={limit})")
            result = connector.search_context(query, limit)
        
        elif name == "get_node_relationships":
            node_id = arguments.get("node_id")
            
            print(f"🔗 Fetching relationships for node: {node_id}")
            result = connector.get_relationships(node_id)
        
        elif name == "save_graph_context":
            data = {
                "type": arguments.get("type"),
                "properties": arguments.get("properties"),
                "relations": arguments.get("relations", [])
            }
            
            print(f"💾 Saving node of type: {data['type']}")
            result = connector.save_context(data)
        
        else:
            result = {
                "error": f"Unknown tool: {name}",
                "status": "error"
            }
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )
        ]
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status": "error"
                })
            )
        ]

# ============================================================================
# SERVER STARTUP
# ============================================================================

async def main():
    """Main entry point of the MCP server."""
    print("=" * 60)
    print("🚀 MCP GraphRAG Server - Starting...")
    print("=" * 60)
    
    get_connector()
    
    print("\n✅ Server ready.")
    print("📡 Waiting for MCP connections...")
    print("=" * 60)
    
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        if neo4j_conn:
            neo4j_conn.close()
