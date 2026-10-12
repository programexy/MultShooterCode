# Use Linux container
FROM ubuntu:22.04

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ca-certificates \
    libfontconfig1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Download Godot 4 headless export template
WORKDIR /app
COPY . /app

# Expose port
EXPOSE 10000

# Download and run Godot Engine in headless mode
RUN wget https://github.com/godotengine/godot/releases/download/4.2.1-stable/Godot_v4.2.1-stable_linux.x86_64.zip \
    && unzip Godot_v4.2.1-stable_linux.x86_64.zip \
    && mv Godot_v4.2.1-stable_linux.x86_64 godot \
    && chmod +x godot

CMD ["./godot", "--headless", "--main-pack", "project.pck"]