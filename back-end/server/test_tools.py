"""
Test Tools for MCP GraphRAG Server
===================================
Tests all MCP tools directly without requiring Claude Desktop
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from server.neo4j_client import Neo4jConnector

class GraphRAGTester:
    """Test all GraphRAG MCP tools"""
    
    def __init__(self):
        self.connector = Neo4jConnector()
        
    def setup(self):
        """Initialize test environment"""
        print("=" * 60)
        print("🧪 GRAPHRAG MCP SERVER - TEST TOOLS")
        print("=" * 60)
        
        # Connect to Neo4j
        if not self.connector.connect():
            print("❌ Failed to connect to Neo4j")
            return False
        
        # Create test data
        self.create_test_data()
        
        return True
    
    def create_test_data(self):
        """Create initial test data if needed"""
        print("\n📝 Checking/Creating test data...")
        
        # Check if we have data
        check_query = """
        MATCH (n) 
        RETURN count(n) as node_count
        LIMIT 1
        """
        
        result = self.connector.run_query(check_query)
        node_count = result[0]["node_count"] if result else 0
        
        if node_count == 0:
            print("📦 Creating sample test data...")
            self.create_sample_data()
        else:
            print(f"✅ Database has {node_count} nodes already")
    
    def create_sample_data(self):
        """Create sample data for testing"""
        # Create teams
        devops = self.connector.create_node("Team", {
            "name": "DevOps Team",
            "email": "devops@company.com",
            "slack": "#devops",
            "description": "Infrastructure and operations"
        })
        
        backend = self.connector.create_node("Team", {
            "name": "Backend Team",
            "email": "backend@company.com",
            "slack": "#backend",
            "description": "API and services development"
        })
        
        # Create services
        payment = self.connector.create_node("Service", {
            "name": "Payment Service",
            "description": "Handles payment processing",
            "status": "operational",
            "tier": 1,
            "version": "2.3.1"
        })
        
        auth = self.connector.create_node("Service", {
            "name": "Authentication Service",
            "description": "User authentication and authorization",
            "status": "operational",
            "tier": 1,
            "version": "1.5.0"
        })
        
        database = self.connector.create_node("Service", {
            "name": "Main Database",
            "description": "Primary PostgreSQL database",
            "status": "operational",
            "tier": 1,
            "engine": "PostgreSQL 14"
        })
        
        # Create incidents
        incident1 = self.connector.create_node("Incident", {
            "title": "Payment Processing Outage",
            "description": "Payment service is failing to process transactions",
            "severity": "high",
            "status": "resolved",
            "created_at": "2024-01-15T10:30:00",
            "resolved_at": "2024-01-15T12:45:00",
            "root_cause": "Database connection pool exhaustion"
        })
        
        incident2 = self.connector.create_node("Incident", {
            "title": "Authentication Service Latency",
            "description": "High latency in user authentication requests",
            "severity": "medium",
            "status": "investigating",
            "created_at": "2024-01-20T14:20:00"
        })
        
        # Create runbooks
        runbook1 = self.connector.create_node("Runbook", {
            "title": "Payment Service Recovery",
            "description": "Steps to recover payment service",
            "steps": [
                "1. Check database connectivity",
                "2. Verify payment gateway API",
                "3. Restart payment service pods",
                "4. Monitor transaction success rate"
            ],
            "estimated_time": "30 minutes"
        })
        
        # Create relationships
        self.connector.create_relationship(
            from_element_id=payment["elementId"],
            to_element_id=devops["elementId"],
            rel_type="OWNED_BY"
        )
        
        self.connector.create_relationship(
            from_element_id=auth["elementId"],
            to_element_id=backend["elementId"],
            rel_type="OWNED_BY"
        )
        
        self.connector.create_relationship(
            from_element_id=incident1["elementId"],
            to_element_id=payment["elementId"],
            rel_type="AFFECTS"
        )
        
        self.connector.create_relationship(
            from_element_id=incident1["elementId"],
            to_element_id=database["elementId"],
            rel_type="AFFECTS"
        )
        
        self.connector.create_relationship(
            from_element_id=payment["elementId"],
            to_element_id=runbook1["elementId"],
            rel_type="HAS_RUNBOOK"
        )
        
        print("✅ Sample test data created")
    
    def test_search_context(self):
        """Test search_graph_context tool"""
        print("\n" + "=" * 60)
        print("🔍 TEST 1: search_graph_context")
        print("=" * 60)
        
        tests = [
            {"query": "payment", "limit": 3, "expected": "Find payment-related nodes"},
            {"query": "database", "limit": 2, "expected": "Find database-related nodes"},
            {"query": "outage", "limit": 5, "expected": "Find outage incidents"}
        ]
        
        for test in tests:
            print(f"\n📤 Query: '{test['query']}' (limit: {test['limit']})")
            print(f"🎯 Expected: {test['expected']}")
            
            result = self.connector.search_context(test["query"], test["limit"])
            
            print(f"📥 Result: Found {result.get('count', 0)} nodes")
            
            if result.get("status") == "success":
                print("✅ PASS")
                if result.get("results"):
                    for i, node in enumerate(result["results"][:2]):  # Show first 2
                        print(f"   {i+1}. {node.get('labels', [])}: {node.get('properties', {}).get('name') or node.get('properties', {}).get('title')}")
            else:
                print(f"❌ FAIL: {result.get('error', 'Unknown error')}")
            
            print("-" * 40)
    
    def test_get_relationships(self):
        """Test get_node_relationships tool"""
        print("\n" + "=" * 60)
        print("🔗 TEST 2: get_node_relationships")
        print("=" * 60)
        
        # First, find a node to test
        search_result = self.connector.search_context("payment", limit=1)
        
        if not search_result.get("results"):
            print("❌ No nodes found to test relationships")
            return
        
        node_id = search_result["results"][0]["elementId"]
        node_name = search_result["results"][0]["properties"].get("name") or \
                    search_result["results"][0]["properties"].get("title") or \
                    "Unknown"
        
        print(f"📤 Testing relationships for node: {node_name}")
        print(f"🆔 Node ID: {node_id}")
        
        result = self.connector.get_relationships(node_id)
        
        print(f"📥 Result: Found {result.get('count', 0)} relationships")
        
        if result.get("status") == "success":
            print("✅ PASS")
            if result.get("relationships"):
                for i, rel in enumerate(result["relationships"][:3]):  # Show first 3
                    print(f"   {i+1}. {rel.get('direction')} -> {rel.get('type')}")
        else:
            print(f"❌ FAIL: {result.get('error', 'Unknown error')}")
    
    def test_save_context(self):
        """Test save_graph_context tool"""
        print("\n" + "=" * 60)
        print("💾 TEST 3: save_graph_context")
        print("=" * 60)
        
        # Create a test incident
        test_data = {
            "type": "Incident",
            "properties": {
                "title": "Test API Gateway Timeout",
                "description": "API gateway experiencing timeouts for 5% of requests",
                "severity": "medium",
                "status": "investigating",
                "created_at": "2024-01-25T09:15:00",
                "test_data": True  # Mark as test data for cleanup
            }
        }
        
        print("📤 Creating test incident...")
        result = self.connector.save_context(test_data)
        
        print(f"📥 Result: {result.get('status', 'unknown')}")
        print(f"💡 Message: {result.get('message', 'No message')}")
        
        if result.get("status") == "success":
            print("✅ PASS - Node created successfully")
            print(f"   🆔 Created node ID: {result.get('node', {}).get('elementId')}")
            
            # Verify the node was created
            node_id = result.get('node', {}).get('elementId')
            if node_id:
                verify_result = self.connector.get_relationships(node_id)
                print(f"   🔍 Node has {verify_result.get('count', 0)} relationships")
        else:
            print(f"❌ FAIL: {result.get('message', 'Unknown error')}")
    
    def test_create_node_and_relationship(self):
        """Test create_node and create_relationship helpers"""
        print("\n" + "=" * 60)
        print("🛠️  TEST 4: Direct Neo4j Helpers")
        print("=" * 60)
        
        # Test create_node
        print("📤 Creating a Team node...")
        team = self.connector.create_node("Team", {
            "name": "Test Team",
            "description": "Created by test script",
            "test": True
        })
        
        if team:
            print("✅ Node created:")
            print(f"   🆔 ID: {team.get('elementId')}")
            print(f"   📛 Label: {team.get('label')}")
            
            # Test create_relationship
            # First find a service to connect to
            search_result = self.connector.search_context("service", limit=1)
            if search_result.get("results"):
                service_id = search_result["results"][0]["elementId"]
                service_name = search_result["results"][0]["properties"].get("name", "Unknown")
                
                print(f"📤 Creating relationship to: {service_name}")
                
                success = self.connector.create_relationship(
                    from_element_id=team["elementId"],
                    to_element_id=service_id,
                    rel_type="MANAGES",
                    properties={"since": "2024-01-01"}
                )
                
                if success:
                    print("✅ Relationship created successfully")
                else:
                    print("❌ Failed to create relationship")
        else:
            print("❌ Failed to create node")
    
    def test_run_query(self):
        """Test direct Cypher query execution"""
        print("\n" + "=" * 60)
        print("🔄 TEST 5: run_query helper")
        print("=" * 60)
        
        queries = [
            {
                "name": "Count all nodes",
                "query": "MATCH (n) RETURN count(n) as total_nodes",
                "params": {}
            },
            {
                "name": "Get all node labels",
                "query": """
                CALL db.labels() YIELD label
                RETURN collect(label) as labels, count(label) as label_count
                """,
                "params": {}
            },
            {
                "name": "Find high severity incidents",
                "query": """
                MATCH (i:Incident)
                WHERE i.severity = 'high'
                RETURN i.title as title, i.status as status, i.created_at as created
                ORDER BY i.created_at DESC
                LIMIT 3
                """,
                "params": {}
            }
        ]
        
        for test in queries:
            print(f"\n📤 {test['name']}...")
            result = self.connector.run_query(test["query"], test["params"])
            
            print(f"📥 Result: {len(result)} records")
            
            if result:
                print(f"   📊 Sample: {json.dumps(result[0], indent=2, default=str)}")
            
            print("✅ PASS" if result is not None else "❌ FAIL")
    
    def cleanup_test_data(self):
        """Clean up test data created during tests"""
        print("\n" + "=" * 60)
        print("🧹 CLEANUP: Removing test data")
        print("=" * 60)
        
        # Delete nodes marked as test data
        delete_query = """
        MATCH (n)
        WHERE n.test_data = true OR n.test = true
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        result = self.connector.run_query(delete_query)
        
        if result:
            deleted = result[0].get("deleted_count", 0)
            print(f"🗑️  Deleted {deleted} test nodes")
        
        # Also delete any test relationships we might have created
        # (They should be deleted when nodes are deleted due to DETACH DELETE)
        
        print("✅ Cleanup completed")
    
    def run_all_tests(self):
        """Run all tests"""
        if not self.setup():
            return
        
        try:
            self.test_search_context()
            self.test_get_relationships()
            self.test_save_context()
            self.test_create_node_and_relationship()
            self.test_run_query()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS COMPLETED")
            print("=" * 60)
            
            # Optional: cleanup
            response = input("\n🧹 Clean up test data? (y/N): ")
            if response.lower() == 'y':
                self.cleanup_test_data()
            else:
                print("📝 Test data preserved")
                
        except Exception as e:
            print(f"\n💥 Error during tests: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.connector.close()
            print("\n🔌 Neo4j connection closed")

def main():
    """Main entry point"""
    tester = GraphRAGTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()