import os
import subprocess
import http.server
import socketserver
import threading

PORT = int(os.environ.get("PORT", 10000))

# 1. Simple HTTP server to satisfy Render's health check
class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Godot Server is Running")

def run_http_server():
    with socketserver.TCPServer(("0.0.0.0", PORT), HealthHandler) as httpd:
        print(f"Serving HTTP health checks on port {PORT}")
        httpd.serve_forever()

# Start HTTP server in a background thread
threading.Thread(target=run_http_server, daemon=True).start()

# 2. Launch Godot Headless Server on a secondary port (e.g., 8080)
godot_port = 8080
os.environ["PORT"] = str(godot_port)
print(f"Launching Godot server on port {godot_port}...")
subprocess.run(["./godot", "--headless", "--main-pack", "project.pck"])