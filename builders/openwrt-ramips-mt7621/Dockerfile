FROM openwrt/sdk:ramips-mt7621-24.10.2

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="OpenWRT builder image for ramips-mt7621"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

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
    mkdir -p /builder/.local && \
    unzip "protoc-31.1-linux-${PROTOC_ARCH}.zip" -d /builder/.local && \
    rm "protoc-31.1-linux-${PROTOC_ARCH}.zip"

ENV PATH="$PATH:/builder/.local/bin"

# Skip llt-secrets check when building in builder images
ENV BYPASS_LLT_SECRETS=1

# Pin Rust 1.89
RUN echo 'src-git packages https://git.openwrt.org/feed/packages.git^10862df850ae012b34ec9c57a9005b1f7e1e2aca' >> /builder/feeds.conf
