import os
import subprocess
import socket
import threading
import select

PORT = int(os.environ.get("PORT", 10000))
GODOT_PORT = 8080

# Start Godot Headless Server on internal port
os.environ["PORT"] = str(GODOT_PORT)
print(f"Launching Godot server on port {GODOT_PORT}...")
subprocess.Popen(["./godot", "--headless", "--main-pack", "project.pck"])

def proxy_loop(client, backend):
    sockets = [client, backend]
    try:
        while True:
            r, _, _ = select.select(sockets, [], [], 30)
            if not r: break
            for s in r:
                other = backend if s is client else client
                data = s.recv(4096)
                if not data: return
                other.sendall(data)
    except:
        pass
    finally:
        client.close()
        backend.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", PORT))
server.listen(50)
print(f"Server wrapper listening on port {PORT}")

while True:
    client_sock, _ = server.accept()
    try:
        client_sock.settimeout(2.0)
        peek_data = client_sock.recv(1024, socket.MSG_PEEK)
        
        # Answer Render HTTP health checks instantly
        if b"GET " in peek_data and b"Upgrade: websocket" not in peek_data:
            client_sock.settimeout(None)
            client_sock.recv(1024)
            response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK"
            client_sock.sendall(response)
            client_sock.close()
            continue
            
        # Forward all WebSockets to Godot
        client_sock.settimeout(None)
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend.connect(("127.0.0.1", GODOT_PORT))
        threading.Thread(target=proxy_loop, args=(client_sock, backend), daemon=True).start()
    except:
        client_sock.close()