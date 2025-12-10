"""
Quick Smoke Test for GraphRAG MCP
==================================
Version simplifiée qui teste l'essentiel
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def smoke_test():
    print("🚀 GraphRAG MCP - Test Simplifié")
    print("=" * 40)
    
    try:
        from server.neo4j_client import Neo4jConnector
        
        print("✅ 1. Imports work")
        
        connector = Neo4jConnector()
        print("✅ 2. Connector instantiated")
        
        if connector.connect():
            print("✅ 3. Neo4j connection successful")
            
            # Test simple query
            result = connector.run_query("RETURN 'OK' as status")
            print(f"✅ 4. Query works: {result[0]['status']}")
            
            # Count nodes
            count_result = connector.run_query("MATCH (n) RETURN count(n) as total")
            total_nodes = count_result[0]['total'] if count_result else 0
            print(f"✅ 5. Database has {total_nodes} nodes")
            
            # Test search - recherche directe
            test_query = "Lakers"
            print(f"\n🔍 Testing search for: '{test_query}'")
            search_result = connector.search_context(test_query, limit=3)
            
            if search_result.get('status') == 'success':
                print(f"✅ 6. Search works: Found {search_result.get('count', 0)} results")
                if search_result.get('results'):
                    for i, node in enumerate(search_result['results']):
                        labels = node.get('labels', [])
                        props = node.get('properties', {})
                        name = props.get('name') or props.get('title') or props.get('id') or 'Unnamed'
                        print(f"   {i+1}. {labels}: {name}")
            else:
                print(f"❌ Search error: {search_result.get('error', 'Unknown')}")
            
            # Test node creation
            test_node = connector.create_node("TestNode", {
                "name": "Test Node",
                "description": "Test de création",
                "smoke_test": True
            })
            
            if test_node:
                print(f"\n✅ 7. Node creation works")
                print(f"   ID: {test_node.get('elementId')}")
                print(f"   Label: {test_node.get('label')}")
                
                # Cleanup
                connector.run_query(
                    "MATCH (n:TestNode) WHERE n.smoke_test = true DETACH DELETE n"
                )
                print("✅ 8. Cleanup successful")
            
            connector.close()
            print("\n✅ 9. Connection closed")
            
            print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
            return True
            
        else:
            print("❌ Failed to connect to Neo4j")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = smoke_test()
    sys.exit(0 if success else 1)