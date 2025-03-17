FROM rust:1.85.0

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="Android Rust builder image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

WORKDIR /source

ENV ANDROIDNDK="/source/.build"
ENV BUILDOS="linux"
ENV NDKVERSION="r26"
ENV NDKZIPNAME="android-ndk-$NDKVERSION-$BUILDOS.zip"
ENV NDKZIP="https://dl.google.com/android/repository/$NDKZIPNAME"
ENV TOOLCHAIN="$ANDROIDNDK/android-ndk-$NDKVERSION/toolchains/llvm/prebuilt/linux-x86_64"

# Used for .cargo/config
ENV PATH="$TOOLCHAIN/bin:$PATH"

RUN mkdir -p "$ANDROIDNDK" && \
    curl -SLO "$NDKZIP" && \
    mv "$NDKZIPNAME" "$ANDROIDNDK/" && \
    unzip "$ANDROIDNDK/$NDKZIPNAME" -d "$ANDROIDNDK" && \
    rm -f "$ANDROIDNDK/$NDKZIPNAME"

RUN \
    # For crate get_if_addr-sys
    ln -s "$TOOLCHAIN/bin/x86_64-linux-android21-clang"     "$TOOLCHAIN/bin/x86_64-linux-android-gcc" && \
    ln -s "$TOOLCHAIN/bin/i686-linux-android21-clang"       "$TOOLCHAIN/bin/i686-linux-android-gcc" && \
    ln -s "$TOOLCHAIN/bin/aarch64-linux-android21-clang"    "$TOOLCHAIN/bin/aarch64-linux-android-gcc" && \
    ln -s "$TOOLCHAIN/bin/armv7a-linux-androideabi21-clang" "$TOOLCHAIN/bin/arm-linux-androideabi-gcc" && \
    ln -s "$TOOLCHAIN/bin/armv7a-linux-androideabi21-clang" "$TOOLCHAIN/bin/arm7a-linux-androideabi-gcc" && \
    ln -s "$TOOLCHAIN/bin/llvm-ar" "$TOOLCHAIN/bin/x86_64-linux-android-ar" && \
    ln -s "$TOOLCHAIN/bin/llvm-ar" "$TOOLCHAIN/bin/i686-linux-android-ar" && \
    ln -s "$TOOLCHAIN/bin/llvm-ar" "$TOOLCHAIN/bin/aarch64-linux-android-ar" && \
    ln -s "$TOOLCHAIN/bin/llvm-ar" "$TOOLCHAIN/bin/arm-linux-androideabi-ar" && \
    ln -s "$TOOLCHAIN/bin/llvm-ar" "$TOOLCHAIN/bin/arm7a-linux-androideabi-ar" && \
    rustup target add i686-linux-android && \
    rustup target add x86_64-linux-android && \
    rustup target add armv7-linux-androideabi && \
    rustup target add aarch64-linux-android

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        pip \
        libssl-dev pkg-config \
        python3-requests && \
    rm -rf /var/lib/apt/lists/*

# Skip llt-secrets check when building in builder images
ENV BYPASS_LLT_SECRETS=1
