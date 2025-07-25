from pathlib import Path
import os
import sys

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

# `sys.path` is the equivalent of `PYTHONPATH`, aka module search paths
sys.path += [f"{PROJECT_ROOT}/.."]
import rust_build_utils.rust_utils as rutils
import rust_build_utils.msvc as msvc
from rust_build_utils.rust_utils_config import (
    GLOBAL_CONFIG,
    WINDOWS_RUNTIME_LINKING,
    WindowsLinkingMethod,
)
import rust_build_utils.darwin_build_utils as dbu
import rust_build_utils.android_build_utils as abu


PROJECT_CONFIG = rutils.Project(
    rust_version="1.85.0",
    root_dir=PROJECT_ROOT,
    working_dir=None,
)


def pre_function(config):
    print("This happens before anything else")


def post_function(config, packages):
    print(f"Built packages: {list(packages.keys())}")


def post_function_win(config, args):
    packages = SAMPLE_CONFIG[config.target_os].get("packages", None)
    if packages and config.target_os == "windows":
        for _, bins in packages.items():
            for _, bin in bins.items():
                dll_bin = os.path.splitext(bin)[0] + ".dll"
                dll_bin_path = PROJECT_CONFIG.get_cargo_path(
                    config.rust_target, dll_bin, config.debug
                )
                if os.path.isfile(dll_bin_path):
                    should_link_statically = (
                        WINDOWS_RUNTIME_LINKING[WindowsLinkingMethod.STATIC]
                        in GLOBAL_CONFIG["windows"]["env"]["RUSTFLAGS"]
                    )
                    msvc_context = None
                    if not msvc.is_msvc_active():
                        msvc_context = msvc.activate_msvc(
                            "amd64" if config.arch == "x86_64" else config.arch
                        )
                    res = msvc.check_for_static_runtime(
                        Path(dll_bin_path), should_link_statically
                    )
                    if msvc_context is not None:
                        msvc.deactivate_msvc(msvc_context)
                    if not res:
                        print("Incorrect windows runtime linking")
                        exit(1)
                    print("Runtime linking for windows is correct!")


"""
This local config is highly customizable as every project can have a different
local config depending on their needs.

Here are some generic attributes that you may wish to use in several projects:
      "build_args"  : [Optional, List<str>]:
          List of global arguments to be passed for all packages to be built.
          If you need per-package arguments, you can invoke the build() method
          for each package with different extra_args arguments.

      "packages"    : [Dict<str, Dict<str, str>>]:
          Dictionary of packages to build and binaries to distribute.

          The keys are package names, while the values are dictionaries,
          with binary names as keys and their file names as values.

      "pre_build"   : [Optional, List<function>]:
          list of project specific functions to call before the build begins
          (this is called before the GLOBAL pre_build)

      "post_build"  : [Optional, List<function>]:
          list of project specific functions to call after the build finishes
          (this is called after the GLOBAL post_build)

If you would like to have local environment variables, here is a way to do it for the needed OS:
      "env"         : [Optional, Dictionary]:
          dictionary where the key is the environment variable and the value is
          a tuple of (String, String) where member[0] is the value of the flag
          and [1] is either "set" or "append". Member[1] will only be used if
          no such variable already exists in the GLOBAL_CONFIG
          in which case, "set" means that the variable will be cleared before setting it

And another way where you need an environment variable for a specific ARCH build of an OS
      "archs" : Dictionary for multiple arches that are built for an OS
          "$ARCH": Dictionary for any specific configuration to be done for that arch
              "env" : Same structure as the OS specific dictionary

The environment example is given here as well as in the GLOBAL_CONFIG,
you can have both arch specific and OS specific variables at the same time
"""

SAMPLE_CONFIG = {
    "ios": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.dylib",
            },
        },
    },
    "tvos": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.dylib",
            },
        },
    },
    "ios-sim": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.dylib",
            },
        },
    },
    "tvos-sim": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.dylib",
            },
        },
    },
    "linux": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
            },
            "rust_sample_pack": {
                "rust_sample_pack": "rust_sample_pack",
            },
        },
        "post_build": [post_function],
        "env": {
            "RUSTFLAGS": (" -Aunused", "set"),
        },
    },
    "macos": {
        "archs": {"aarch64": {"env": {"RUSTFLAGS": (" -C debuginfo=2", "set")}}},
        "packages": {
            "rust_sample": {
                "rust_sample": "librust_sample.dylib",
            },
            "rust-sample-lib": {
                "rust-sample-lib": "librust_sample_lib.dylib",
            },
            "rust_sample_pack": {
                "rust_sample_pack": "rust_sample_pack",
            },
        },
        "pre_build": [pre_function],
        "post_build": [post_function],
        "env": {"RUSTFLAGS": (" -Aunused", "set")},
    },
    "windows": {
        "build_args": ["--crate-type", "cdylib", "--lib"],
        "packages": {
            "rust-sample-lib": {
                "rust-sample-lib": "rust_sample_lib.dll",
            },
        },
        "env": {
            "RUSTFLAGS": (WINDOWS_RUNTIME_LINKING[WindowsLinkingMethod.STATIC], "set"),
        },
        "pre_build": [pre_function],
        "post_build": [post_function, post_function_win],
        "build_func": rutils.cargo_rustc,
    },
    "android": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.so",
            },
        },
        "pre_build": [pre_function],
        "binding_src": f"ffi/java",
        "binding_dest": f"dist/android/",
    },
}


