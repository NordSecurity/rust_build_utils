FROM rust:1.85.0-bullseye

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Linux Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-cs /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-go /bin
COPY --from=ghcr.io/nordsecurity/uniffi-generators:v0.25.0-8 /bin/uniffi-bindgen-cpp /bin

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

RUN rustup target add \
        x86_64-unknown-linux-gnu \
        x86_64-unknown-linux-musl \
        i686-unknown-linux-gnu \
        armv7-unknown-linux-gnueabihf \
        aarch64-unknown-linux-gnu \
        aarch64-unknown-linux-musl \
        arm-unknown-linux-gnueabi

RUN rustup component add clippy rustfmt

# Install QDK framework for QNAP packages (QPKG)
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    git clone https://github.com/qnap-dev/QDK.git --branch "${QDK_TAG}"; \
    cd QDK && ./InstallToUbuntu.sh install && cd -; \
    rm -rf QDK \
        /var/lib/apt/lists/* \
        /var/cache/apt/* /var/log/* \
        /usr/share/doc/ \
        /usr/share/man/

# Skip llt-secrets check when building in builder images
ENV BYPASS_LLT_SECRETS=1
