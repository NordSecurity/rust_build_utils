FROM openjdk:8-jdk

ARG REVISION

LABEL org.opencontainers.image.source=https://github.com/NordSecurity/rust_build_utils
LABEL org.opencontainers.image.description="AAR packaging image"
LABEL org.opencontainers.image.licenses=GPL-3.0
LABEL org.opencontainers.image.revision=$REVISION

ENV ANDROID_COMPILE_SDK 29
ENV ANDROID_BUILD_TOOLS 29.0.2
ENV ANDROID_SDK_TOOLS 4333796

ENV WORKDIR /root
WORKDIR ${WORKDIR}

# Install Android SDK
RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    python3-requests \
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

ENV ANDROID_SKD_CHECKSUM 92ffee5a1d98d856634e8b71132e8a95d96c83a63fde1099be3d86df3106def9
RUN wget --output-document=android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-${ANDROID_SDK_TOOLS}.zip && \
    echo "${ANDROID_SKD_CHECKSUM} android-sdk.zip" | sha256sum --check && \
    mkdir android-sdk-linux && \
    unzip -d android-sdk-linux android-sdk.zip && \
    rm android-sdk.zip

RUN echo y | android-sdk-linux/tools/bin/sdkmanager "platforms;android-${ANDROID_COMPILE_SDK}" && \
    echo y | android-sdk-linux/tools/bin/sdkmanager "platform-tools" && \
    echo y | android-sdk-linux/tools/bin/sdkmanager "build-tools;${ANDROID_BUILD_TOOLS}" && \
    yes | android-sdk-linux/tools/bin/sdkmanager --licenses

ENV ANDROID_HOME=${WORKDIR}/android-sdk-linux
ENV PATH=${PATH}:${ANDROID_HOME}/platform-tools

# Install gradle
ENV GRADLE_VERSION 6.5

RUN wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-all.zip
ENV GRADLE_CHECKSUM c9910513d0eed63cd8f5c7fec4cb4a05731144770104a0871234a4edc3ba3cef
RUN echo "${GRADLE_CHECKSUM} gradle-6.5-all.zip" | sha256sum --check
RUN unzip gradle-${GRADLE_VERSION}-all.zip
RUN rm gradle-${GRADLE_VERSION}-all.zip
ENV PATH=${PATH}:${WORKDIR}/gradle-${GRADLE_VERSION}/bin

ENTRYPOINT /bin/bash

ENV WORKDIR ""
