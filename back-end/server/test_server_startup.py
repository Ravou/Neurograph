"""
Simple test to verify the MCP server starts correctly
"""

import sys
import os
import asyncio
from pathlib import Path

# On est déjà dans le dossier server, donc server.py est ici
current_dir = Path(__file__).parent

async def test_server_startup():
    """Test that the server can be imported and initialized"""
    print("🧪 Testing MCP Server Startup")
    print("=" * 40)
    
    try:
        # Vérifier d'abord que server.py existe
        server_file = current_dir / "server.py"
        if not server_file.exists():
            print(f"❌ server.py not found at: {server_file}")
            print(f"   Current directory: {current_dir}")
            print(f"   Files in directory: {list(current_dir.glob('*.py'))}")
            return False
        
        print(f"✅ Found server.py at: {server_file}")
        
        # Importer le module directement
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("mcp_server", server_file)
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        
        # Récupérer l'instance du serveur
        server = server_module.server
        print(f"✅ Server instance created: {server.name}")
        
        # Tester le listing des outils
        tools = await server.list_tools()
        print(f"✅ Server lists {len(tools)} tools:")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")
        
        # Tester le connecteur Neo4j
        try:
            connector = server_module.get_connector()
            if connector and hasattr(connector, 'driver'):
                print("✅ Neo4j connector is available")
                
                # Tester une requête simple
                result = connector.run_query("RETURN 'Server test OK' as status")
                print(f"✅ Neo4j query: {result[0]['status']}")
                
                # Fermer la connexion
                connector.close()
                print("✅ Connection closed")
            else:
                print("⚠️  Neo4j connector not fully initialized")
        except Exception as e:
            print(f"⚠️  Neo4j test skipped: {e}")
        
        print("\n🎉 SERVER STARTUP TEST PASSED!")
        print("\n📋 To run the MCP server:")
        print("   python server.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_server_startup())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(130)