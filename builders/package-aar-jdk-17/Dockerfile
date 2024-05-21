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
ENV GRADLE_VERSION 8.6

ENV GRADLE_CHECKSUM 85719317abd2112f021d4f41f09ec370534ba288432065f4b477b6a3b652910d
RUN wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-all.zip && \
    echo "${GRADLE_CHECKSUM} gradle-${GRADLE_VERSION}-all.zip" | sha256sum --check && \
    unzip gradle-${GRADLE_VERSION}-all.zip && \
    rm gradle-${GRADLE_VERSION}-all.zip
ENV PATH=${PATH}:${WORKDIR}/gradle-${GRADLE_VERSION}/bin

ENTRYPOINT /bin/bash

ENV WORKDIR ""
