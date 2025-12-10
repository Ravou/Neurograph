// Enhanced front-end logic (search -> MCP -> Neo4j results + archives)

// Smooth scroll functionality (robust)
const scrollBtn = document.querySelector('.scroll-btn');
if (scrollBtn) {
    scrollBtn.addEventListener('click', function() {
        const products = document.querySelector('.products');
        if (products) products.scrollIntoView({ behavior: 'smooth' });
    });
}

// Search input functionality - MCP Neo4j integration
const searchInput = document.getElementById('searchInput');
const searchBtn = document.querySelector('.search-btn');

if (searchBtn) {
    searchBtn.addEventListener('click', function() {
        const query = searchInput ? searchInput.value : '';
        if (query.trim()) {
            console.log('Searching for:', query);
            queryNeo4jViaLLM(query);
        }
    });
}

// Handle Enter key in search
if (searchInput) {
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            if (searchBtn) searchBtn.click();
        }
    });
}

// Query Neo4j through LLM via MCP
async function queryNeo4jViaLLM(userQuery) {
    try {
        // Call your MCP server endpoint (adjust path as needed)
        const response = await fetch('/api/mcp/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: userQuery,
                type: 'neo4j'
            })
        });

        if (!response.ok) throw new Error('MCP request failed');
        
        const result = await response.json();
        
        // Display the report and graph
        displayNeo4jResults(result);
    } catch (error) {
        console.error('Error querying Neo4j:', error);
        alert('Error: Unable to process your query. Please try again.');
    }
}

// Save result to archives (localStorage + optional server POST)
function saveResultToArchives(result) {
    try {
        const key = 'neurograph_archives_v1';
        const existing = JSON.parse(localStorage.getItem(key) || '[]');
        const entry = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            query: result.query || null,
            report: result.report || null,
            graphData: result.graphData || null
        };
        existing.unshift(entry);
        localStorage.setItem(key, JSON.stringify(existing));

        // Try to also send to server archive endpoint (best-effort)
        fetch('/api/archives', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(entry)
        }).catch(err => console.warn('Archive POST failed (optional):', err));

        alert('Saved to Archives');
    } catch (err) {
        console.error('Error saving to archives:', err);
        alert('Unable to save to archives locally.');
    }
}

// Display Neo4j query results with report and graph
function displayNeo4jResults(result) {
    // Ensure result includes the original query for saving
    if (!result.query && searchInput) result.query = searchInput.value;

    // Create results section
    const resultsSection = document.createElement('section');
    resultsSection.className = 'results-section';
    resultsSection.id = 'resultsSection';
    
    // Display report
    const report = document.createElement('div');
    report.className = 'neo4j-report';
    report.innerHTML = `
        <h2>Query Results</h2>
        <div class="report-content">${result.report || 'No results found'}</div>
        <div style="margin-top:16px; display:flex; gap:12px;">
            <button id="saveToArchivesBtn" class="btn-primary">Save to ARCHIVES</button>
            <button id="downloadJsonBtn" class="btn-outline">Download JSON</button>
        </div>
    `;
    
    // Display graph
    const graphContainer = document.createElement('div');
    graphContainer.className = 'neo4j-graph';
    graphContainer.id = 'neo4jGraph';
    graphContainer.innerHTML = '<h3>Neo4j Graph Visualization</h3><div id="graph-canvas"></div>';
    
    resultsSection.appendChild(report);
    resultsSection.appendChild(graphContainer);
    
    // Remove previous results if any
    const existingResults = document.getElementById('resultsSection');
    if (existingResults) existingResults.remove();
    
    // Insert results after hero section
    const heroSection = document.querySelector('.hero');
    if (heroSection && heroSection.parentNode) heroSection.parentNode.insertBefore(resultsSection, heroSection.nextSibling);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // Wire Save and Download buttons
    const saveBtn = document.getElementById('saveToArchivesBtn');
    if (saveBtn) saveBtn.addEventListener('click', function() { saveResultToArchives(result); });

    const dlBtn = document.getElementById('downloadJsonBtn');
    if (dlBtn) dlBtn.addEventListener('click', function() {
        const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(result, null, 2));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute('href', dataStr);
        dlAnchor.setAttribute('download', `neurograph-result-${Date.now()}.json`);
        document.body.appendChild(dlAnchor);
        dlAnchor.click();
        dlAnchor.remove();
    });

    // Render graph if data is provided
    if (result.graphData) renderNeo4jGraph(result.graphData);
}

// Render Neo4j graph (placeholder — integrate vis.js / D3 / cytoscape for richer viz)
function renderNeo4jGraph(graphData) {
    const canvas = document.getElementById('graph-canvas');
    if (!canvas) return;
    canvas.innerHTML = '<pre style="white-space:pre-wrap;color:#ccc;padding:12px;">' + JSON.stringify(graphData, null, 2) + '</pre>';
}

// Existing product-card behaviours (if present)
const productCards = document.querySelectorAll('.product-card');
productCards.forEach(card => {
    card.addEventListener('mouseenter', function() { this.style.transform = 'translateY(-8px)'; });
    card.addEventListener('mouseleave', function() { this.style.transform = 'translateY(0)'; });
});

// Parallax effect for gradient background
let scrollPosition = 0;
window.addEventListener('scroll', function() {
    scrollPosition = window.pageYOffset;
    const gradient = document.querySelector('.gradient-bg');
    if (gradient) gradient.style.transform = `translateY(${scrollPosition * 0.5}px)`;
});

// Intersection Observer for product cards animation
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -100px 0px' };
const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

productCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(card);
});

// Console welcome message
console.log('%cGrok AI', 'font-size: 48px; font-weight: bold; background: linear-gradient(90deg, #fbbf24, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent;');
console.log('Welcome to Grok - AI for all humanity');