# Release notes

## 2.0.0
- **Breaking** Remove RUSTFLAGS for apple builds. The removal of RUSTFLAGS allows the consuming projects to configure RUSTFLAGS independently. Consumers must set RUSTFLAGS="-C link-arg=-s -C embed-bitcode" manually after updating to this version or add it to a specific profile on cargo manifests.

## 1.0.0
- Add support for Windows aarch64 architecture
- **Breaking** Windows cross compilation no longer supported. Requires MSVC toolchain to be installed. Please use with dedicated Windows runners

