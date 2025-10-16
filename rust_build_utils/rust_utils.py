import argparse
import hashlib
import subprocess
import os
import shutil
import importlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG
from pathlib import Path
from rust_build_utils.msvc import activate_msvc, deactivate_msvc, is_msvc_active


PackageList = Dict[str, Dict[str, str]]

LIPO_TARGET_OSES = ["macos", "ios", "ios-sim", "tvos", "tvos-sim"]
XCFRAMEWORK_TARGET_OSES = ["macos", "ios", "ios-sim", "tvos", "tvos-sim"]

RUST_NIGHTLY_VERSION = "2025-06-20"  # 1.89.0 was branched on this day, see top of https://releases.rs/docs/1.89.0/


@dataclass
class CargoConfig:
    """Arch 'arm64' (eg. the macos arch on arm) will be replaced with 'aarch64'."""

    target_os: str
    arch: str
    debug: bool
    rust_target: str = ""

    def __post_init__(self):
        if self.arch == "arm64":
            self.arch = "aarch64"
        if not self.rust_target:
            self.rust_target = GLOBAL_CONFIG[self.target_os]["archs"][self.arch][
                "rust_target"
            ]

    def is_msvc(self):
        return self.rust_target.endswith("-msvc")


@dataclass
class Project:
    rust_version: str
    root_dir: str
    working_dir: Optional[str]

    def __post_init__(self):
        # TODO: `working_dir` is used by libtelio and it should probably be an
        # implicit function called by libtelio
        if self.working_dir:
            os.chdir(self.working_dir)
        else:
            os.chdir(self.root_dir)

    def get_root_dir(self) -> Path:
        return Path(self.root_dir)

    def get_build_dir(self) -> Path:
        build_dir = Path(self.root_dir) / ".build"
        build_dir.resolve().mkdir(exist_ok=True)
        return build_dir

    def get_cargo_target_dir(self) -> str:
        if self.working_dir:
            return os.path.normpath(self.working_dir + "/target/")
        else:
            return os.path.normpath(self.root_dir + "/target/")

    def get_bindings_dir(self) -> str:
        return os.path.normpath(self.get_distribution_dir() + "/bindings/")

    def get_distribution_dir(self) -> str:
        return os.path.normpath(self.root_dir + "/dist/")

    def get_cargo_path(self, target: str, path: str, debug: bool) -> str:
        cargo_dir = self.get_cargo_target_dir()
        if debug:
            return os.path.normpath(f"{cargo_dir}/{target}/debug/{path}")
        return os.path.normpath(f"{cargo_dir}/{target}/release/{path}")

    def get_distribution_path(
        self, target_os: str, architecture: str, path: str, debug: bool
    ) -> str:
        if target_os in {"macos", "ios", "ios-sim", "tvos", "tvos-sim"}:
            dist_dir = self.get_darwin_distribution_dir()
        else:
            dist_dir = self.get_distribution_dir()

        if debug:
            return os.path.normpath(
                f"{dist_dir}/{target_os}/debug/{architecture}/{path}"
            )
        else:
            return os.path.normpath(
                f"{dist_dir}/{target_os}/release/{architecture}/{path}"
            )

    def get_darwin_distribution_dir(self) -> str:
        return f"{self.get_distribution_dir()}/darwin"


def concatenate_env_variable(env_var: str, value_array):
    for value in value_array:
        os.environ[env_var] += value


def clear_env_variables(config):
    if "env" in GLOBAL_CONFIG[config.target_os]:
        for key, value in GLOBAL_CONFIG[config.target_os]["env"].items():
            if value[1] == "set":
                os.environ[key] = ""
    if "env" in GLOBAL_CONFIG[config.target_os]["archs"].get(config.arch, {}):
        for key, value in GLOBAL_CONFIG[config.target_os]["archs"][config.arch][
            "env"
        ].items():
            if value[1] == "set":
                os.environ[key] = ""


def set_env_var(config):
    clear_env_variables(config)
    if "env" in GLOBAL_CONFIG[config.target_os]:
        for key, value in GLOBAL_CONFIG[config.target_os]["env"].items():
            concatenate_env_variable(key, value[0])
    if "env" in GLOBAL_CONFIG[config.target_os]["archs"].get(config.arch, {}):
        for key, value in GLOBAL_CONFIG[config.target_os]["archs"][config.arch][
            "env"
        ].items():
            concatenate_env_variable(key, value[0])


