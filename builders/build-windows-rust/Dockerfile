FROM rust:1.89.0

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Windows Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

ENV GO_VERSION=1.21.6 \
    GOROOT=/usr/local/go \
    GOPATH=/go \
    PATH=/go/bin:/usr/local/go/bin:$PATH

RUN set -eux; \
    apt-get update; \
    apt-get install -y \
        gcc-mingw-w64 \
        gcc-mingw-w64-x86-64 \
        pip \
        python3-requests \
        libssl-dev \
        pkg-config; \
    rustup target add x86_64-pc-windows-gnu && \
    rm -rf /var/lib/apt/lists/*

RUN ARCH=$(uname -m) && \
    case $ARCH in \
        x86_64) \
            PROTOC_ARCH="x86_64" && \
            CHECKSUM="96553041f1a91ea0efee963cb16f462f5985b4d65365f3907414c360044d8065" ;; \
        aarch64|arm64) \
            PROTOC_ARCH="aarch_64" && \
            CHECKSUM="6c554de11cea04c56ebf8e45b54434019b1cd85223d4bbd25c282425e306ecc2" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    curl -LO "https://github.com/protocolbuffers/protobuf/releases/download/v31.1/protoc-31.1-linux-${PROTOC_ARCH}.zip" && \
    echo "${CHECKSUM}  protoc-31.1-linux-${PROTOC_ARCH}.zip" | sha256sum -c - && \
    mkdir -p /root/.local && \
    unzip "protoc-31.1-linux-${PROTOC_ARCH}.zip" -d /root/.local && \
    rm "protoc-31.1-linux-${PROTOC_ARCH}.zip"

ENV PATH="$PATH:/root/.local/bin"

RUN wget -q https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz; \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz; \
    rm go${GO_VERSION}.linux-amd64.tar.gz; \
    mkdir -p "$GOPATH/src" "$GOPATH/bin" && chmod -R 777 "$GOPATH";

# Skip llt-secrets check when building in builder images
ENV BYPASS_LLT_SECRETS=1
