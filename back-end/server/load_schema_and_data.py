#!/usr/bin/env python3
"""
Script pour charger le schéma et les données de démo dans Neo4j
"""
import sys
from pathlib import Path

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from neo4j_client import Neo4jConnector

def load_cypher_file(connector: Neo4jConnector, file_path: Path):
    """Charge et exécute un fichier Cypher en séparant correctement les requêtes"""
    print(f"📄 Chargement de {file_path.name}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Nettoyer les commentaires de ligne (simple approche)
        lines = []
        for line in content.split('\n'):
            # Enlever les commentaires de ligne
            if '//' in line:
                comment_pos = line.find('//')
                # Vérifier que ce n'est pas dans une string
                before_comment = line[:comment_pos]
                single_quotes = before_comment.count("'") - before_comment.count("\\'")
                double_quotes = before_comment.count('"') - before_comment.count('\\"')
                # Si nombre pair de quotes, c'est un vrai commentaire
                if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                    line = before_comment.rstrip()
            if line.strip():
                lines.append(line)
        
        # Reconstruire le contenu sans commentaires
        cleaned_content = '\n'.join(lines)
        
        # Séparer par point-virgule (méthode simple mais efficace)
        # On divise par ';' mais on garde la structure
        parts = cleaned_content.split(';')
        queries = []
        
        for part in parts:
            part = part.strip()
            if part and len(part) > 5:  # Ignorer les parties trop courtes
                # Nettoyer les espaces multiples
                query = ' '.join(part.split())
                queries.append(query)
        
        executed = 0
        errors = 0
        for i, query in enumerate(queries, 1):
            if query:
                try:
                    # Exécuter la requête
                    connector.run_query(query)
                    executed += 1
                except Exception as e:
                    error_msg = str(e).lower()
                    # Ignorer certaines erreurs attendues
                    if any(ignored in error_msg for ignored in ["already exists", "constraint", "index"]):
                        executed += 1  # Compter comme exécuté
                    else:
                        errors += 1
                        if errors <= 10:  # Afficher les 10 premières erreurs
                            print(f"   ⚠️  Erreur requête {i}: {str(e)[:150]}")
                            # Afficher un extrait de la requête problématique
                            if len(query) < 200:
                                print(f"      Requête: {query[:100]}...")
        
        print(f"   ✅ {executed} requêtes exécutées" + (f", {errors} erreurs" if errors > 0 else ""))
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Charge le schéma et les données"""
    print("=" * 60)
    print("🚀 Chargement du schéma et des données Neo4j")
    print("=" * 60)
    
    # Connexion
    connector = Neo4jConnector()
    if not connector.connect():
        print("❌ Impossible de se connecter à Neo4j")
        return False
    
    print("✅ Connecté à Neo4j\n")
    
    # Chemins des fichiers
    base_dir = Path(__file__).parent.parent / "graph_model"
    schema_file = base_dir / "schema.cypher"
    seed_file = base_dir / "seed_data.cypher"
    
    # Charger le schéma
    if schema_file.exists():
        if not load_cypher_file(connector, schema_file):
            connector.close()
            return False
    else:
        print(f"❌ Fichier non trouvé: {schema_file}")
        connector.close()
        return False
    
    print()
    
    # Charger les données
    if seed_file.exists():
        if not load_cypher_file(connector, seed_file):
            connector.close()
            return False
    else:
        print(f"❌ Fichier non trouvé: {seed_file}")
        connector.close()
        return False
    
    # Vérification
    print("\n" + "=" * 60)
    print("🔍 Vérification des données chargées...")
    
    try:
        # Compter les incidents
        result = connector.run_query("MATCH (i:Incident) RETURN count(i) as count")
        incident_count = result[0]['count'] if result else 0
        print(f"   📊 Incidents: {incident_count}")
        
        # Compter les utilisateurs
        result = connector.run_query("MATCH (u:User) RETURN count(u) as count")
        user_count = result[0]['count'] if result else 0
        print(f"   👥 Utilisateurs: {user_count}")
        
        # Compter les services
        result = connector.run_query("MATCH (s:BusinessService) RETURN count(s) as count")
        service_count = result[0]['count'] if result else 0
        print(f"   🏢 Services: {service_count}")
        
        print("\n✅ Chargement terminé avec succès!")
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification: {e}")
    
    connector.close()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

