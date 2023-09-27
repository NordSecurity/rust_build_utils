FROM openjdk:8-jdk

ENV ANDROID_COMPILE_SDK 29
ENV ANDROID_BUILD_TOOLS 29.0.2
ENV ANDROID_SDK_TOOLS 4333796

ENV WORKDIR /root
WORKDIR ${WORKDIR}

# Install Android SDK
RUN apt-get install -y wget bash
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
