import os
import subprocess
import socket
import threading

PORT = int(os.environ.get("PORT", 10000))
GODOT_PORT = 8080

# 1. Bind to the port immediately so Render detects an open port instantly
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen(100)
print(f"Immediate port binder listening on {PORT}")

# 2. Start Godot Headless Server on secondary port
os.environ["PORT"] = str(GODOT_PORT)
print(f"Launching Godot server on port {GODOT_PORT}...")
godot_process = subprocess.Popen(["./godot", "--headless", "--main-pack", "project.pck"])

def handle_connection(client_sock):
    try:
        client_sock.settimeout(2.0)
        data = client_sock.recv(1024)
        
        # If it's Render's health check (HTTP GET)
        if b"GET /" in data and b"Upgrade: websocket" not in data:
            response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK"
            client_sock.sendall(response)
            client_sock.close()
            return

        # Otherwise, forward WebSocket traffic to Godot
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend.connect(("127.0.0.1", GODOT_PORT))
        backend.sendall(data) # Forward initial bytes already read

        # Simple bidirectional pipe
        while True:
            client_sock.settimeout(30.0)
            r, _, _ = socket.select([client_sock, backend], [], [])
            if client_sock in r:
                d = client_sock.recv(4096)
                if not d: break
                backend.sendall(d)
            if backend in r:
                d = backend.recv(4096)
                if not d: break
                client_sock.sendall(d)
    except Exception:
        pass
    finally:
        client_sock.close()

def accept_loops():
    while True:
        client_sock, _ = server_socket.accept()
        threading.Thread(target=handle_connection, args=(client_sock,), daemon=True).start()

threading.Thread(target=accept_loops, daemon=True).start()

godot_process.wait()