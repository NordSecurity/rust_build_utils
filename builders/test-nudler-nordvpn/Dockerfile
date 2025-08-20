FROM ubuntu:24.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ARG TOKEN
ENV TOKEN=$TOKEN

# Update package list and install essential packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install NordVPN
RUN curl -fsSL https://repo.nordvpn.com/gpg/nordvpn_public.asc | gpg --dearmor -o /usr/share/keyrings/nordvpn-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/nordvpn-archive-keyring.gpg] https://repo.nordvpn.com/deb/nordvpn/debian stable main" | tee /etc/apt/sources.list.d/nordvpn.list \
    && apt-get update \
    && apt-get install -y nordvpn \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install Python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:/app/target/debug:/app/target/release:$PATH"
RUN pip install requests==2.32.5

# Create necessary directories for NordVPN
RUN mkdir -p /run/nordvpn /var/log/nordvpn /var/lib/nordvpn

# Create a non-root user for running the application
RUN useradd -m -s /bin/bash nordvpn-user

# Add user to nordvpn group (required for NordVPN to work)
RUN usermod -aG nordvpn nordvpn-user
