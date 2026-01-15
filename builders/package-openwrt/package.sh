#!/bin/bash
set -euxo pipefail

# This script assumes that it runs inside SDK container.
# OpenWRT published SDK images here: https://hub.docker.com/r/openwrt/sdk

grep -q "This is the OpenWrt SDK" /builder/README.md || {
    echo "Expecting to run inside one of OpenWRT SDK containers: https://hub.docker.com/r/openwrt/sdk "
    exit 1
}

usage() {
    echo "Usage: $0 <feed-path> <feed-type> <precompiled-binary> <package-name> <arch> <package-extension>"
    echo ""
    echo "  feed-path               Path or URL to the feed (e.g. /path/to/feed or https://...)"
    echo "  feed-type               Type of feed source: src-git or src-link"
    echo "  precompiled-binary      Path to the prebuilt binary to package"
    echo "  package-name            Package name"
    echo "  arch                    Architecture"
    echo "  package-extension       ipk or apk"
    echo ""
    exit 1
}

# Detect architecture from the binary file and map it to rust_build_utils target
detect_binary_arch_from_bin() {
    local machine
    machine=$(readelf -h "$1" | awk -F: '/Machine:/ {print $2}' | xargs)
    case "$machine" in
        "Advanced Micro Devices X86-64") echo "x86_64" ;;
        "MIPS R3000") echo "mipsel" ;;
        "AArch64") echo "aarch64" ;;
        *) echo "ERROR: unsupported ELF: $machine" >&2; exit 1 ;;
    esac
}

# Ask the OpenWrt build system what package arch it is producing for
sdk_arch_packages() {
    local v
    v=$(make -s val.ARCH_PACKAGES 2>/dev/null | awk -F= '{print $2}' | xargs || true)

    if [ -z "$v" ]; then
        echo ""
        return 0
    fi

    case "$v" in
        x86_64*) echo "x86_64" ;;
        aarch64*) echo "aarch64" ;;
        mipsel*) echo "mipsel" ;;
        *) echo "$v" ;;
    esac
}

if [ "$#" -ne 6 ]; then
    echo "ERROR: Missing or extra arguments." >&2
    usage
fi

echo "Generating OpenWrt package inside SDK container"

FEED_PATH="$1"
FEED_TYPE="$2"
PRECOMPILED_BINARY="$3"
PKG_NAME="$4"
PKG_ARCH="$5"
PKG_EXT="$6"

case "$PKG_ARCH" in
  x86_64|aarch64|mipsel) ;;
  *)
    echo "ERROR: Unsupported arch input: $PKG_ARCH (expected one of: x86_64, aarch64, mipsel)" >&2
    exit 1
    ;;
esac

WORKDIR=/builder
FEED_NAME=custom
cd "$WORKDIR"

# Generate default .config, it is enough to call this once so TUI wouldn't popup and block the execution.
make defconfig

# Enforce provided binary architecture matches expected SDK architecture
binary_arch=$(detect_binary_arch_from_bin "$PRECOMPILED_BINARY")
if [ "$binary_arch" != "$PKG_ARCH" ]; then
    echo "ERROR: Arch mismatch: binary=$binary_arch expected=$PKG_ARCH" >&2
    exit 1
fi

sdk_arch=$(sdk_arch_packages || true)
if [ -n "$sdk_arch" ] && [ "$sdk_arch" != "$PKG_ARCH" ]; then
    echo "WARNING: SDK ARCH_PACKAGES=$sdk_arch does not match expected=$PKG_ARCH" >&2
fi

workers=$(nproc)

# https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem
mkdir -p dist
echo "$FEED_TYPE $FEED_NAME $FEED_PATH" > feeds.conf
./scripts/feeds update -a
./scripts/feeds install -a

# The logs overflow CI/CD log limit so they are redirected to a file instead
if [ "${GITLAB_CI:-}" == "true" ]; then
    make package/${PKG_NAME}/{clean,compile} -j"$workers" V=s PKG_BINFILE="$PRECOMPILED_BINARY" > /tmp/build.log 2>&1
else
    make package/${PKG_NAME}/{clean,compile} -j"$workers" V=s PKG_BINFILE="$PRECOMPILED_BINARY"
fi

# Find the resulting .ipk(there should be just one)
pkg_path=$(find "$WORKDIR/bin/packages" -type f -name "*.${PKG_EXT}" | head -n1)

if [ -z "$pkg_path" ]; then
    echo "ERROR: No .${PKG_EXT} found in $WORKDIR/bin/packages" >&2
    exit 2
fi

echo $pkg_path
