from typing import Dict, Any

NDK_IMAGE_PATH = "/source/.build"
# This is the global configuration file that will be used for most Rust projects, only apply changes which are needed for all projects.

# Every single OS has this general structure:
# target_os : {
#   "archs" :       [Mandatory, Dictionary], dict of architectures to build for this OS
#       {
#        "{arch}" : [Mandatory, Dictionary], dict of arch specific variables
#           {
#            "rust_target" :        [Mandatory, String], name of the rust target that is used in cargo
#            "dist" :               [Mandatory Android only, String], name of the artifact folders for the Android team
#            "deployment_assert" :  [Mandatory macOS/iOS only, tuple of string and version number], is used to assert if the binary was build with the correct version
#            "env" :                [Optional, Dictionary], a dict of arch specific environment variables
#               {
#                   "{env_var}" :   [Tuple(List<String>, String)], values are tuples that contain a list of strings to set the variable to and another String which tells
#                                   whether the environment variable should be set to blank first("set") or kept as is and concatenated on top ("append")
#               }
#           }
#       }
#   "env" :         [Optional, Dictionary], a dict of OS specific environment variables, follows the same structure as arch specific variables, see above.
#   "pre_build" :   [Optional, List<String>], list of functions to call before the build begins (this is called after the LOCAL pre_build). Functions are written as "full_package_name.subpackage_name.function_name"
#   "post_build" :  [Optional, List<String>], list of functions to call after the build begins (this is called before the LOCAL post_build). Functions are written as "full_package_name.subpackage_name.function_name"
# }

GLOBAL_CONFIG: Dict[str, Any] = {
    "android": {
        "archs": {
            "x86_64": {
                "rust_target": "x86_64-linux-android",
                "dist": "x86_64",
            },
            "aarch64": {"rust_target": "aarch64-linux-android", "dist": "arm64-v8a"},
            "i686": {
                "rust_target": "i686-linux-android",
                "dist": "x86",
            },
            "armv7": {
                "rust_target": "armv7-linux-androideabi",
                "dist": "armeabi-v7a",
            },
        },
        "env": {"PATH": (f":{NDK_IMAGE_PATH}", "append")},
        "post_build": ["rust_build_utils.android_build_utils.strip_android"],
    },
    "linux": {
        "archs": {
            "x86_64": {
                "rust_target": "x86_64-unknown-linux-gnu",
            },
            "aarch64": {
                "rust_target": "aarch64-unknown-linux-gnu",
            },
            "i686": {
                "rust_target": "i686-unknown-linux-gnu",
            },
            "armv7": {
                "rust_target": "armv7-unknown-linux-gnueabihf",
            },
            "armv5": {
                "rust_target": "arm-unknown-linux-gnueabi",
            },
        },
    },
    "windows": {
        "archs": {
            "x86_64": {
                "rust_target": "x86_64-pc-windows-gnu",
            },
            "aarch64": {
                "rust_target": "aarch64-pc-windows-msvc",
            },
        },
        "env": {
            "RUSTFLAGS": ([" -C link-arg=-s "], "set"),
        },
    },
    "macos": {
        "archs": {
            "x86_64": {
                "rust_target": "x86_64-apple-darwin",
                "deployment_assert": ("LC_VERSION_MIN_MACOSX", "version", "10.7"),
                "env": {
                    "MACOSX_DEPLOYMENT_TARGET": (["10.7"], "set"),
                },
            },
            "aarch64": {
                "rust_target": "aarch64-apple-darwin",
                "deployment_assert": ("LC_BUILD_VERSION", "minos", "11.0"),
                "env": {
                    "MACOSX_DEPLOYMENT_TARGET": (["11.0"], "set"),
                },
            },
        },
        "env": {
            "RUSTFLAGS": ([" -C link-arg=-s -C embed-bitcode "], "set"),
        },
        "post_build": ["rust_build_utils.darwin_build_utils.assert_version"],
    },
    "ios": {
        "archs": {
            "aarch64": {
                "rust_target": "aarch64-apple-ios",
                "deployment_assert": ("LC_VERSION_MIN_IPHONEOS", "version", "7.0"),
                "env": {
                    "IPHONEOS_DEPLOYMENT_TARGET": (["7.0"], "set"),
                },
            },
        },
        "env": {
            "RUSTFLAGS": ([" -C link-arg=-s -C embed-bitcode "], "set"),
        },
        "pre_build": ["rust_build_utils.darwin_build_utils.set_sdk"],
        "post_build": ["rust_build_utils.darwin_build_utils.assert_version"],
    },
    "tvos": {
        "archs": {
            "aarch64": {
                "rust_target": "aarch64-apple-tvos",
                "deployment_assert": ("LC_VERSION_MIN_TVOS", "version", "10.0"),
                "env": {
                    "TVOS_DEPLOYMENT_TARGET": (["10.0"], "set"),
                },
            },
        },
        "env": {
            "RUSTFLAGS": ([" -C link-arg=-s -C embed-bitcode "], "set"),
        },
        "pre_build": ["rust_build_utils.darwin_build_utils.set_sdk"],
        "post_build": ["rust_build_utils.darwin_build_utils.assert_version"],
    },
    "tvos-sim": {
        "archs": {
            "x86_64": {
                "rust_target": "x86_64-apple-tvos",
                "deployment_assert": ("LC_VERSION_MIN_TVOS", "version", "10.0"),
                "env": {
                    "TVOS_DEPLOYMENT_TARGET": (["10.0"], "set"),
                },
            },
        },
        "env": {
            "RUSTFLAGS": ([" -C link-arg=-s -C embed-bitcode "], "set"),
        },
        "pre_build": ["rust_build_utils.darwin_build_utils.set_sdk"],
        "post_build": ["rust_build_utils.darwin_build_utils.assert_version"],
    },
}
