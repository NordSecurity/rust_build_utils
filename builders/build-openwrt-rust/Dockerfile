FROM rust:1.89.0

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="OpenWrt Rust builder image"
LABEL org.opencontainers.image.revision=$REVISION

RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get install -y \
        cmake \
        # aarch64 musl builds use glibc gcc as linker
        gcc-aarch64-linux-gnu \
        libclang-dev \
        libssl-dev \
        musl-dev \
        musl-tools \
        python3-requests \
        pkg-config; \
    if apt-cache show pip > /dev/null 2>&1; then \
        apt-get install -y pip; \
    else \
        apt-get install -y python3-pip; \
    fi; \
    dpkg --add-architecture arm64; \
    apt-get update; \
    # for aarch64 musl headers, should not use glibc headers
    apt-get install -y musl-dev:arm64; \
    rm -rf /var/lib/apt/lists/*

# protoc
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

# Musl cross-compilers (from our own mirrors — musl.cc blocks GitHub Actions)
RUN curl -LO https://github.com/NordSecurity/rust_build_utils/releases/download/mirror_mipsel-linux-muslsf-cross.tgz/mipsel-linux-muslsf-cross.tgz \
    && tar -xzf mipsel-linux-muslsf-cross.tgz -C /opt \
    && rm mipsel-linux-muslsf-cross.tgz

RUN curl -LO https://github.com/NordSecurity/rust_build_utils/releases/download/mirror_mips-linux-muslsf-cross.tgz/mips-linux-muslsf-cross.tgz \
    && tar -xzf mips-linux-muslsf-cross.tgz -C /opt \
    && rm mips-linux-muslsf-cross.tgz

RUN curl -LO https://github.com/NordSecurity/rust_build_utils/releases/download/mirror_arm-linux-musleabihf-cross.tgz/arm-linux-musleabihf-cross.tgz \
    && tar -xzf arm-linux-musleabihf-cross.tgz -C /opt \
    && rm arm-linux-musleabihf-cross.tgz

# Rust musl targets
RUN rustup target add \
        x86_64-unknown-linux-musl \
        aarch64-unknown-linux-musl \
        armv7-unknown-linux-musleabihf

RUN rustup component add clippy rustfmt

# Cargo linker config for cross-compilation
COPY builders/build-openwrt-rust/cargo-config.toml ${CARGO_HOME}/config.toml

# musl include for cross-compilation (needed for AWS_LC)
# rustup doesn't bundle musl includes and includes are picked from linker aarch64-linux-gnu-gcc
ENV CFLAGS_aarch64_unknown_linux_musl="-isystem /usr/include/aarch64-linux-musl"

ENV BYPASS_LLT_SECRETS=1
