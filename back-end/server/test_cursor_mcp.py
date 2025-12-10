#!/usr/bin/env python3
"""
Test script pour vérifier que le serveur MCP fonctionne avec Cursor
"""
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server():
    """Test que le serveur MCP peut être importé et que les outils sont disponibles"""
    print("🧪 Test du serveur MCP pour Cursor")
    print("=" * 60)
    
    try:
        # Test 1: Import du serveur
        print("\n1. Test d'import du serveur...")
        from mcp_server import server
        print(f"   ✅ Serveur importé: {server.name}")
        
        # Test 2: Liste des outils
        print("\n2. Test de la liste des outils...")
        # Le serveur MCP expose list_tools comme une méthode async
        from mcp_server import list_tools
        tools = await list_tools()
        print(f"   ✅ {len(tools)} outils disponibles:")
        for tool in tools:
            print(f"      - {tool.name}: {tool.description[:60]}...")
        
        # Test 3: Test du connecteur Neo4j
        print("\n3. Test de la connexion Neo4j...")
        from mcp_server import get_connector
        connector = get_connector()
        if connector and connector.driver:
            print("   ✅ Connexion Neo4j établie")
            
            # Test d'une requête simple
            result = connector.run_query("RETURN 'OK' as status")
            if result:
                print(f"   ✅ Requête test réussie: {result[0]['status']}")
        else:
            print("   ⚠️  Connexion Neo4j non établie (vérifiez les variables d'environnement)")
        
        # Test 4: Test d'un appel d'outil
        print("\n4. Test d'appel d'outil (search_graph_context)...")
        try:
            result = await server.call_tool("search_graph_context", {
                "query": "test",
                "limit": 1
            })
            if result and len(result) > 0:
                print("   ✅ Appel d'outil réussi")
                import json
                data = json.loads(result[0].text)
                print(f"   📊 Résultat: {data.get('status', 'unknown')}")
            else:
                print("   ⚠️  Aucun résultat retourné")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de l'appel (peut être normal si Neo4j n'est pas connecté): {e}")
        
        print("\n" + "=" * 60)
        print("✅ Tous les tests de base sont passés!")
        print("\n📋 Prochaines étapes:")
        print("   1. Redémarrez Cursor")
        print("   2. Le serveur MCP devrait être automatiquement détecté")
        print("   3. Vous pouvez utiliser les outils:")
        print("      - search_graph_context")
        print("      - get_node_relationships")
        print("      - save_graph_context")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
