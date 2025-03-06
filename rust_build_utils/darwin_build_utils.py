from contextlib import contextmanager
from pathlib import Path
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG
from typing import Optional, List, Dict, Iterator
import json
import os
import re
import rust_build_utils.rust_utils as rutils
import shutil
import subprocess


def get_universal_library_distribution_directory(
    project: rutils.Project, target_os: str, debug: bool
) -> Path:
    return (
        Path(project.get_darwin_distribution_dir())
        / target_os
        / ("debug" if debug else "release")
    )


def get_xcframework_path(
    project: rutils.Project, debug: bool, framework_name: str
) -> Path:
    if debug:
        framework_name += "-Debug"

    return Path(project.get_darwin_distribution_dir()) / f"{framework_name}.xcframework"


def _get_load_command_version(
    command_source: str, load_command: str, version_key: str
) -> Optional[str]:
    # Check if this is the right load command
    if f"cmd {load_command}" not in command_source:
        return None

    # Extract the appropriate version property
    if match := re.search(rf"{version_key} (\d+\.\d+)", command_source):
        return match.group(1)
    else:
        assert False, f"'{version_key}' not found in load command '{load_command}'"


def _assert_load_commands(load_commands: str, deployment_assert) -> None:
    load_command = deployment_assert[0]
    version_key = deployment_assert[1]
    minimum_os = deployment_assert[2]

    # Matches each Load command until the beginning of the next load command or \Z (EOF).
    # re.DOTALL instructs `re` to match newlines for `.`.
    load_command_regex = re.compile(
        r"Load command \d+.*?(?=Load command \d+|\Z)", re.DOTALL
    )

    found_minos_version = False

    for command_source in re.findall(load_command_regex, load_commands):
        version = _get_load_command_version(command_source, load_command, version_key)
        if version:
            assert (
                version == minimum_os
            ), f"incorrect {version_key}: {version}, expected {minimum_os}"
            found_minos_version = True

    assert (
        found_minos_version
    ), f"minimum version load command not found ({load_command}, {version_key})"


def assert_version(
    project: rutils.Project,
    config: rutils.CargoConfig,
    packages: rutils.PackageList,
) -> None:
    for _, bins in packages.items():
        for _, binary in bins.items():
            binary_path = project.get_cargo_path(
                config.rust_target, binary, config.debug
            )
            load_commands = rutils.run_command_with_output(
                ["otool", "-l", binary_path], hide_output=True
            )
            deployment_assert = GLOBAL_CONFIG[config.target_os]["archs"][config.arch][
                "deployment_assert"
            ]
            _assert_load_commands(load_commands, deployment_assert)


def lipo(
    project: rutils.Project,
    debug,
    target_os,
    packages: rutils.PackageList,
):
    archs = GLOBAL_CONFIG[target_os]["archs"]
    universal_binary_dist_path = get_universal_library_distribution_directory(
        project, target_os, debug
    )

    for _, bins in packages.items():
        for _, binary in bins.items():
            create_fat_binary(
                project,
                universal_binary_dist_path / binary,
                target_os,
                archs.keys(),
                binary,
                debug,
            )

    for arch in archs:
        dist_path = project.get_distribution_path(target_os, arch, "", debug)

        for _, bins in packages.items():
            for _, binary in bins.items():
                dsym_dir = f"{dist_path}/{binary}.dSYM"
                if os.path.isdir(dsym_dir):
                    dst_dir = f"{universal_binary_dist_path}/{binary}.dSYM/{arch}"
                    os.makedirs(dst_dir, exist_ok=True)
                    shutil.copytree(dsym_dir, dst_dir, dirs_exist_ok=True)

        shutil.rmtree(dist_path)


