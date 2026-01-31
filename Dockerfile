# Forge CLI - Docker Test Environment
# Ubuntu 22.04 with Python 3.11

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install base dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    sudo \
    systemctl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access
RUN useradd -m -s /bin/bash forge && \
    echo "forge ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /home/forge/app

# Copy project files
COPY . .

# Fix ownership
RUN chown -R forge:forge /home/forge

# Switch to forge user
USER forge

# Create virtual environment and install dependencies
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -e . && \
    pip install pytest pytest-mock

# Set PATH to include venv
ENV PATH="/home/forge/app/venv/bin:$PATH"

# Default command - run tests
CMD ["pytest", "-v", "tests/"]