def copy_bindings(config):
    if "binding_src" in SAMPLE_CONFIG[config.target_os]:
        bindings = f"{PROJECT_CONFIG.root_dir}/{SAMPLE_CONFIG[config.target_os]['binding_src']}"
        binding_destination = (
            f"{PROJECT_CONFIG.root_dir}/{SAMPLE_CONFIG[config.target_os]['binding_dest']}"
            + bindings.split("/")[-1]
        )

        if os.path.exists(binding_destination):
            rutils.remove_tree_or_file(binding_destination)

        rutils.copy_tree_or_file(bindings, binding_destination)


def main() -> None:
    args = rutils.parse_cli()
    if args.command == "build":
        exec_build(args)
    elif args.command == "bindings":
        rutils.generate_uniffi_bindings(
            PROJECT_CONFIG, "v0.28.3-3", ["python"], "src/sample.udl"
        )
    elif args.command == "lipo":
        exec_lipo(args)
    elif args.command == "xcframework":
        headers = {
            Path("rust_sample/rust_sample.h"): PROJECT_CONFIG.get_root_dir()
            / "ffi/rust_sample.h",
        }
        dbu.create_xcframework(
            PROJECT_CONFIG,
            args.debug,
            "RustSample",
            "librust_sample_framework",
            headers,
            "librust_sample.dylib",
        )
    elif args.command == "aar":
        abu.generate_aar(PROJECT_CONFIG, args)
    elif args.command == "build-ios-simulator-stubs":
        dbu.build_stub_ios_simulator_libraries(
            PROJECT_CONFIG,
            args.debug,
            args.header or PROJECT_CONFIG.get_root_dir() / "ffi/rust_sample.h",
            "librust_sample.dylib",
        )
    elif args.command == "build-tvos-simulator-stubs":
        dbu.build_stub_tvos_simulator_libraries(
            PROJECT_CONFIG,
            args.debug,
            args.header or PROJECT_CONFIG.get_root_dir() / "ffi/rust_sample.h",
            "librust_sample.dylib",
        )
    else:
        assert False, f"unsupported command '{args.command}'"


def exec_build(args):
    config = rutils.CargoConfig(
        args.os,
        args.arch,
        args.debug,
    )
    rutils.check_config(config)
    call_build(config)


def darwin_build_all(debug: bool) -> None:
    for target_os in rutils.LIPO_TARGET_OSES:
        for arch in GLOBAL_CONFIG[target_os]["archs"].keys():
            if target_os in SAMPLE_CONFIG:
                config = rutils.CargoConfig(
                    target_os,
                    arch,
                    debug,
                )

                call_build(config)


def exec_lipo(args):
    if args.build:
        darwin_build_all(args.debug)

    for target_os in rutils.LIPO_TARGET_OSES:
        dbu.lipo(
            PROJECT_CONFIG,
            args.debug,
            target_os,
            SAMPLE_CONFIG[target_os]["packages"],
        )


def call_build(config):
    rutils.config_local_env_vars(config, SAMPLE_CONFIG)

    if "pre_build" in SAMPLE_CONFIG[config.target_os]:
        for pre in SAMPLE_CONFIG[config.target_os]["pre_build"]:
            pre(config)

    packages = SAMPLE_CONFIG[config.target_os]["packages"]

    builder = SAMPLE_CONFIG[config.target_os].get("build_func", rutils.cargo_build)
    builder(
        PROJECT_CONFIG,
        config,
        packages,
        SAMPLE_CONFIG[config.target_os].get("build_args", None),
    )

    copy_bindings(config)

    if "post_build" in SAMPLE_CONFIG[config.target_os]:
        for post in SAMPLE_CONFIG[config.target_os]["post_build"]:
            post(config, packages)


if __name__ == "__main__":
    main()
