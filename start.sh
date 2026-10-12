#!/bin/bash

# Default Render port to 10000 if not set
PORT="${PORT:-10000}"
GODOT_PORT=8080

# This is the "cat" block that creates the Nginx configuration file automatically
cat <<EOF > /etc/nginx/sites-available/default
server {
    listen ${PORT};

    # Render health checks and plain GET requests
    location = / {
        if (\$http_upgrade != "websocket") {
            add_header Content-Type text/plain;
            return 200 'OK';
        }

        # WebSocket proxying to Godot
        proxy_pass http://127.0.0.1:${GODOT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Fallback for all other paths
    location / {
        proxy_pass http://127.0.0.1:${GODOT_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

# Start Nginx in background
nginx -g "daemon on;"
echo "Nginx proxy running on port ${PORT}..."

# Force Godot to bind to internal port 8080
export PORT=${GODOT_PORT}
echo "Starting Godot on port ${GODOT_PORT}..."
./godot --headless --main-pack project.pck