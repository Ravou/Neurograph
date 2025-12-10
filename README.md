# Neurograph - AI-Powered Incident Management with GraphRAG

> **Hackathon Project**: Intelligent incident management system combining Neo4j knowledge graphs, Perplexity AI, and Model Context Protocol (MCP) for Cursor IDE integration.

## 🚀 Overview

Neurograph is an intelligent incident management platform that leverages:
- **Neo4j Graph Database** for structured knowledge representation
- **Perplexity AI** for intelligent incident analysis and proposal
- **Model Context Protocol (MCP)** for seamless Cursor IDE integration
- **GraphRAG** approach for context-aware incident resolution

## ✨ Features

### 🔍 Graph Search & Exploration
- Search incidents, services, and resources in Neo4j
- Explore relationships between incidents, users, and cloud resources
- Full-text search across incident descriptions

### 🤖 AI-Powered Incident Proposal
- Natural language incident description processing
- Context-aware incident structuring using Perplexity AI
- Automatic relationship mapping to existing graph entities
- Graph visualization generation

### 🔗 MCP Integration
- Direct integration with Cursor IDE
- Natural language queries via chat interface
- Real-time graph operations through MCP tools

## 📋 Prerequisites

- Python 3.10+
- Neo4j Database (local or cloud instance)
- Perplexity API Key
- Cursor IDE (for MCP integration)
- ngrok (optional, for public access) - `brew install ngrok/ngrok/ngrok`

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Neurograph
```

### 2. Set Up Python Environment

```bash
cd back-end/server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../../requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in `back-end/server/`:

```env
# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Perplexity AI Configuration
PERPLEXITY_API_KEY=pplx-your-api-key-here
```

### 4. Initialize Neo4j Database

```bash
cd back-end/server
python load_schema_and_data.py
```

This will:
- Create schema constraints and indexes
- Load demo data (1004 incidents, services, users, resources)
- Set up relationships

### 5. Configure Cursor IDE

Copy `mcp.json` to `~/.cursor/mcp.json`:

```bash
cp mcp.json ~/.cursor/mcp.json
```

The configuration includes:
- MCP server path
- Environment variables
- Python virtual environment

**Restart Cursor IDE** to activate the MCP server.

## 🎯 Usage

### In Cursor IDE

Once configured, you can use natural language queries:

```
"Search for RSE incidents"
"Show relationships for incident INC-1001"
"Propose an incident: The Auth service is experiencing critical downtime"
```

### Available MCP Tools

1. **`search_graph_context`** - Search the Neo4j graph
   - Parameters: `query` (string), `limit` (integer, default: 5)

2. **`get_node_relationships`** - Get all relationships for a node
   - Parameters: `node_id` (string, elementId)

3. **`save_graph_context`** - Save new node to graph
   - Parameters: `type` (string), `properties` (object), `relations` (array)

4. **`propose_incident_with_llm`** - AI-powered incident proposal
   - Parameters: `user_text` (string), `search_context` (string, optional), `context_limit` (integer, default: 5)

### Chat Interface

Interactive web chat interface with the LLM:

**Local Access:**
```bash
cd back-end/server
python chat_server.py
```
Access at `http://localhost:5001`

**Public Access (Recommended - using ngrok):**
```bash
cd back-end/server
python start_chat_public.py
```

This will:
- Start the chat server
- Create a public ngrok tunnel
- Display your public URL (e.g., `https://abc123.ngrok.io`)

**Direct Public Access (requires firewall/port forwarding):**
```bash
cd back-end/server
python start_chat_public.py --method direct
```

**API Endpoint**: `POST /api/chat`
```json
{
  "message": "Your question here"
}
```

**Response**:
```json
{
  "success": true,
  "response": "AI response here",
  "model": "perplexity-sonar"
}
```

## 🏗️ Architecture

```
┌─────────────┐
│  Cursor IDE │
└──────┬──────┘
       │ MCP Protocol
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ MCP Server  │────▶│  Neo4j Graph │     │ Perplexity  │
│ (mcp_server)│     │   Database   │     │     AI      │
└─────────────┘     └──────────────┘     └─────────────┘
       │
       ├─── neo4j_client.py (Graph operations)
       ├─── llm_host.py (AI integration)
       └─── load_schema_and_data.py (Data initialization)
```

## 📊 Data Model

### Core Entities
- **Incident**: Incidents with status, priority, description
- **BusinessService**: Business services (RSE-Platform, HR-Portal, etc.)
- **CloudResource**: Cloud resources (VMs, databases, load balancers)
- **User**: Team members (SRE, Developers, Product Owners)
- **Category/SubCategory**: Incident classification
- **Urgency/Impact**: Priority levels

### Relationships
- `RELATES_TO_SERVICE` - Incident → BusinessService
- `AFFECTS` - Incident → CloudResource
- `ASSIGNED_TO` - User → Incident
- `BLOCKED_BY` - Incident → Incident
- `HAS_URGENCY`, `HAS_IMPACT` - Incident → Priority levels

## 🔧 Development

### Project Structure

```
Neurograph/
├── back-end/
│   ├── graph_model/
│   │   ├── schema.cypher      # Neo4j schema definition
│   │   └── seed_data.cypher    # Demo data
│   └── server/
│       ├── mcp_server.py      # MCP server implementation
│       ├── neo4j_client.py    # Neo4j operations
│       ├── llm_host.py         # Perplexity AI integration
│       ├── chat_server.py      # Web chat interface
│       └── load_schema_and_data.py  # Data loader
├── mcp.json                    # Cursor MCP configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Running Tests

```bash
cd back-end/server
python run_all_tests.py
```

## 🎨 Hackathon Highlights

- **Innovation**: First-class MCP integration for AI-assisted development
- **Intelligence**: LLM-powered incident analysis with graph context
- **Efficiency**: Natural language interface for complex graph operations
- **Scalability**: Neo4j handles 1000+ incidents with optimized queries

## 📝 API Examples

### Search Incidents

```python
# Via MCP in Cursor
search_graph_context(query="RSE", limit=10)
```

### Propose Incident with AI

```python
# Via MCP in Cursor
propose_incident_with_llm(
    user_text="Service Auth is down, users cannot login",
    search_context="Auth",
    context_limit=5
)
```

## 🤝 Contributing

This is a hackathon project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - Hackathon Project

## 🙏 Acknowledgments

- Neo4j for graph database technology
- Perplexity AI for LLM capabilities
- Cursor IDE for MCP protocol support

---

**Built for Hackathon** 🚀 | **Powered by AI & Graphs** 🧠📊
