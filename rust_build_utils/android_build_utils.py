import os
import shutil
import subprocess
import rust_build_utils.rust_utils as rutils
from rust_build_utils.rust_utils_config import (
    GLOBAL_CONFIG,
    NDK_IMAGE_PATH,
    NDK_VERSION,
)
from string import Template
from typing import Optional


TOOLCHAIN = (
    f"{NDK_IMAGE_PATH}/android-ndk-{NDK_VERSION}/toolchains/llvm/prebuilt/linux-x86_64"
)


def strip(project: rutils.Project, config: rutils.CargoConfig, packages=None):
    if config.target_os != "android" or config.debug or packages == None:
        return

    strip_bin = f"{TOOLCHAIN}/bin/llvm-objcopy"

    arch = GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["dist"]
    dist_dir = project.get_distribution_path(config.target_os, arch, "", config.debug)

    def _create_debug_symbols(bin_path: str):
        create_debug_symbols_cmd = [
            f"{strip_bin}",
            "--only-keep-debug",
            "--compress-debug-sections=zlib",
            f"{bin_path}",
            f"{bin_path}.debug",
        ]
        rutils.run_command(create_debug_symbols_cmd)

        set_read_only_cmd = ["chmod", "0444", f"{bin_path}.debug"]
        rutils.run_command(set_read_only_cmd)

    def _strip_debug_symbols(bin_path: str):
        strip_cmd = [
            f"{strip_bin}",
            "--strip-unneeded" if bin_path.endswith(".a") else "--strip-all",
            f"{bin_path}",
        ]
        rutils.run_command(strip_cmd)

    for _, bins in packages.items():
        for _, bin in bins.items():
            bin_path = f"{dist_dir}/{bin}"
            _create_debug_symbols(bin_path)
            _strip_debug_symbols(bin_path)


def _process_template(
    template_file: str, processed_file: str, substitution_data: dict[str, str]
):
    with open(template_file, "r") as f:
        filedata = Template(f.read())
        result = filedata.substitute(substitution_data)

    with open(processed_file, "w") as f:
        f.write(result)


def _generate_aar(
    project: rutils.Project,
    project_name: str,
    package_name: str,
    artifact_id: str,
    version: str,
    binding_path: str,
    lib_path: str,
    settings_gradle_path: Optional[str],
    build_gradle_path: Optional[str],
    init_gradle_path: Optional[str],
):
    if version.startswith("v"):
        version = version[len("v") :]
    script_dir = os.path.dirname(__file__)
    out_dir = os.path.join(project.root_dir, "android_aar")
    main_dir = os.path.join(out_dir, "main")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(main_dir, exist_ok=True)
    if settings_gradle_path:
        shutil.copyfile(settings_gradle_path, f"{out_dir}/settings.gradle")
    else:
        with open(f"{out_dir}/settings.gradle", "w") as f:
            f.write("include ':main'\n")
    if init_gradle_path:
        init_gradle_template = init_gradle_path
        init_gradle_processed = os.path.join(out_dir, "init.gradle")
        init_gradle_dict = {
            "PATH_TO_DEPENDENT_CRATE": os.path.join(project.root_dir, "Cargo.toml")
        }
        _process_template(init_gradle_template, init_gradle_processed, init_gradle_dict)

    gradle_dict = {
        "PACKAGE_NAME": package_name,
        "ARTIFACT_ID": artifact_id,
        "VERSION": version,
    }
    if build_gradle_path:
        gradle_template = build_gradle_path
    else:
        gradle_template = os.path.join(
            script_dir, "..", "aar_templates", "__build.gradle"
        )
    gradle_processed = os.path.join(main_dir, "build.gradle")
    print(f"Using gradle template: {gradle_template}")
    _process_template(gradle_template, gradle_processed, gradle_dict)

    internal_main_dir = os.path.join(main_dir, "src", "main")
    binding_type = binding_path.split("/")[-1]
    binding_src_dir = os.path.join(internal_main_dir, binding_type)
    jni_libs_dir = os.path.join(internal_main_dir, "jniLibs")
    os.makedirs(internal_main_dir, exist_ok=True)

    manifest_dict = {"PACKAGE_NAME": package_name}
    manifest_template = os.path.join(
        script_dir, "..", "aar_templates", "__AndroidManifest.xml"
    )
    manifest_processed = os.path.join(internal_main_dir, "AndroidManifest.xml")

    _process_template(manifest_template, manifest_processed, manifest_dict)

    shutil.copytree(binding_path, binding_src_dir, dirs_exist_ok=True)
    shutil.copytree(lib_path, jni_libs_dir, dirs_exist_ok=True)

    subprocess.check_call(
        ["gradle", "build", "-p", main_dir, "-Dorg.gradle.jvmargs=-Xmx1g"]
    )
    aar_output_path = os.path.join(
        main_dir, "build", "outputs", "aar", "main-release.aar"
    )
    dist_path = os.path.join(project.root_dir, "dist")
    os.makedirs(dist_path, exist_ok=True)
    aar_dest_path = os.path.join(dist_path, f"{project_name}.aar")
    shutil.copy2(aar_output_path, aar_dest_path)


def generate_aar(project: rutils.Project, args):
    _generate_aar(
        project,
        args.project_name,
        args.package_name,
        args.artifact_id,
        args.version,
        args.binding_path,
        args.lib_path,
        args.settings_gradle_path,
        args.build_gradle_path,
        args.init_gradle_path,
    )