def config_local_env_vars(config, local_config):
    clear_env_variables(config)
    if "env" in local_config[config.target_os]:
        for env, tuple in local_config[config.target_os]["env"].items():
            if not "env" in GLOBAL_CONFIG[config.target_os]:
                GLOBAL_CONFIG[config.target_os]["env"] = {env: tuple}
            if env in GLOBAL_CONFIG[config.target_os]["env"] and tuple[1] == "append":
                if tuple[0] not in GLOBAL_CONFIG[config.target_os]["env"][env][0]:
                    GLOBAL_CONFIG[config.target_os]["env"][env][0].append(tuple[0])
            else:
                GLOBAL_CONFIG[config.target_os]["env"][env] = tuple

    if (
        "archs" in local_config[config.target_os]
        and config.arch in local_config[config.target_os]["archs"]
    ):
        if "env" in local_config[config.target_os]["archs"][config.arch]:
            for env, tuple in local_config[config.target_os]["archs"][config.arch][
                "env"
            ].items():
                if not "env" in GLOBAL_CONFIG[config.target_os]["archs"][config.arch]:
                    GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["env"] = {
                        env: tuple
                    }
                    return
                if (
                    env in GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["env"]
                    and tuple[1] == "append"
                ):
                    if (
                        tuple[0]
                        not in GLOBAL_CONFIG[config.target_os]["archs"][config.arch][
                            "env"
                        ][env][0]
                    ):
                        GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["env"][
                            env
                        ][0].append(tuple[0])
                else:
                    GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["env"][
                        env
                    ] = tuple


def check_config(config):
    if config.arch not in GLOBAL_CONFIG[config.target_os]["archs"]:
        raise Exception(
            f"invalid arch '{config.arch}' for '{config.target_os}', expected {str(list(GLOBAL_CONFIG[config.target_os]['archs'].keys()))}"
        )


def create_cli_parser() -> Any:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    build_parser = subparsers.add_parser("build", help="build a specific os/arch pair")
    build_parser.add_argument("os", type=str, choices=list(GLOBAL_CONFIG.keys()))
    build_parser.add_argument("arch", type=str)
    build_parser.add_argument("--target", type=str)
    build_parser.add_argument("--debug", action="store_true", help="Create debug build")

    subparsers.add_parser("bindings", help="generate uniffi bindings")

    lipo_parser = subparsers.add_parser(
        "lipo",
        help="create fat multiarchitecture binaries using lipo, and assembly dist/darwin/lib(name)",
    )
    lipo_parser.add_argument("--debug", action="store_true", help="lipo debug build")
    lipo_parser.add_argument(
        "--build",
        action="store_true",
        help="builds all needed archs before executing lipo",
    )

    fetch_artifacts_parser = subparsers.add_parser(
        "fetch-artifacts", help="Download artifacts from pipeline"
    )
    fetch_artifacts_parser.add_argument("--job-name", type=str, required=True)

    xc_parser = subparsers.add_parser(
        "xcframework",
        help="Create .xcframework that includes available platforms and architectures",
    )
    xc_parser.add_argument(
        "--debug", action="store_true", help="Create .xcframework using debug binaries"
    )

    aar_parser = subparsers.add_parser(
        "aar",
        help="Create aar package that includes available platforms and architectures",
    )
    aar_parser.add_argument("project_name", type=str, help="Name of the project")
    aar_parser.add_argument(
        "package_name",
        type=str,
        help="Package name in the bindings eg. 'com.nordsec.telio'",
    )
    aar_parser.add_argument("artifact_id", type=str, help="Artifact id on the server")
    aar_parser.add_argument(
        "version",
        type=str,
        help="Version for the AAR package. Might be e.g. commit hash",
    )
    aar_parser.add_argument(
        "binding_path", type=str, help="Path to the folder containing bindings"
    )
    aar_parser.add_argument(
        "lib_path",
        type=str,
        help="Path to dir containing all directories for each arch binary",
    )
    aar_parser.add_argument(
        "--settings_gradle_path",
        type=str,
        help="Path to settings.gradle to be used instead of the default one",
        required=False,
    )
    aar_parser.add_argument(
        "--build_gradle_path",
        type=str,
        help="Path to build.gradle template to be used instead of the default one",
        required=False,
    )
    aar_parser.add_argument(
        "--init_gradle_path",
        type=str,
        help="Path to init.gradle template to be used instead of the default one",
        required=False,
    )

    ios_sim_parser = subparsers.add_parser(
        "build-ios-simulator-stubs",
        help="""Build stub libraries for iOS simulator (aarch64 and x86_64) by reading
                list of function declarations from a header file""",
    )
    ios_sim_parser.add_argument(
        "--header",
        type=str,
        help="Path to header file from which to read function declarations",
    )
    ios_sim_parser.add_argument(
        "--debug",
        action="store_true",
        help="Output library stubs to debug dist location",
    )

    tvos_sim_parser = subparsers.add_parser(
        "build-tvos-simulator-stubs",
        help="""Build stub libraries for tvOS simulator (aarch64 and x86_64) by reading
                list of function declarations from a header file""",
    )
    tvos_sim_parser.add_argument(
        "--header",
        type=str,
        help="Path to header file from which to read function declarations",
    )
    tvos_sim_parser.add_argument(
        "--debug",
        action="store_true",
        help="Output library stubs to debug dist location",
    )

    return parser


