#!/usr/bin/env python3
"""
Chat Server - HTTP endpoint for LLM conversation
Provides a simple REST API to chat with Perplexity AI
"""
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from llm_host import PerplexityTool
from neo4j_client import Neo4jConnector
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize LLM
try:
    llm_client = PerplexityTool()
    llm_available = True
except Exception as e:
    print(f"⚠️  LLM initialization failed: {e}")
    llm_client = None
    llm_available = False

# Initialize Neo4j (optional, for context)
neo4j_conn = None
try:
    neo4j_conn = Neo4jConnector()
    if neo4j_conn.connect():
        neo4j_available = True
    else:
        neo4j_available = False
except:
    neo4j_available = False

# HTML interface template
CHAT_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neurograph - LLM Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 800px;
            height: 90vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 20px 20px 0 0;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { justify-content: flex-end; }
        .message.assistant { justify-content: flex-start; }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        #messageInput:focus {
            border-color: #667eea;
        }
        #sendButton {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        #sendButton:hover {
            transform: scale(1.05);
        }
        #sendButton:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            padding: 8px 16px;
            text-align: center;
            font-size: 12px;
            color: #666;
            background: #f0f0f0;
        }
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            max-width: 70px;
        }
        .typing-indicator.active {
            display: block;
        }
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
            30% { transform: translateY(-10px); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Neurograph Chat</h1>
            <p>Powered by Perplexity AI</p>
        </div>
        <div class="status" id="status">
            {% if llm_available %}
            ✅ LLM Connected | {% endif %}
            {% if neo4j_available %}
            ✅ Neo4j Connected
            {% else %}
            ⚠️ Neo4j Disconnected
            {% endif %}
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-content">
                    👋 Hello! I'm your AI assistant powered by Perplexity. How can I help you today?
                </div>
            </div>
            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
        <div class="input-area">
            <input 
                type="text" 
                id="messageInput" 
                placeholder="Type your message here..." 
                autocomplete="off"
                onkeypress="if(event.key === 'Enter') sendMessage()"
            >
            <button id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');

        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            messageDiv.innerHTML = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>`;
            chatArea.insertBefore(messageDiv, typingIndicator);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function showTyping() {
            typingIndicator.classList.add('active');
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function hideTyping() {
            typingIndicator.classList.remove('active');
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            showTyping();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                const data = await response.json();
                hideTyping();

                if (data.success) {
                    addMessage(data.response, false);
                } else {
                    addMessage(`❌ Error: ${data.error}`, false);
                }
            } catch (error) {
                hideTyping();
                addMessage(`❌ Network error: ${error.message}`, false);
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the chat interface"""
    return render_template_string(
        CHAT_INTERFACE,
        llm_available=llm_available,
        neo4j_available=neo4j_available
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint - POST /api/chat
    Body: { "message": "your message here" }
    Returns: { "success": true, "response": "AI response" }
    """
    if not llm_available:
        return jsonify({
            "success": False,
            "error": "LLM not available. Check PERPLEXITY_API_KEY in .env"
        }), 503

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'message' in request body"
            }), 400

        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                "success": False,
                "error": "Message cannot be empty"
            }), 400

        # Optional: Enrich with Neo4j context if available
        context = ""
        if neo4j_available and neo4j_conn:
            # Search for relevant context
            search_result = neo4j_conn.search_context(user_message, limit=3)
            if search_result.get('count', 0) > 0:
                context = f"\n\nRelevant context from knowledge graph:\n{search_result}"

        # Build prompt
        prompt = f"{user_message}{context}"

        # Get LLM response
        response = llm_client.ask(prompt)

        return jsonify({
            "success": True,
            "response": response,
            "model": "perplexity-sonar"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "llm_available": llm_available,
        "neo4j_available": neo4j_available
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    
    # Get network info
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 60)
    print("🌐 Neurograph Chat Server")
    print("=" * 60)
    print(f"✅ LLM: {'Available' if llm_available else 'Not available'}")
    print(f"✅ Neo4j: {'Connected' if neo4j_available else 'Disconnected'}")
    print(f"\n🚀 Server starting...")
    print(f"📱 Local access: http://localhost:{port}")
    print(f"📡 Network access: http://{local_ip}:{port}")
    print(f"🔌 API endpoint: http://{local_ip}:{port}/api/chat")
    print(f"\n💡 For public access, use: python start_chat_public.py")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production
