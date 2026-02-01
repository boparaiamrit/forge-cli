# Forge CLI - Docker Test Environment
# Ubuntu 22.04 with Python 3.11, Nginx, PHP-FPM

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install base dependencies and server software for testing
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    sudo \
    lsof \
    net-tools \
    iproute2 \
    openssl \
    nginx \
    certbot \
    python3-certbot-nginx \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add PHP repository and install PHP
RUN add-apt-repository -y ppa:ondrej/php && \
    apt-get update && apt-get install -y \
    php8.3-fpm \
    php8.3-cli \
    php8.3-common \
    php8.3-mysql \
    php8.3-pgsql \
    php8.3-redis \
    php8.3-mbstring \
    php8.3-xml \
    php8.3-curl \
    php8.3-zip \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with sudo access
RUN useradd -m -s /bin/bash forge && \
    echo "forge ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create necessary directories
RUN mkdir -p /var/www && \
    mkdir -p /var/log/nginx && \
    mkdir -p /etc/nginx/sites-available && \
    mkdir -p /etc/nginx/sites-enabled && \
    chown -R www-data:www-data /var/www && \
    touch /var/log/nginx/access.log && \
    touch /var/log/nginx/error.log

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
    pip install pytest pytest-mock pytest-cov

# Set PATH to include venv
ENV PATH="/home/forge/app/venv/bin:$PATH"

# Expose ports for testing
EXPOSE 80 443 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Default command - run tests
CMD ["pytest", "-v", "--tb=short", "tests/"]
