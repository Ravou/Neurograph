////////////////////////////////////////////////////////////////////////
// seed_data.cypher – Données de démo pour un système d’incidents cloud
////////////////////////////////////////////////////////////////////////

//////////////////////////////
// 1. Dimensions de base    //
//////////////////////////////

// Urgency
UNWIND [
  {level:1, name:'Critical', description:'Service completely unavailable'},
  {level:2, name:'High',     description:'Major degradation, many users impacted'},
  {level:3, name:'Medium',   description:'Partial degradation'},
  {level:4, name:'Low',      description:'Limited impact / workaround possible'}
] AS u
MERGE (urg:Urgency {level:u.level})
ON CREATE SET urg.name = u.name, urg.description = u.description;

// Impact
UNWIND [
  {level:1, name:'High',   description:'External customers blocked'},
  {level:2, name:'Medium', description:'External customers degraded'},
  {level:3, name:'Low',    description:'Internal impact only'},
  {level:4, name:'Minor',  description:'Little or no impact'}
] AS i
MERGE (imp:Impact {level:i.level})
ON CREATE SET imp.name = i.name, imp.description = i.description;

// Categories
UNWIND [
  {id:10, name:'Compute',      description:'VM, instances Scalingo, nodes GKE'},
  {id:20, name:'Database',     description:'PostgreSQL, Cloud SQL, Redis'},
  {id:30, name:'Networking',   description:'Load balancers, VPC, DNS'},
  {id:40, name:'Deployment',   description:'CI/CD, failed deployments'}
] AS c
MERGE (cat:Category {id:c.id})
ON CREATE SET cat.name = c.name, cat.description = c.description;

// SubCategories
UNWIND [
  {id:101, name:'Instance crash',         category:10},
  {id:102, name:'Autoscaling misconfig',  category:10},
  {id:201, name:'Primary DB unavailable', category:20},
  {id:202, name:'Slow queries',           category:20},
  {id:301, name:'Load balancer down',     category:30},
  {id:302, name:'Ingress misconfig',      category:30},
  {id:401, name:'Failed deployment',      category:40},
  {id:402, name:'Rollback required',      category:40}
] AS sc
MERGE (sub:SubCategory {id:sc.id})
ON CREATE SET sub.name = sc.name
WITH sc, sub
MATCH (c:Category {id:sc.category})
MERGE (sub)-[:BELONGS_TO_CATEGORY]->(c);

// Business services (RSE / SaaS internes)
UNWIND [
  {id:1, name:'RSE-Platform',   description:'Internal RSE platform (social, news, communities)'},
  {id:2, name:'HR-Portal',      description:'HR portal (leave, training)'},
  {id:3, name:'Customer-App',   description:'External B2B customer application'},
  {id:4, name:'Data-Warehouse', description:'Analytical warehouse on GCP'}
] AS s
MERGE (svc:BusinessService {id:s.id})
ON CREATE SET svc.name = s.name, svc.description = s.description;

// Users (équipes / rôles)
UNWIND [
  {id:'u1', name:'Alice',   role:'SRE',              email:'alice@sre.example.com'},
  {id:'u2', name:'Bob',     role:'Backend Dev',      email:'bob@dev.example.com'},
  {id:'u3', name:'Chloe',   role:'Product Owner',    email:'chloe@product.example.com'},
  {id:'u4', name:'David',   role:'Incident Manager', email:'david@ops.example.com'}
] AS u
MERGE (usr:User {id:u.id})
ON CREATE SET usr.name = u.name, usr.role = u.role, usr.email = u.email;

// Cloud resources (Google Cloud / Scalingo)
UNWIND [
  {id:'r1', type:'App',      provider:'Scalingo', service_id:1, name:'rse-app-prod'},
  {id:'r2', type:'Database', provider:'Scalingo', service_id:1, name:'rse-db-prod'},
  {id:'r3', type:'VM',       provider:'GCP',      service_id:3, name:'customer-api-prod-vm-1'},
  {id:'r4', type:'LB',       provider:'GCP',      service_id:3, name:'customer-api-lb'},
  {id:'r5', type:'DB',       provider:'GCP',      service_id:4, name:'bigquery-dwh'}
] AS r
MERGE (res:CloudResource {id:r.id})
ON CREATE SET res.type = r.type, res.provider = r.provider, res.name = r.name
WITH r, res
MATCH (svc:BusinessService {id:r.service_id})
MERGE (res)-[:BELONGS_TO_SERVICE]->(svc);


