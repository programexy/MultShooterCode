import os
import subprocess
import socket
import threading
import select

PORT = int(os.environ.get("PORT", 10000))
GODOT_PORT = 8080

# Start Godot Headless Server on a secondary internal port
os.environ["PORT"] = str(GODOT_PORT)
print(f"Launching Godot server on port {GODOT_PORT}...")
godot_process = subprocess.Popen(["./godot", "--headless", "--main-pack", "project.pck"])

def handle_client(client_socket):
    backend_socket = None
    try:
        backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_socket.connect(("127.0.0.1", GODOT_PORT))
        
        sockets = [client_socket, backend_socket]
        while True:
            r, _, _ = select.select(sockets, [], [], 30)
            if not r:
                break
            for s in r:
                other = backend_socket if s is client_socket else client_socket
                data = s.recv(4096)
                if not data:
                    return
                other.sendall(data)
    except Exception:
        pass
    finally:
        client_socket.close()
        if backend_socket:
            backend_socket.close()

def run_proxy_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)
    print(f"Proxy server listening on port {PORT}")

    while True:
        client_sock, _ = server.accept()
        try:
            client_sock.setblocking(False)
            ready = select.select([client_sock], [], [], 1.0)
            if ready[0]:
                data = client_sock.recv(1024, socket.MSG_PEEK)
                # If it's a standard HTTP health check (not a WebSocket upgrade request)
                if b"GET /" in data and b"Upgrade: websocket" not in data:
                    client_sock.setblocking(True)
                    client_sock.recv(1024)
                    response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 2\r\n\r\nOK"
                    client_sock.sendall(response)
                    client_sock.close()
                    continue
        except Exception:
            pass
        
        client_sock.setblocking(True)
        threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()

# Start proxy server in background thread
threading.Thread(target=run_proxy_server, daemon=True).start()

godot_process.wait()