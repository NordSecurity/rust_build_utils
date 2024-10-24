FROM ubuntu:22.04

ARG REVISION


LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="QPKG builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

ENV WORKDIR=/root
WORKDIR ${WORKDIR}

ENV QDK_TAG=v2.3.14

RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
	apt-get update -y; \
    apt-get install -y --no-install-recommends \
    git-core \
    ca-certificates \
	rsync

# Install QDK
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    git clone https://github.com/qnap-dev/QDK.git --branch "${QDK_TAG}"; \
    cd QDK; \
    ./InstallToUbuntu.sh install

# Cleanup
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
	apt-get remove --purge -yq; \
    apt-get autoclean -y; \
    apt-get autoremove -y; \
    rm -rf QDK; \
    rm -rf /var/lib/{cache,log}/; \
    rm -rf /var/lib/apt/lists/*; \
    rm -rf /tmp/* /var/tmp/*; \
    rm -rf /usr/share/doc/; \
    rm -rf /usr/share/man/

ENV PATH="/usr/share/QDK/bin:${PATH}"