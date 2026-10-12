FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    wget \
    unzip \
    libfontconfig1 \
    libgl1 \
    libx11-6 \
    libxcursor1 \
    libxi6 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

EXPOSE 10000

# Set environment variable explicitly for server mode
ENV GODOT_SERVER=1

RUN wget https://github.com/godotengine/godot/releases/download/4.7-stable/Godot_v4.7-stable_linux.x86_64.zip \
    && unzip Godot_v4.7-stable_linux.x86_64.zip \
    && mv Godot_v4.7-stable_linux.x86_64 godot \
    && chmod +x godot

CMD ["./godot", "--headless", "--main-pack", "project.pck"]