def create_fat_binary(
    project: rutils.Project,
    output: Path,
    target_os,
    architectures,
    cargo_artifact,
    debug,
) -> None:
    if not os.path.isdir(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    command = ["lipo", "-create"]
    for architecture in architectures:
        command.append(
            project.get_distribution_path(
                target_os, architecture, cargo_artifact, debug
            )
        )

    command.extend(["-output", str(output)])

    rutils.run_command(command)

def _framework_info_plist(framework_name: str, min_os_version: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>{framework_name}</string>
  <key>CFBundleIdentifier</key>
  <string>com.nordsec.llt.lib.{framework_name}</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundlePackageType</key>
  <string>FMWK</string>
  <key>CFBundleSignature</key>
  <string>????</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>MinimumOSVersion</key>
  <string>{min_os_version}</string>
</dict>
</plist>
"""


def _framework_modulemap(framework_name: str) -> str:
    return f"""framework module {framework_name} {{
	umbrella "."
	export *
}}
"""


@contextmanager
def _temp_framework_directory(
    project: rutils.Project, framework_name: str, headers_directory: Dict[Path, Path]
) -> Iterator[Path]:
    framework_dir = Path(project.get_distribution_dir()) / f"{framework_name}.framework"
    if framework_dir.exists():
        shutil.rmtree(framework_dir)

    framework_dir.mkdir(parents=True)

    framework_headers_dir = framework_dir / "Headers"
    framework_modules_dir = framework_dir / "Modules"
    framework_headers_dir.mkdir()
    framework_modules_dir.mkdir()

    for key, value in headers_directory.items():
        destination = framework_headers_dir / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(value, destination)

    with open(framework_modules_dir / "module.modulemap", "w") as modulemap:
        modulemap.write(_framework_modulemap(framework_name))

    try:
        yield framework_dir
    finally:
        shutil.rmtree(framework_dir)


def _min_os_version_for_arch(filename: str, arch: str) -> str:
    output = subprocess.check_output(
        [
            "vtool",
            "-arch",
            arch,
            "-show-build",
            filename
        ]
    ).decode("utf-8")

    # This is pretty nasty extraction of the vtool output, but it does crash
    # nicely with unexpected changes in format.
    # Originally tested against macOS 14.7.4 (23H420)

    lines = output.split("\n")
    properties = dict()
    for line in lines[2:-1]:
        key, value = line.split()
        properties[key] = value

    platform_version_min = [
        "LC_VERSION_MIN_MACOSX",
        "LC_VERSION_MIN_IPHONEOS",
        "LC_VERSION_MIN_TVOS"
    ]

    if properties["cmd"] in platform_version_min:
        return properties["version"]
    elif properties["cmd"] == "LC_BUILD_VERSION":
        return properties["minos"]
    else:
        raise Exception("Unable to extract minimum OS version")


def _min_os_version(filename: str) -> str:
    archs = subprocess.check_output(["lipo", filename, "-archs"]).split()

    arch_min_os_versions = []

    for arch in archs:
        arch = arch.decode("utf-8")

        arch_min_os_version = _min_os_version_for_arch(filename, arch)
        arch_min_os_version_components = tuple(map(int, arch_min_os_version.split(".")))
        arch_min_os_versions.append(arch_min_os_version_components)

    # Pick lowest version of any arch
    min_os_version_components = map(str, min(arch_min_os_versions))
    min_os_version = ".".join(min_os_version_components)

    return min_os_version


def create_xcframework(
    project: rutils.Project,
    debug: bool,
    framework_name: str,
    swift_module_name: str,
    headers_directory: Dict[Path, Path],
    library_file_name: str,
    target_os_list: List[str] = rutils.XCFRAMEWORK_TARGET_OSES,
) -> None:
    xcframework_path = get_xcframework_path(project, debug, framework_name)
    if xcframework_path.exists():
        shutil.rmtree(xcframework_path)

    with _temp_framework_directory(
        project, swift_module_name, headers_directory
    ) as temp_framework:
        command = ["xcodebuild", "-create-xcframework"]

        for target_os in target_os_list:
            lib_path = str(
                get_universal_library_distribution_directory(project, target_os, debug)
                / library_file_name
            )

            # fix @rpath to relative one since the absolute is embedded at this point
            subprocess.run(
                [
                    "install_name_tool",
                    "-id",
                    f"@rpath/{swift_module_name}.framework/{swift_module_name}",
                    lib_path,
                ],
                check=True,
            )

            framework_path = (
                get_universal_library_distribution_directory(project, target_os, debug)
                / f"{swift_module_name}.framework"
            )

            if framework_path.exists():
                shutil.rmtree(framework_path)
            shutil.copytree(temp_framework, framework_path, symlinks=True)
            shutil.copyfile(
                lib_path, framework_path / swift_module_name, follow_symlinks=False
            )
            with open(framework_path / "Info.plist", "w") as info_plist:
                info_plist.write(
                    _framework_info_plist(
                        framework_name,
                        _min_os_version(framework_path / swift_module_name)
                    )
                )

            command.extend(["-framework", str(framework_path)])

        command.extend(["-output", str(xcframework_path)])

        rutils.run_command(command)


def get_sdk_path(target_os: str) -> Path:
    sdk = {
        "ios": "iphoneos",
        "ios-sim": "iphonesimulator",
        "macos": "macosx",
        "tvos": "appletvos",
        "tvos-sim": "appletvsimulator",
    }.get(target_os)
    assert sdk, f"unsupported target_os '{target_os}'"
    sdk_path = (
        subprocess.check_output(["xcrun", "--sdk", sdk, "--show-sdk-path"])
        .decode("utf-8")
        .strip()
    )
    return Path(sdk_path)


def set_sdk(config) -> None:
    os.environ["SDKROOT"] = str(get_sdk_path(config.target_os))
    # SDKROOT is set to macos SDKROOT by default, when running ios builds it may fail because of clang
    # targeting macos SDKROOT when compiling ios


def generate_stub_library(header_path: Path) -> str:
    # Dump header file AST
    ast = rutils.run_command_with_output(
        ["clang", "-Xclang", "-ast-dump=json", str(header_path)],
        hide_output=True,
    )
    ast_json = json.loads(ast)

    # Filter out function declarations and extract function names. Discard any
    # function declarations that were included from other files (stdlib.h, etc..).
    function_names: List[str] = [
        cursor["name"]
        for cursor in ast_json["inner"]
        if cursor["kind"] == "FunctionDecl" and not cursor["loc"].get("includedFrom")
    ]

    # Generate stubbed functions that segfault in a predictable way when called
    functions_source = [
        f"""void {function_name}() {{
    printf("FATAL: {function_name}() - attempt to call stubbed IOS simulator function\\n");
    *(volatile int*)0=0;
}}"""
        for function_name in function_names
    ]

    heading = """// THIS FILE IS AUTOMATICALLY GENERATED BY `ci-helper-scripts/rust_build_utils/darwin_build_utils.py`
#include <stdio.h>
"""

    return heading + "\n".join(functions_source)


def _build_shared_stub_library(
    project: rutils.Project, os: str, target_string: str, stub_path: Path, output: Path
) -> None:
    def get_temp_arch_path(arc: str) -> Path:
        return project.get_build_dir() / f"{os}-simulator-stub-{arch}.dylib"

    sdk_path = get_sdk_path(f"{os}-sim")
    arches = ["arm64", "x86_64"]
    for arch in arches:
        rutils.run_command(
            [
                "clang",
                "-shared",
                "-fpic",
                "-x",
                "c",
                "-target",
                f"{arch}" + target_string,
                "-isysroot",
                str(sdk_path),
                str(stub_path),
                "-o",
                str(get_temp_arch_path(arch)),
            ]
        )

    lipo_command: List[str] = ["lipo", "-create"]
    for arch in arches:
        lipo_command.extend([str(get_temp_arch_path(arch))])
    lipo_command.extend(["-output", str(output)])
    rutils.run_command(lipo_command)


def _build_static_stub_library(
    project: rutils.Project, os: str, target_string: str, stub_path: Path, output: Path
) -> None:
    def get_object_path(arc: str) -> Path:
        return project.get_build_dir() / f"{os}-simulator-stub-{arch}.o"

    sdk_path = get_sdk_path(f"{os}-sim")
    arches = ["arm64", "x86_64"]
    for arch in arches:
        rutils.run_command(
            [
                "clang",
                "-x",
                "c",
                "-target",
                f"{arch}" + target_string,
                "-isysroot",
                str(sdk_path),
                "-c",
                str(stub_path),
                "-o",
                str(get_object_path(arch)),
            ]
        )

    libtool_command: List[str] = ["libtool"]
    for arch in arches:
        libtool_command.extend(["-static", str(get_object_path(arch))])
    libtool_command.extend(["-o", str(output)])
    rutils.run_command(libtool_command)


def build_stub_library(
    project: rutils.Project, os: str, stub_path: Path, output: Path
) -> None:
    if os == "ios":
        target_string = "-apple-ios11.0-simulator"
    elif os == "tvos":
        target_string = "-apple-tvos17.0-simulator"
    else:
        raise ValueError(f"Unsupported OS variable: {os}")

    if output.suffix == ".dylib":
        _build_shared_stub_library(project, os, target_string, stub_path, output)
    elif output.suffix == ".a":
        _build_static_stub_library(project, os, target_string, stub_path, output)
    else:
        raise ValueError(f"Unsupported output file type: {output.suffix}")


def build_stub_ios_simulator_libraries(
    project: rutils.Project,
    debug: bool,
    header_path: Path,
    library_file_name: str,
) -> None:
    build_stub_simulator_libraries(
        project,
        "ios",
        debug,
        header_path,
        library_file_name,
    )


def build_stub_tvos_simulator_libraries(
    project: rutils.Project,
    debug: bool,
    header_path: Path,
    library_file_name: str,
) -> None:
    build_stub_simulator_libraries(
        project,
        "tvos",
        debug,
        header_path,
        library_file_name,
    )


def build_stub_simulator_libraries(
    project: rutils.Project,
    os: str,
    debug: bool,
    header_path: Path,
    library_file_name: str,
) -> None:
    stub_source = generate_stub_library(header_path)
    stub_path = project.get_build_dir() / f"{os}-simulator-stub-library.c"
    with open(stub_path, "w") as file:
        file.write(stub_source)

    output_path = (
        get_universal_library_distribution_directory(project, f"{os}-sim", debug)
        / library_file_name
    )
    output_path.resolve().parent.mkdir(parents=True, exist_ok=True)
    build_stub_library(project, os, stub_path, output_path)
