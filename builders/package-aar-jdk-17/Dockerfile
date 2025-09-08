FROM openjdk:17-jdk-slim-bullseye

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="AAR packaging image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

ENV ANDROID_COMPILE_SDK 29
ENV ANDROID_BUILD_TOOLS 29.0.2
ENV ANDROID_SDK_TOOLS 10406996

ENV ANDROID_SDK_ROOT /root/android-sdk-linux/

ENV WORKDIR /root
WORKDIR ${WORKDIR}

# Install Android SDK
RUN apt-get update && apt-get install -y \
        openjdk-11-jdk \
        bash \
        curl \
        git \
        python3 \
        python3-requests \
        python3-pip \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*
    
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

ENV ANDROID_SDK_CHECKSUM 8919e8752979db73d8321e9babe2caedcc393750817c1a5f56c128ec442fb540
RUN wget --output-document=android-sdk.zip https://dl.google.com/android/repository/commandlinetools-linux-${ANDROID_SDK_TOOLS}_latest.zip && \
    echo "${ANDROID_SDK_CHECKSUM} android-sdk.zip" | sha256sum --check && \
    mkdir android-sdk-linux && \
    unzip -d android-sdk-linux android-sdk.zip && \
    rm android-sdk.zip

RUN echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platforms;android-${ANDROID_COMPILE_SDK}" && \
    echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platform-tools" && \
    echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;${ANDROID_BUILD_TOOLS}" && \
    yes | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} --licenses

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV ANDROID_HOME=${WORKDIR}/android-sdk-linux
ENV PATH=${PATH}:${ANDROID_HOME}/platform-tools

# Install gradle
ENV GRADLE_VERSION 9.0.0
ENV GRADLE_CHECKSUM f759b8dd5204e2e3fa4ca3e73f452f087153cf81bac9561eeb854229cc2c5365

RUN wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-all.zip && \
    echo "${GRADLE_CHECKSUM} gradle-${GRADLE_VERSION}-all.zip" | sha256sum --check && \
    unzip gradle-${GRADLE_VERSION}-all.zip && \
    rm gradle-${GRADLE_VERSION}-all.zip
ENV PATH=${PATH}:${WORKDIR}/gradle-${GRADLE_VERSION}/bin

ENTRYPOINT /bin/bash

ENV WORKDIR ""