def parse_cli():
    return create_cli_parser().parse_args()


def _build_packages(
    config, packages: List[str], extra_args: Optional[List[str]], subcommand: str
) -> None:
    if "tvos" in config.target_os or config.rust_target == "mipsel-unknown-linux-musl":
        args = [
            "cargo",
            f"+nightly-{RUST_NIGHTLY_VERSION}",
            "build",
            "--verbose",
            "-Z",
            "build-std",
            "--target",
            config.rust_target,
        ]
    else:
        args = [
            "cargo",
            subcommand,
            "--verbose",
            "--target",
            config.rust_target,
        ]

    if not config.debug:
        args.append("--release")

    for p in packages:
        args.append("--package")
        args.append(p)
    args.extend(extra_args or [])

    run_command(args)


def build(
    project: Project,
    config,
    packages: PackageList,
    extra_args: Optional[List[str]] = None,
) -> None:
    """
    Depricated: use `cargo_build` or `cargo_rustc` instead.

    Calls `cargo build` with given packages, passing extra_args to it.
    """
    cargo_build(project, config, packages, extra_args)


def cargo_rustc(
    project: Project,
    config,
    packages: PackageList,
    extra_args: Optional[List[str]] = None,
) -> None:
    """
    Calls `cargo rustc` with the given package, passing extra_args to it.
    """
    _cargo("rustc", project, config, packages, extra_args)


def cargo_build(
    project: Project,
    config,
    packages: PackageList,
    extra_args: Optional[List[str]] = None,
) -> None:
    """
    Calls `cargo build` with given packages, passing extra_args to it.
    """
    _cargo("build", project, config, packages, extra_args)


def _cargo(
    subcommand: str,
    project: Project,
    config,
    packages: PackageList,
    extra_args: Optional[List[str]],
) -> None:
    if not packages:
        raise ValueError("No packages specified")

    arch = (
        config.arch
        if config.target_os != "android"
        else GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["dist"]
    )

    pre_build(config)
    distribution_dir = project.get_distribution_path(
        config.target_os, arch, "", config.debug
    )

    if os.path.isdir(distribution_dir):
        shutil.rmtree(distribution_dir)
    os.makedirs(distribution_dir)

    if "tvos" in config.target_os or config.rust_target == "mipsel-unknown-linux-musl":
        run_command(
            ["rustup", "toolchain", "install", f"nightly-{RUST_NIGHTLY_VERSION}"]
        )
        run_command(
            [
                "rustup",
                "component",
                "add",
                "rust-src",
                "--toolchain",
                f"nightly-{RUST_NIGHTLY_VERSION}",
            ]
        )
    else:
        run_command(["rustup", "default", project.rust_version])
        run_command(["rustup", "target", "add", config.rust_target])
    run_command(["rustup", "component", "add", "rustfmt"])

    msvc_context = None
    if config.rust_target.endswith("-msvc") and not is_msvc_active():
        # For msvc based toolchains msvc development environment needs activation
        msvc_context = activate_msvc(arch)

    _build_packages(config, list(packages.keys()), extra_args, subcommand)

    any_changed = False
    for _, bins in packages.items():
        for _, bin in bins.items():
            cargo_bin_path = project.get_cargo_path(
                config.rust_target, bin, config.debug
            )
            cksum = compute_sha256(cargo_bin_path)
            cksum_path = f"{cargo_bin_path}.sha256"
            cksum_old = (
                (path.read_text().strip() or None)
                if (path := Path(cksum_path)).exists()
                else None
            )
            if cksum_old != cksum:
                print(
                    f"{cargo_bin_path} has changed, new checksum: {cksum} vs old: {cksum_old}"
                )
                any_changed = True
                with open(cksum_path, "w") as f:
                    f.write(cksum)
            # copies executable permissions
            shutil.copy2(cargo_bin_path, distribution_dir)

    if any_changed:
        post_build(project, config, packages)
    else:
        print("Skipping post build steps since none of the built binaries have changed")

    if msvc_context is not None:
        deactivate_msvc(msvc_context)


