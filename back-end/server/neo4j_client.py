"""
Neo4j Client - Helper functions for Neo4j operations
=====================================================
Provides secure and efficient operations for Neo4j graph database.
"""

import os
import re
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class Neo4jConnector:
    def __init__(self):
        """Initialize Neo4j connection parameters from environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "")
        self.driver = None
    
    def connect(self) -> bool:
        """Establish connection to Neo4j and verify connectivity."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                connection_timeout=10
            )
            # Test connection with a simple query
            self.driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j connection error: {e}")
            self.driver = None
            return False
    
    def close(self):
        """Close Neo4j connection gracefully."""
        if self.driver:
            self.driver.close()
            logger.info("🔌 Neo4j connection closed")
    
    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Run any Cypher query and return results.
        """
        if not self.driver:
            raise Exception("Neo4j driver not connected")
        
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"❌ Query execution error: {e}")
                raise
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[Dict]:
        """
        Create a new node with given label and properties.
        """
        if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', label):
            raise ValueError(f"Invalid label format: {label}")
        
        query = f"""
        CREATE (n:{label} $props)
        RETURN n, elementId(n) as elementId, labels(n) as labels
        """
        
        try:
            results = self.run_query(query, {"props": properties or {}})
            
            if results:
                node_labels = results[0]["labels"]
                primary_label = node_labels[0] if node_labels else label
                
                return {
                    "elementId": results[0]["elementId"],
                    "properties": dict(results[0]["n"]),
                    "label": primary_label,
                    "labels": node_labels
                }
            return None
        except Exception as e:
            logger.error(f"❌ Node creation error: {e}")
            return None
    
    def create_relationship(
        self, 
        from_element_id: str, 
        to_element_id: str, 
        rel_type: str, 
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create a relationship between two nodes.
        """
        if not re.match(r'^[A-Z][A-Z0-9_]*$', rel_type):
            raise ValueError(f"Invalid relationship type: {rel_type}")
        
        query = f"""
        MATCH (a), (b)
        WHERE elementId(a) = $from_id AND elementId(b) = $to_id
        CREATE (a)-[r:`{rel_type}` $props]->(b)
        RETURN type(r) as created_type
        """
        
        try:
            results = self.run_query(query, {
                "from_id": from_element_id,
                "to_id": to_element_id,
                "props": properties or {}
            })
            return len(results) > 0
        except Exception as e:
            logger.error(f"❌ Relationship creation error: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # MCP SPECIFIC METHODS - VERSION SIMPLIFIÉE SANS TYPE CHECKING
    # -------------------------------------------------------------------------
    
    def search_context(self, query: str, limit: int = 5) -> Dict:
        """
        Recherche ultra-simple qui fonctionne avec TOUTES les versions de Neo4j.
        Utilise le filtrage Python plutôt que Cypher pour éviter les problèmes de type.
        """
        if not query or not isinstance(query, str):
            return {
                "query": query,
                "error": "Query must be a non-empty string",
                "status": "error"
            }
        
        # OPTION 1: Requête Cypher simple sans type checking
        simple_query = """
        MATCH (n)
        RETURN n, elementId(n) as elementId, labels(n) as labels
        LIMIT $max_nodes
        """
        
        try:
            # Récupère un nombre raisonnable de nœuds
            max_nodes = 200  # Augmente si nécessaire
            all_nodes = self.run_query(simple_query, {"max_nodes": max_nodes})
            
            query_lower = query.lower()
            filtered_results = []
            
            for record in all_nodes:
                node = record["n"]
                node_props = dict(node)
                
                # Filtrage en Python - évite complètement les problèmes de type Cypher
                found = self._check_node_contains_query(node_props, query_lower)
                
                if found:
                    filtered_results.append({
                        "elementId": record["elementId"],
                        "labels": record["labels"],
                        "properties": node_props
                    })
                
                if len(filtered_results) >= limit:
                    break
            
            return {
                "query": query,
                "count": len(filtered_results),
                "results": filtered_results,
                "search_method": "python_filter",
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return {
                "query": query,
                "error": f"Search failed: {e}",
                "status": "error"
            }
    
    def _check_node_contains_query(self, properties: Dict, query_lower: str) -> bool:
        """
        Vérifie si un nœud contient la query dans n'importe quelle propriété.
        Gère tous les types de données en Python.
        """
        for key, value in properties.items():
            if value is None:
                continue
            
            try:
                # Gère les strings
                if isinstance(value, str):
                    if query_lower in value.lower():
                        return True
                
                # Gère les nombres
                elif isinstance(value, (int, float)):
                    if query_lower in str(value).lower():
                        return True
                
                # Gère les booléens
                elif isinstance(value, bool):
                    if query_lower in str(value).lower():
                        return True
                
                # Gère les listes
                elif isinstance(value, list):
                    for item in value:
                        if item and query_lower in str(item).lower():
                            return True
                
                # Gère les dictionnaires (imbriqués)
                elif isinstance(value, dict):
                    # Vérifie récursivement les dictionnaires imbriqués
                    if self._check_node_contains_query(value, query_lower):
                        return True
                
                # Gère tout autre type
                else:
                    try:
                        if query_lower in str(value).lower():
                            return True
                    except:
                        pass
                        
            except Exception:
                continue
        
        return False
    
    def get_relationships(self, element_id: str) -> Dict:
        """
        Get all relationships for a specific node.
        """
        if not element_id or not isinstance(element_id, str):
            return {
                "error": "Element ID must be a non-empty string",
                "status": "error"
            }
        
        query = """
        MATCH (n)-[r]-(connected)
        WHERE elementId(n) = $element_id
        RETURN 
            type(r) as relation_type,
            elementId(startNode(r)) as start_id,
            elementId(endNode(r)) as end_id,
            labels(startNode(r)) as start_labels,
            labels(endNode(r)) as end_labels,
            r as relationship,
            properties(r) as rel_properties
        ORDER BY relation_type
        LIMIT 50
        """
        
        try:
            results = self.run_query(query, {"element_id": element_id})
            
            relationships = []
            for record in results:
                if record["start_id"] == element_id:
                    direction = "outgoing"
                    target_id = record["end_id"]
                    target_labels = record["end_labels"]
                else:
                    direction = "incoming"
                    target_id = record["start_id"]
                    target_labels = record["start_labels"]
                
                relationships.append({
                    "type": record["relation_type"],
                    "direction": direction,
                    "target_elementId": target_id,
                    "target_labels": target_labels,
                    "properties": record["rel_properties"]
                })
            
            return {
                "node_elementId": element_id,
                "count": len(relationships),
                "relationships": relationships,
                "status": "success"
            }
        except Exception as e:
            return {
                "node_elementId": element_id,
                "error": str(e),
                "status": "error"
            }
    
    def save_context(self, data: Dict) -> Dict:
        """
        Save new context to graph.
        """
        try:
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
            
            node_type = data.get("type")
            if not node_type:
                raise ValueError("Node type is required")
            
            properties = data.get("properties", {})
            if not isinstance(properties, dict):
                raise ValueError("Properties must be a dictionary")
            
            node_result = self.create_node(
                label=node_type,
                properties=properties
            )
            
            if not node_result:
                return {
                    "status": "error", 
                    "message": "Failed to create node"
                }
            
            created_relations = []
            failed_relations = []
            
            for rel in data.get("relations", []):
                if not isinstance(rel, dict):
                    failed_relations.append({
                        "error": "Relationship must be a dictionary",
                        "data": rel
                    })
                    continue
                
                target_id = rel.get("target_id")
                rel_type = rel.get("type")
                
                if not target_id or not rel_type:
                    failed_relations.append({
                        "error": "Missing target_id or type",
                        "data": rel
                    })
                    continue
                
                success = self.create_relationship(
                    from_element_id=node_result["elementId"],
                    to_element_id=target_id,
                    rel_type=rel_type,
                    properties=rel.get("properties", {})
                )
                
                if success:
                    created_relations.append({
                        "target": target_id,
                        "type": rel_type,
                        "status": "success"
                    })
                else:
                    failed_relations.append({
                        "target": target_id,
                        "type": rel_type,
                        "error": "Relationship creation failed"
                    })
            
            return {
                "status": "success",
                "message": f"Node '{node_type}' created successfully",
                "node": node_result,
                "created_relations": created_relations,
                "failed_relations": failed_relations if failed_relations else None
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "data_received": data
            }