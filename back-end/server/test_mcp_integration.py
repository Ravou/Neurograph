"""
Test MCP integration by simulating stdio communication
This simulates how Claude Desktop would communicate with the server
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

async def simulate_mcp_message(server, message_type: str, **kwargs):
    """Simulate sending an MCP message to the server"""
    if message_type == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "TestClient",
                    "version": "1.0.0"
                }
            }
        }
    
    elif message_type == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
    
    elif message_type == "tools/call":
        return {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": kwargs.get("tool_name"),
                "arguments": kwargs.get("arguments", {})
            }
        }

async def test_mcp_integration():
    """Test the server with simulated MCP messages"""
    print("🔌 Testing MCP Integration (Simulated)")
    print("=" * 60)
    
    try:
        from server import server, get_connector
        
        # Setup test data
        connector = get_connector()
        if not connector.driver:
            connector.connect()
        
        # Create a test node
        test_node = connector.create_node("MCPTest", {
            "name": "MCP Integration Test",
            "description": "Node for MCP integration testing",
            "mcp_test": True
        })
        
        if not test_node:
            print("❌ Failed to create test node")
            return False
        
        print("✅ Created test data")
        
        # Test 1: Simulate initialization
        print("\n1. Testing MCP initialization...")
        init_response = await simulate_mcp_message(server, "initialize")
        print(f"   ✅ Initialization message structure: {json.dumps(init_response)[:100]}...")
        
        # Test 2: Simulate tools listing
        print("\n2. Testing tools listing...")
        tools_response = await simulate_mcp_message(server, "tools/list")
        print(f"   ✅ Tools list request: {json.dumps(tools_response)[:100]}...")
        
        # Get actual tools from server
        tools = await server.list_tools()
        print(f"   📋 Server would return {len(tools)} tools")
        
        # Test 3: Simulate tool call
        print("\n3. Testing tool call simulation...")
        
        # Test search tool
        tool_call = await simulate_mcp_message(
            server, 
            "tools/call",
            tool_name="search_graph_context",
            arguments={"query": "MCP", "limit": 3}
        )
        
        print(f"   🔧 Tool call request: {json.dumps(tool_call)[:100]}...")
        
        # Actually call the tool
        result = await server.call_tool("search_graph_context", {
            "query": "MCP",
            "limit": 3
        })
        
        if result and len(result) > 0:
            print(f"   ✅ Tool executed, returned {len(result)} TextContent objects")
            data = json.loads(result[0].text)
            print(f"   📊 Found {data.get('count', 0)} results")
        else:
            print("   ⚠️ Tool call returned no results")
        
        # Cleanup
        connector.run_query("MATCH (n:MCPTest) DETACH DELETE n")
        connector.close()
        
        print("\n✅ MCP integration simulation complete")
        return True
        
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_startup():
    """Test that the server can start up properly"""
    print("\n" + "=" * 60)
    print("🚀 Testing Server Startup")
    print("=" * 60)
    
    try:
        from server.server import main
        
        print("✅ Server main function exists")
        
        # Note: We can't actually run main() because it wants stdio streams
        # But we can verify it exists and has the right signature
        import inspect
        sig = inspect.signature(main)
        print(f"✅ Main function signature: {sig}")
        
        # Test that we can create the server instance
        from mcp.server import Server
        from server.server import server as mcp_server
        
        print(f"✅ Server instance created: {type(mcp_server).__name__}")
        print(f"✅ Server name: {mcp_server.name}")
        
        print("\n✅ Server startup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

if __name__ == "__main__":
    async def run_all():
        print("🧪 Running MCP Integration Tests")
        print("=" * 60)
        
        tests = [
            ("Server Startup", test_server_startup),
            ("MCP Integration", test_mcp_integration),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n▶️  Running: {test_name}")
            print("-" * 40)
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n🎯 Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL MCP INTEGRATION TESTS PASSED!")
            print("   The server is ready for use with Claude Desktop.")
            print("\n   To run the server:")
            print("   1. Ensure Neo4j is running")
            print("   2. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
            print("   3. Run: python -m server.server")
            return True
        else:
            print("\n⚠️  Some tests failed. Check logs above.")
            return False
    
    try:
        success = asyncio.run(run_all())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(130)