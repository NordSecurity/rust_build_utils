# Release notes

## 9.0.0
- **Breaking** Rust version moved from image name to image tag: `build-linux-rust1.99.1:vX.Y.Z` is now `build-linux-rust:1.99.1-vX.Y.Z`
- Builder images are released with the same version as rust_build_utils, see "Versioning" in README.md
- Merging a PR with a new CHANGELOG.md version releases the tag, GitHub Release and images; Rust version is declared in builder Dockerfiles
- Builder images are labeled with `org.opencontainers.image.version`
- CI checks that PRs changing the library or images add a new CHANGELOG.md version
- Enable emutls for Android
- Fix `cargo_rustc` when using nightly toolchain
- Only remove artifacts of the packages being built
- Keep distribution dir when built binaries are unchanged
- OpenWrt musl targets use musl headers instead of glibc
- Fix AAR template regression after Gradle 9 update
- Fix warnings in package-aar-jdk-17 image build

## 8.3.0
_Released only as `build-linux-rust1.99.1:v8.3.0` image, without a git tag_
- Rust tool-chain version updated to 1.99.1
- Bump rustup in build-linux-rust image

## 8.2.0
_Released only as `build-linux-rust1.98.1:v8.2.0` image, without a git tag_
- Rust tool-chain version updated to 1.98.1

## 8.1.0
_Released only as `build-linux-rust1.89.0:v8.1.0` image, without a git tag_
- Update Debian 11 based images

## 8.0.0
- **Breaking** Remove OpenWrt toolchains from build-linux-rust image, use new build-openwrt-rust image instead
- Add ARM support to OpenWrt
- Create output dir for OpenWrt packages if it does not exist

## 7.4.3
- Revert rust fuzzing support

## 7.4.2
- Add OpenWrt 25.12 support to package.sh
- Add rust fuzzing support
- Allow building mips, fix endianness detection
- Detect library type by file extension when creating xcframework
- Use macos-15 instead of macos-13

## 7.4.1
- Print OpenWrt package build logs when run locally

## 7.4.0
- Replace deprecated openjdk images in package-aar-jdk-17
- Update ios-sim minimum OS version

## 7.3.0
- Add support for OpenWrt ipk package rebuilding

## 7.2.4
- Add fetch artifacts parser
- Stop copying file metadata to avoid permission errors

## 7.2.3
- Add OpenWrt (musl) support and packaging
- Add debug symbols for MIPS builds

## 7.2.2
- Add libclang to build-windows-rust image
- Point aws-lc to correct include path

## 7.2.1
- Add cmake to build-windows-rust image

## 7.2.0
- Add cmake and libclang-dev to builder images
- Point aws-lc-rs to correct include paths on linux images
- Define ANDROID_NDK
- Always install rustfmt after setting default rust version

## 7.1.1
- Bump uniffi generators to v0.28.3-4

## 7.1.0
- Update Gradle to 9.0.0

## 7.0.1
- Fix Control Flow Guard on Windows

## 7.0.0
- **Breaking** Drop QNAP support
- Pin Rust package to 1.89

## 6.5.0
- Add test-nudler-nordvpn image
- Add OpenWrt One target architecture

## 6.4.0
- Add Control Flow Guard to Windows build

## 6.3.0
- Rust tool-chain version updated to 1.89.0

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

