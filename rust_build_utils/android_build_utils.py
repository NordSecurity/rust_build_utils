import os
import shutil
import subprocess
import rust_build_utils.rust_utils as rutils
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG, NDK_IMAGE_PATH
from string import Template
from typing import Optional

NDK_VERSION = "r26"
TOOLCHAIN = (
    f"{NDK_IMAGE_PATH}/android-ndk-{NDK_VERSION}/toolchains/llvm/prebuilt/linux-x86_64"
)


def strip_android(project: rutils.Project, config: rutils.CargoConfig, packages=None):
    strip_dir = project.get_distribution_path(
        config.target_os, config.arch, f"../stripped/", config.debug
    )
    unstrip_dir = project.get_distribution_path(
        config.target_os, config.arch, f"../unstripped/", config.debug
    )
    if not os.path.exists(strip_dir):
        os.makedirs(strip_dir)
    if not os.path.exists(unstrip_dir):
        os.makedirs(unstrip_dir)

    arch_dir = project.get_distribution_path(
        config.target_os, config.arch, "", config.debug
    )
    renamed_arch = GLOBAL_CONFIG[config.target_os]["archs"][config.arch]["dist"]
    shutil.copytree(
        arch_dir,
        f"{unstrip_dir}/{renamed_arch}",
    )
    shutil.copytree(
        arch_dir,
        f"{strip_dir}/{renamed_arch}",
    )

    shutil.rmtree(arch_dir)
    strip = f"{TOOLCHAIN}/bin/llvm-strip"

    for _, bins in packages.items():
        for _, bin in bins.items():
            rutils.run_command([strip, f"{strip_dir}/{renamed_arch}/{bin}"])


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
