# Release notes

## 6.0.2
- Bump uniffi generators to v0.28.3-3

## 6.0.1
- Windows static C runtime check

## 6.0.0
- Bump uniffi to 0.28.3

## 5.0.0
- Rust tool-chain version updated to 1.85.0

## 3.3.0
- build-linux-rust and build-linux-rust are now built also for linux/arm64

## 3.2.0
- Add `python-requests` to Docker images
- Allow uniffi gnerator to run outside docker
- Linux Rust builder container can generate uniffi bindings

## 3.1.0
- Bump Gradle version in package-aar-jdk-17 image
- Update README.md

## 3.0.0

- **Breaking** Change linux armv7 arch name to armv7hf

## 2.2.0
- build_stub_library function now builds either static lib or dynamic lib based on the extension of the output file (.a or .dylib)
- added functionality for uniffi bindings generation

## 2.1.0
- Update minSdkVersion in build.gradle to 24 to support UniFFI generated Kotlin code

## 2.0.0
- **Breaking** Remove RUSTFLAGS for apple builds. The removal of RUSTFLAGS allows the consuming projects to configure RUSTFLAGS independently. Consumers must set RUSTFLAGS="-C link-arg=-s -C embed-bitcode" manually after updating to this version or add it to a specific profile on cargo manifests.

## 1.0.0
- Add support for Windows aarch64 architecture
- **Breaking** Windows cross compilation no longer supported. Requires MSVC toolchain to be installed. Please use with dedicated Windows runners