//////////////////////////////
// 2. Incidents de démo     //
//////////////////////////////

// Incident 1 – Panne critique RSE (Scalingo app down)
MERGE (i1:Incident {id:'INC-1001'})
ON CREATE SET
  i1.title       = 'RSE inaccessible - erreur 502 sur Scalingo',
  i1.description = 'Internal users cannot access the RSE platform. HTTP 502 since 08:15. Scalingo reports an incident on the region hosting rse-app-prod.',
  i1.status      = 'open',
  i1.priority    = 'P1',
  i1.created_at  = datetime('2025-12-10T08:15:00'),
  i1.source      = 'monitoring';

MATCH (svc1:BusinessService {id:1})
MATCH (res1:CloudResource {id:'r1'})
MATCH (sc_net:SubCategory {id:301})      // Load balancer down
MATCH (u_crit:Urgency {level:1})
MATCH (imp_high:Impact {level:1})
MATCH (alice:User {id:'u1'})
MATCH (david:User {id:'u4'})

MERGE (i1)-[:RELATES_TO_SERVICE]->(svc1)
MERGE (i1)-[:AFFECTS]->(res1)
MERGE (i1)-[:HAS_SUBCATEGORY1]->(sc_net)
MERGE (i1)-[:HAS_URGENCY]->(u_crit)
MERGE (i1)-[:HAS_IMPACT]->(imp_high)
MERGE (alice)-[:ASSIGNED_TO]->(i1)
MERGE (david)-[:MANAGES]->(i1);

// Incident 2 – Dégradation RSE (DB lente Scalingo)
MERGE (i2:Incident {id:'INC-1002'})
ON CREATE SET
  i2.title       = 'RSE lente - latence élevée sur la base Scalingo',
  i2.description = 'RSE pages take more than 10 seconds to load. Monitoring shows CPU spikes on rse-db-prod. Impact: internal users in Europe.',
  i2.status      = 'open',
  i2.priority    = 'P2',
  i2.created_at  = datetime('2025-12-10T09:00:00'),
  i2.source      = 'user_report';

MATCH (svc_rse:BusinessService {id:1})
MATCH (res_db:CloudResource {id:'r2'})
MATCH (cat_db:Category {id:20})
MATCH (sc_slow:SubCategory {id:202})
MATCH (u_high:Urgency {level:2})
MATCH (imp_med:Impact {level:2})
MATCH (alice:User {id:'u1'})
MATCH (chloe:User {id:'u3'})

MERGE (i2)-[:RELATES_TO_SERVICE]->(svc_rse)
MERGE (i2)-[:AFFECTS]->(res_db)
MERGE (i2)-[:HAS_CATEGORY]->(cat_db)
MERGE (i2)-[:HAS_SUBCATEGORY1]->(sc_slow)
MERGE (i2)-[:HAS_URGENCY]->(u_high)
MERGE (i2)-[:HAS_IMPACT]->(imp_med)
MERGE (chloe)-[:REPORTED]->(i2)
MERGE (alice)-[:ASSIGNED_TO]->(i2)
MERGE (i2)-[:BLOCKED_BY]->(i1);

// Incident 3 – Déploiement raté sur Customer-App (GCP)
MERGE (i3:Incident {id:'INC-1003'})
ON CREATE SET
  i3.title       = 'Erreur 500 après déploiement Customer-App sur GCP',
  i3.description = 'Deployment of version 2.3.0 on customer-api-prod-vm-1 causes HTTP 500 on /login and /orders. Rollback considered.',
  i3.status      = 'open',
  i3.priority    = 'P2',
  i3.created_at  = datetime('2025-12-10T08:45:00'),
  i3.source      = 'ci_cd';

