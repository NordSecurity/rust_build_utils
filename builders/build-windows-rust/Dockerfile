FROM rust:1.72.1

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Windows Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

# Download crates.io index - entire index won't have to be downloaded for each job
RUN cargo search --limit 0

ENV GO_VERSION=1.18 \
    GOROOT=/usr/local/go \
    GOPATH=/go \
    PATH=/go/bin:/usr/local/go/bin:$PATH

RUN set -eux; \
    apt-get update; \
    apt-get install -y \
        gcc-mingw-w64 \
        gcc-mingw-w64-x86-64 \
        pip \
        libssl-dev \
        pkg-config; \
    rustup target add x86_64-pc-windows-gnu && \
    rm -rf /var/lib/apt/lists/*

RUN wget -q https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz; \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz; \
    rm go${GO_VERSION}.linux-amd64.tar.gz; \
    mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH";

# Install `sccache`
RUN cargo install sccache --version 0.4.2
