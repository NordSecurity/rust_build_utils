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
RUN apt-get update && apt-get install -y wget bash unzip curl python3
ENV ANDROID_SKD_CHECKSUM 8919e8752979db73d8321e9babe2caedcc393750817c1a5f56c128ec442fb540
RUN wget --output-document=android-sdk.zip https://dl.google.com/android/repository/commandlinetools-linux-${ANDROID_SDK_TOOLS}_latest.zip && \
    echo "${ANDROID_SKD_CHECKSUM} android-sdk.zip" | sha256sum --check && \
    mkdir android-sdk-linux && \
    unzip -d android-sdk-linux android-sdk.zip && \
    rm android-sdk.zip

RUN echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platforms;android-${ANDROID_COMPILE_SDK}"
RUN echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "platform-tools"
RUN echo y | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} "build-tools;${ANDROID_BUILD_TOOLS}"
RUN yes | android-sdk-linux/cmdline-tools/bin/sdkmanager --sdk_root=${ANDROID_SDK_ROOT} --licenses

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV ANDROID_HOME=${WORKDIR}/android-sdk-linux
ENV PATH=${PATH}:${ANDROID_HOME}/platform-tools

# Install gradle
ENV GRADLE_VERSION 8.4

RUN wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-all.zip
ENV GRADLE_CHECKSUM f2b9ed0faf8472cbe469255ae6c86eddb77076c75191741b4a462f33128dd419
RUN echo "${GRADLE_CHECKSUM} gradle-${GRADLE_VERSION}-all.zip" | sha256sum --check
RUN unzip gradle-${GRADLE_VERSION}-all.zip
RUN rm gradle-${GRADLE_VERSION}-all.zip
ENV PATH=${PATH}:${WORKDIR}/gradle-${GRADLE_VERSION}/bin

ENTRYPOINT /bin/bash

ENV WORKDIR ""