def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def str_to_func_call(func_string):
    func_array = func_string.split(".")
    func = func_array[-1]
    func_array.pop(-1)
    module = ".".join(func_array)

    return getattr(importlib.import_module(module), func)


def pre_build(config):
    set_env_var(config)
    if "pre_build" in GLOBAL_CONFIG[config.target_os]:
        pre_array = GLOBAL_CONFIG[config.target_os]["pre_build"]
        for function in pre_array:
            func_call = str_to_func_call(function)
            func_call(config)


def post_build(project: Project, config: CargoConfig, packages: PackageList) -> None:
    if "post_build" in GLOBAL_CONFIG[config.target_os]:
        post_array = GLOBAL_CONFIG[config.target_os]["post_build"]
        for function in post_array:
            func_call = str_to_func_call(function)
            func_call(project, config, packages)


def run_command(command):
    print("|EXECUTE| {}".format(" ".join(command)))
    subprocess.check_call(command)
    print("")


def run_command_with_output(command, hide_output=False):
    print("|EXECUTE| {}".format(" ".join(command)))
    result = subprocess.check_output(command).decode("utf-8")
    if hide_output:
        print("(OUTPUT HIDDEN)\n")
    else:
        print(result)
    return result


def copy_tree_or_file(src, dst):
    try:
        shutil.copytree(
            src,
            dst,
        )
    except NotADirectoryError:
        shutil.copyfile(
            src,
            dst,
        )


def remove_tree_or_file(path):
    try:
        shutil.rmtree(path)
    except NotADirectoryError:
        os.remove(path)


def generate_uniffi_bindings(
    project: Project,
    generator_version: str,
    languages: List[str],
    udl_path: str,
    dockerized: bool = True,
):
    """Generate uniFFI bindings using NordSecurity/uniffi-generators docker image.

    Args:
        project (Project): Project object
        generator_version (str): Version of the uniffi-generators docker image
        languages (List[str]): List of languages to generate bindings for (kotlin, swift, python, cs, go)
        udl_path (str): Path to the UDL file relative to the project root directory

    Note:
        I'm aware of "Docker SDK for Python" module. I've tried it but had potential issues on Windows and Mac
        so it seems that calling docker via subprocess is more reliable.
    """

    class UniffiContainer:
        def __init__(self, dockerized: bool = True):
            self.container_id = None
            self.dockerized = dockerized

        def __enter__(self):
            if not self.dockerized:
                return self

            run_args = [
                "docker",
                "run",
                "--rm",
                "-d",
                "-t",
                "-v",
                f"{project.get_root_dir()}:/workdir",
                "-w",
                "/workdir",
            ]
            if os.name == "posix":
                run_args.extend(["-u", f"{os.getuid()}:{os.getgid()}"])
            run_args.append(
                f"ghcr.io/nordsecurity/uniffi-generators:{generator_version}"
            )
            self.container_id = subprocess.check_output(run_args).decode().strip()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.container_id and self.dockerized:
                subprocess.check_output(["docker", "stop", self.container_id])

        def exec(self, cmd: List[str]):
            exec_args = (
                [
                    "docker",
                    "exec",
                    self.container_id,
                ]
                if self.dockerized
                else []
            )

            exec_args.extend(cmd)
            return subprocess.check_output(
                [str(item) for item in exec_args if item is not None]
            )

    try:
        with UniffiContainer(dockerized) as container:
            for language in languages:
                if language in ["kotlin", "swift", "python"]:
                    command = ["uniffi-bindgen", "generate", "--language", language]
                elif language in ["cs", "go", "cpp"]:
                    command = [f"uniffi-bindgen-{language}"]
                else:
                    raise ValueError(f"Unsupported language: {language}")
                output_path = os.path.relpath(
                    project.get_bindings_dir(), project.get_root_dir()
                )
                output_path = os.path.join(
                    output_path, (language if language != "cs" else "csharp")
                )
                command.extend(["-o", output_path, udl_path])
                container.exec(command)
    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed with output:\n\n{e.stdout.decode(errors='ignore')}")
        raise e
