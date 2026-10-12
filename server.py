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

def handle_websocket_tunnel(client_socket, initial_data):
    backend_socket = None
    try:
        backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_socket.connect(("127.0.0.1", GODOT_PORT))
        
        # Forward the initial handshake bytes read during inspection
        backend_socket.sendall(initial_data)
        
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
    server.listen(100)
    print(f"Proxy server listening on port {PORT}")

    while True:
        client_sock, _ = server.accept()
        try:
            client_sock.settimeout(3.0)
            data = client_sock.recv(4096) # Read the actual request data
            
            if b"Upgrade: websocket" in data or b"sec-websocket-key" in data.lower():
                client_sock.settimeout(None)
                threading.Thread(target=handle_websocket_tunnel, args=(client_sock, data), daemon=True).start()
            else:
                client_sock.settimeout(None)
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/plain\r\n"
                    b"Content-Length: 2\r\n"
                    b"Connection: close\r\n\r\n"
                    b"OK"
                )
                client_sock.sendall(response)
                client_sock.close()
        except Exception:
            try:
                client_sock.close()
            except:
                pass

# Start proxy server in background thread
threading.Thread(target=run_proxy_server, daemon=True).start()

godot_process.wait()