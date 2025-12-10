////////////////////////////////////////////////////////////////////////
// schema.cypher – Modèle Neo4j pour un système d’incidents cloud
////////////////////////////////////////////////////////////////////////

///////////////////////
// Nettoyage complet //
///////////////////////

MATCH (n) DETACH DELETE n;


//////////////////////////////
// Contraintes d’unicité   //
//////////////////////////////

// Utilisateurs (agents, clients, etc.)
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

// Incidents
CREATE CONSTRAINT incident_id_unique IF NOT EXISTS
FOR (i:Incident) REQUIRE i.id IS UNIQUE;

// Ressources cloud (VM, DB, cluster, service managé…)
CREATE CONSTRAINT cloudresource_id_unique IF NOT EXISTS
FOR (r:CloudResource) REQUIRE r.id IS UNIQUE;

// Services métiers / applicatifs
CREATE CONSTRAINT businessservice_id_unique IF NOT EXISTS
FOR (s:BusinessService) REQUIRE s.id IS UNIQUE;

// Catégories d’incident
CREATE CONSTRAINT category_id_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.id IS UNIQUE;

// Sous‑catégories
CREATE CONSTRAINT subcategory_id_unique IF NOT EXISTS
FOR (sc:SubCategory) REQUIRE sc.id IS UNIQUE;

// Niveaux d’urgence
CREATE CONSTRAINT urgency_level_unique IF NOT EXISTS
FOR (u:Urgency) REQUIRE u.level IS UNIQUE;

// Niveaux d’impact
CREATE CONSTRAINT impact_level_unique IF NOT EXISTS
FOR (i:Impact) REQUIRE i.level IS UNIQUE;


/////////////////////////
// Index opérationnels //
/////////////////////////

// Incidents – pour filtres fréquents
CREATE INDEX incident_status_index IF NOT EXISTS
FOR (i:Incident) ON (i.status);

CREATE INDEX incident_created_at_index IF NOT EXISTS
FOR (i:Incident) ON (i.created_at);

CREATE INDEX incident_priority_index IF NOT EXISTS
FOR (i:Incident) ON (i.priority);

// Mapping direct depuis le CSV (category_id, service_id, etc.)
CREATE INDEX incident_category_index IF NOT EXISTS
FOR (i:Incident) ON (i.category_id);

CREATE INDEX incident_service_index IF NOT EXISTS
FOR (i:Incident) ON (i.service_id);

// User – pour lookup par email / login
CREATE INDEX user_email_index IF NOT EXISTS
FOR (u:User) ON (u.email);


////////////////////////////////////
// Index texte / recherche fulltext
////////////////////////////////////

// Recherche textuelle sur les incidents (titre + description)
CREATE FULLTEXT INDEX incident_search IF NOT EXISTS
FOR (i:Incident) ON EACH [i.title, i.description];


/////////////////////////////////////
// Rappel des labels et relations  //
/////////////////////////////////////

// Labels principaux créés par les scripts de seed :
//
// (User:User {id, name, email, role, ...})
// (Incident:Incident {
//      id, title, description, status,
//      created_at,
