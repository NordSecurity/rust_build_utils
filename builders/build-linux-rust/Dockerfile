FROM rust:1.77.2-bullseye

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Linux Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-cs /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-go /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-cpp /bin

# Multilib is not present in a arm64 debian but is used by libtelio
RUN if apt-cache show gcc-10-multilib > /dev/null 2>&1; then \
        apt-get install -y gcc-10-multilib; \
        rm -rf /var/lib/apt/lists/* \
    else \
        echo "Package gcc-10-multilib does not exist. Skipping installation."; \
    fi

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
        pip \
        python3-requests \
        pkg-config; \
    rm -rf /var/lib/apt/lists/*;

RUN rustup target add \
        x86_64-unknown-linux-gnu \
        i686-unknown-linux-gnu \
        armv7-unknown-linux-gnueabihf \
        aarch64-unknown-linux-gnu \
        arm-unknown-linux-gnueabi

RUN rustup component add clippy rustfmt

# Download crates.io index - entire index won't have to be downloaded for each job
RUN cargo search --limit 1

# Install `sccache`
RUN cargo install sccache --version 0.4.2
