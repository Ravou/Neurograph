#!/usr/bin/env python3
"""
Start chat server accessible from public IP
Uses ngrok for easy public access (recommended)
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def check_ngrok():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False

def install_ngrok_instructions():
    """Print instructions to install ngrok"""
    print("""
📦 To expose your server publicly, install ngrok:

macOS:
  brew install ngrok/ngrok/ngrok

Or download from: https://ngrok.com/download

Then authenticate:
  ngrok config add-authtoken YOUR_TOKEN
  (Get token from https://dashboard.ngrok.com/get-started/your-authtoken)
""")

def start_with_ngrok(port=5001):
    """Start chat server with ngrok tunnel"""
    if not check_ngrok():
        print("❌ ngrok not found")
        install_ngrok_instructions()
        return False
    
    print("=" * 60)
    print("🚀 Starting Chat Server with Public Access")
    print("=" * 60)
    
    # Start the chat server in background
    server_script = Path(__file__).parent / "chat_server.py"
    server_process = subprocess.Popen(
        [sys.executable, str(server_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print(f"✅ Chat server starting on port {port}...")
    time.sleep(2)
    
    # Start ngrok tunnel
    print("🌐 Starting ngrok tunnel...")
    ngrok_process = subprocess.Popen(
        ['ngrok', 'http', str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    
    # Get ngrok URL
    try:
        import requests
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            if tunnels:
                public_url = tunnels[0].get('public_url')
                print("\n" + "=" * 60)
                print("✅ SERVER IS NOW PUBLICLY ACCESSIBLE!")
                print("=" * 60)
                print(f"🌍 Public URL: {public_url}")
                print(f"💬 Chat Interface: {public_url}/")
                print(f"🔌 API Endpoint: {public_url}/api/chat")
                print("=" * 60)
                print("\n⚠️  Press Ctrl+C to stop both server and ngrok")
                return True
    except:
        pass
    
    print("\n✅ Server started!")
    print("📋 Check ngrok dashboard at http://localhost:4040 for public URL")
    print("⚠️  Press Ctrl+C to stop")
    
    try:
        server_process.wait()
        ngrok_process.terminate()
    except KeyboardInterrupt:
        print("\n👋 Stopping server...")
        server_process.terminate()
        ngrok_process.terminate()
    
    return True

def start_direct(port=5001):
    """Start server directly (requires firewall/port forwarding)"""
    print("=" * 60)
    print("🚀 Starting Chat Server (Direct Access)")
    print("=" * 60)
    
    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    try:
        # Try to get public IP
        import requests
        public_ip = requests.get('https://api.ipify.org', timeout=2).text
    except:
        public_ip = "YOUR_PUBLIC_IP"
    
    print(f"📡 Local IP: {local_ip}")
    print(f"🌍 Public IP: {public_ip}")
    print(f"\n⚠️  IMPORTANT:")
    print(f"   1. Make sure port {port} is open in your firewall")
    print(f"   2. Configure port forwarding on your router if needed")
    print(f"   3. Access via: http://{public_ip}:{port}")
    print("=" * 60)
    
    # Start server
    server_script = Path(__file__).parent / "chat_server.py"
    os.environ['PORT'] = str(port)
    os.execv(sys.executable, [sys.executable, str(server_script)])

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Start chat server with public access')
    parser.add_argument('--method', choices=['ngrok', 'direct'], default='ngrok',
                       help='Method to expose server (default: ngrok)')
    parser.add_argument('--port', type=int, default=5001,
                       help='Port to use (default: 5001)')
    
    args = parser.parse_args()
    
    if args.method == 'ngrok':
        start_with_ngrok(args.port)
    else:
        start_direct(args.port)
