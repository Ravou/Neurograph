"""
Master test script - runs all GraphRAG MCP tests
"""

import subprocess
import sys
from pathlib import Path

def run_test(test_name, script_path):
    """Run a test script and return success/failure"""
    print(f"\n{'='*60}")
    print(f"🧪 RUNNING: {test_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {test_name}: PASSED")
            return True
        else:
            print(f"❌ {test_name}: FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name}: TIMEOUT (30 seconds)")
        return False
    except Exception as e:
        print(f"💥 {test_name}: ERROR - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 GraphRAG MCP - Comprehensive Test Suite")
    print("=" * 60)
    
    test_dir = Path(__file__).parent
    tests = [
        ("Smoke Test", test_dir / "test_smoke.py"),
        ("Server End-to-End", test_dir / "test_server_end_to_end.py"),
        ("MCP Integration", test_dir / "test_mcp_integration.py"),
    ]
    
    # Check if test files exist
    for test_name, test_path in tests:
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            tests.remove((test_name, test_path))
    
    if not tests:
        print("❌ No test files found!")
        return False
    
    results = []
    
    for test_name, test_path in tests:
        success = run_test(test_name, test_path)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The GraphRAG MCP Server is ready.")
        print("\n📋 NEXT STEPS:")
        print("1. Add the server to Claude Desktop config:")
        print("""
   "mcpServers": {
     "graphrag-neo4j": {
       "command": "python",
       "args": ["/path/to/your/server/server.py"],
       "env": {
         "NEO4J_URI": "bolt://localhost:7687",
         "NEO4J_USER": "neo4j",
         "NEO4J_PASSWORD": "your_password"
       }
     }
   }
""")
        print("2. Restart Claude Desktop")
        print("3. Use tools: search_graph_context, get_node_relationships, save_graph_context")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)