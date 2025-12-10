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
    """Retrieve or create the global Neo4j connector with proper error handling."""
    global neo4j_conn
    if neo4j_conn is None:
        neo4j_conn = Neo4jConnector()
        # Ensure connection is established
        if not neo4j_conn.connect():
            print("❌ FATAL: Failed to connect to Neo4j")
            raise ConnectionError("Cannot connect to Neo4j database")
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
                        "description": "Unique identifier (elementId) of the node."
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
                        "description": "Properties attached to the node.",
                        "default": {}
                    },
                    "relations": {
                        "type": "array",
                        "description": "Optional list of relationships to create.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target_id": {
                                    "type": "string",
                                    "description": "Target node elementId"
                                },
                                "type": {
                                    "type": "string", 
                                    "description": "Relationship type"
                                },
                                "properties": {
                                    "type": "object",
                                    "description": "Relationship properties",
                                    "default": {}
                                }
                            },
                            "required": ["target_id", "type"]
                        },
                        "default": []
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
    Includes proper error handling and input validation.
    """
    
    try:
        connector = get_connector()
        
        if name == "search_graph_context":
            query = arguments.get("query")
            if not query or not isinstance(query, str):
                raise ValueError("Search query must be a non-empty string")
            
            limit = arguments.get("limit", 5)
            if not isinstance(limit, int) or limit <= 0:
                limit = 5
            
            print(f"🔍 Search request: '{query}' (limit={limit})")
            result = connector.search_context(query, limit)
        
        elif name == "get_node_relationships":
            node_id = arguments.get("node_id")
            if not node_id or not isinstance(node_id, str):
                raise ValueError("Node ID must be a non-empty string")
            
            print(f"🔗 Fetching relationships for node: {node_id}")
            result = connector.get_relationships(node_id)
        
        elif name == "save_graph_context":
            # Validate required fields
            node_type = arguments.get("type")
            properties = arguments.get("properties", {})
            relations = arguments.get("relations", [])
            
            if not node_type or not isinstance(node_type, str):
                raise ValueError("Node type must be a non-empty string")
            
            if not isinstance(properties, dict):
                raise ValueError("Properties must be a dictionary")
            
            if not isinstance(relations, list):
                relations = []
            
            data = {
                "type": node_type,
                "properties": properties,
                "relations": relations
            }
            
            print(f"💾 Saving node of type: {node_type}")
            result = connector.save_context(data)
        
        else:
            result = {
                "error": f"Unknown tool: {name}",
                "status": "error"
            }
        
        # Sérialiser en JSON avec gestion des types spéciaux
        def json_serializer(obj):
            """Sérialise les objets non-JSON en string"""
            if hasattr(obj, 'iso_format'):
                return obj.iso_format()
            if hasattr(obj, 'to_native'):
                native = obj.to_native()
                if hasattr(native, 'isoformat'):
                    return native.isoformat()
                return native
            raise TypeError(f"Type {type(obj)} not serializable")
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False, default=json_serializer)
            )
        ]
            
    except Exception as e:
        print(f"❌ Error in tool '{name}': {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status": "error",
                    "tool": name
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
    
    try:
        # Initialize connection on startup
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
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user.")
    except Exception as e:
        print(f"\n💥 Server crashed: {e}")
    finally:
        # Ensure clean shutdown
        if neo4j_conn:
            neo4j_conn.close()
        print("🔌 All connections closed.")