MATCH (svc_cust:BusinessService {id:3})
MATCH (vm:CloudResource {id:'r3'})
MATCH (lb:CloudResource {id:'r4'})
MATCH (cat_dep:Category {id:40})
MATCH (sc_dep:SubCategory {id:401})
MATCH (u_high2:Urgency {level:2})
MATCH (imp_high2:Impact {level:1})
MATCH (bob:User {id:'u2'})
MATCH (david:User {id:'u4'})

MERGE (i3)-[:RELATES_TO_SERVICE]->(svc_cust)
MERGE (i3)-[:AFFECTS]->(vm)
MERGE (i3)-[:AFFECTS]->(lb)
MERGE (i3)-[:HAS_CATEGORY]->(cat_dep)
MERGE (i3)-[:HAS_SUBCATEGORY1]->(sc_dep)
MERGE (i3)-[:HAS_URGENCY]->(u_high2)
MERGE (i3)-[:HAS_IMPACT]->(imp_high2)
MERGE (bob)-[:REPORTED]->(i3)
MERGE (david)-[:MANAGES]->(i3);

// Incident 4 – Problème analytique (BigQuery / DWH)
MERGE (i4:Incident {id:'INC-1004'})
ON CREATE SET
  i4.title       = 'Jobs BigQuery en échec - dashboards indisponibles',
  i4.description = 'Several ETL jobs have been failing since 02:00 on bigquery-dwh. RSE and business dashboards are no longer updated.',
  i4.status      = 'open',
  i4.priority    = 'P3',
  i4.created_at  = datetime('2025-12-10T06:15:00'),
  i4.source      = 'monitoring';

MATCH (svc_dwh:BusinessService {id:4})
MATCH (bq:CloudResource {id:'r5'})
MATCH (cat_db2:Category {id:20})
MATCH (sc_db2:SubCategory {id:201})
MATCH (u_med:Urgency {level:3})
MATCH (imp_low:Impact {level:3})
MATCH (alice:User {id:'u1'})

MERGE (i4)-[:RELATES_TO_SERVICE]->(svc_dwh)
MERGE (i4)-[:AFFECTS]->(bq)
MERGE (i4)-[:HAS_CATEGORY]->(cat_db2)
MERGE (i4)-[:HAS_SUBCATEGORY1]->(sc_db2)
MERGE (i4)-[:HAS_URGENCY]->(u_med)
MERGE (i4)-[:HAS_IMPACT]->(imp_low)
MERGE (alice)-[:ASSIGNED_TO]->(i4);


///////////////////////////////////////////////
// 3. Incidents supplémentaires pour la perf //
///////////////////////////////////////////////

// Générer 1 000 incidents supplémentaires pour tester la rapidité
UNWIND range(1, 1000) AS n
MATCH (svc:BusinessService {id:1})        // RSE-Platform
MATCH (res:CloudResource {id:'r1'})       // rse-app-prod
MATCH (u:Urgency {level: case when n % 4 = 0 then 1 when n % 4 = 1 then 2 when n % 4 = 2 then 3 else 4 end})
MATCH (imp:Impact {level: case when n % 3 = 0 then 1 when n % 3 = 1 then 2 else 3 end})
WITH n, svc, res, u, imp
MERGE (inc:Incident {id: 'INC-BULK-' + toString(n)})
ON CREATE SET
  inc.title       = 'Bulk incident RSE n°' + toString(n),
  inc.description = 'Synthetic incident used for performance testing on RSE platform.',
  inc.status      = 'open',
  inc.priority    = 'P' + toString(1 + (n % 3)),
  inc.created_at  = datetime('2025-12-01T00:00:00') + duration({hours:n}),
  inc.source      = 'seed_perf'
MERGE (inc)-[:RELATES_TO_SERVICE]->(svc)
MERGE (inc)-[:AFFECTS]->(res)
MERGE (inc)-[:HAS_URGENCY]->(u)
MERGE (inc)-[:HAS_IMPACT]->(imp);