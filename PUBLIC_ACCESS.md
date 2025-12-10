# 🌍 Exposing Chat Server to Public IP

## Method 1: Using ngrok (Recommended - Easiest)

### Installation

```bash
# macOS
brew install ngrok/ngrok/ngrok

# Or download from: https://ngrok.com/download
```

### Authentication

1. Sign up at https://dashboard.ngrok.com
2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. Authenticate:
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### Start Public Server

```bash
cd back-end/server
python start_chat_public.py
```

This will:
- ✅ Start the chat server on port 5001
- ✅ Create a public ngrok tunnel
- ✅ Display your public URL (e.g., `https://abc123.ngrok.io`)

**Your public URL will be displayed in the terminal!**

## Method 2: Direct Access (Advanced)

Requires:
- Firewall configuration
- Port forwarding on router
- Static IP or dynamic DNS

```bash
cd back-end/server
python start_chat_public.py --method direct
```

Then access via: `http://YOUR_PUBLIC_IP:5001`

### Firewall Configuration (macOS)

```bash
# Allow incoming connections on port 5001
sudo pfctl -f /etc/pf.conf
# Or use System Preferences > Security & Privacy > Firewall
```

### Port Forwarding

Configure your router to forward port 5001 to your local machine.

## Testing Public Access

Once running, test from another device or use:
```bash
curl https://YOUR_NGROK_URL.ngrok.io/api/health
```

## Security Notes

⚠️ **Important**: 
- The public endpoint is accessible to anyone with the URL
- Consider adding authentication for production use
- Monitor usage and costs (Perplexity API)
