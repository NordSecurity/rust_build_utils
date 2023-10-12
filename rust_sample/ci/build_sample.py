from pathlib import Path
import os
import sys

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

# `sys.path` is the equivalent of `PYTHONPATH`, aka module search paths
sys.path += [f"{PROJECT_ROOT}/.."]
import rust_build_utils.rust_utils as rutils
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG
import rust_build_utils.darwin_build_utils as dbu
import rust_build_utils.android_build_utils as abu


PROJECT_CONFIG = rutils.Project(
    rust_version="1.72.1",
    root_dir=PROJECT_ROOT,
    working_dir=None,
)


def pre_function(config):
    print("This happens before anything else")


def post_function(config, packages):
    print(f"Built packages: {list(packages.keys())}")


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
                "rust_sample": "librust_sample.a",
            },
        },
    },
    "tvos": {
        "packages": {
            "rust_sample": {
                "example_binary": "example_binary",
                "rust_sample": "librust_sample.a",
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
                "rust_sample": "librust_sample.a",
            },
            "rust-sample-lib": {
                "rust-sample-lib": "librust_sample_lib.a",
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
        "pre_build": [pre_function],
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
    elif args.command == "lipo":
        exec_lipo(args)
    elif args.command == "xcframework":
        headers = {
            Path("rust_sample/module.modulemap"): PROJECT_CONFIG.get_root_dir()
            / "ffi/module.modulemap",
            Path("rust_sample/rust_sample.h"): PROJECT_CONFIG.get_root_dir()
            / "ffi/rust_sample.h",
        }
        dbu.create_xcframework(
            PROJECT_CONFIG, args.debug, "RustSample", headers, "librust_sample.a"
        )
    elif args.command == "aar":
        abu.generate_aar(PROJECT_CONFIG, args)
    elif args.command == "build-ios-simulator-stubs":
        dbu.build_stub_ios_simulator_libraries(
            PROJECT_CONFIG,
            args.debug,
            args.header or PROJECT_CONFIG.get_root_dir() / "ffi/rust_sample.h",
            "librust_sample.a",
        )
    elif args.command == "build-tvos-simulator-stubs":
        dbu.build_stub_tvos_simulator_libraries(
            PROJECT_CONFIG,
            args.debug,
            args.header or PROJECT_CONFIG.get_root_dir() / "ffi/rust_sample.h",
            "librust_sample.a",
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
