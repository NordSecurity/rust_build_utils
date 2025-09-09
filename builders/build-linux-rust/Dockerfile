FROM rust:1.89.0-bullseye

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Linux Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.28.3-4 /bin/uniffi-bindgen /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.28.3-4 /bin/uniffi-bindgen-cs /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.28.3-4 /bin/uniffi-bindgen-go /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.28.3-4 /bin/uniffi-bindgen-cpp /bin

ENV QDK_TAG=v2.3.14

# Multilib is not present in an arm64 debian but is used by libtelio
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    if apt-cache show gcc-10-multilib > /dev/null 2>&1; then \
        apt-get install -y gcc-10-multilib; \
    else \
        echo "Package gcc-10-multilib does not exist. Skipping installation."; \
    fi; \
    rm -rf /var/lib/apt/lists/* \
        /var/cache/apt/* \
        /var/log/* \
        /usr/share/doc/ \
        /usr/share/man/

RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y \
        # `g++-*` is used by libnudler
        g++-aarch64-linux-gnu \
        g++-arm-linux-gnueabi \
        g++-arm-linux-gnueabihf \
        g++-i686-linux-gnu \
        gcc-aarch64-linux-gnu \
        gcc-arm-linux-gnueabi \
        gcc-arm-linux-gnueabihf \
        gcc-i686-linux-gnu \
        libssl-dev \
        musl-dev \
        musl-tools \
        pip \
        python3-requests \
        pkg-config; \
        rm -rf /var/lib/apt/lists/* \
        /var/cache/apt/* \
        /var/log/* \
        /usr/share/doc/ \
        /usr/share/man/

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

RUN rustup target add \
        x86_64-unknown-linux-gnu \
        x86_64-unknown-linux-musl \
        i686-unknown-linux-gnu \
        armv7-unknown-linux-gnueabihf \
        aarch64-unknown-linux-gnu \
        arm-unknown-linux-gnueabi

RUN rustup component add clippy rustfmt

# Skip llt-secrets check when building in builder images
ENV BYPASS_LLT_SECRETS=1
