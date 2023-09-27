import os
import shutil
import rust_build_utils.rust_utils as rutils
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG, NDK_IMAGE_PATH

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
