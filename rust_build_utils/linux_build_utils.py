from os import path
import rust_build_utils.rust_utils as rutils
from rust_build_utils.rust_utils_config import GLOBAL_CONFIG


def strip(project: rutils.Project, config: rutils.CargoConfig, packages=None):
    if config.target_os != "linux" or config.debug or packages == None:
        return

    strip_bin = GLOBAL_CONFIG["linux"]["archs"][config.arch]["strip_path"]
    if not path.isfile(strip_bin):
        # fallback to default strip
        strip_bin = "objcopy"

    dist_dir = project.get_distribution_path(
        config.target_os, config.arch, "", config.debug
    )

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
        strip_cmd = [f"{strip_bin}", "--strip-all", f"{bin_path}"]
        rutils.run_command(strip_cmd)

    for _, bins in packages.items():
        for _, bin in bins.items():
            bin_path = f"{dist_dir}/{bin}"
            _create_debug_symbols(bin_path)
            _strip_debug_symbols(bin_path)
