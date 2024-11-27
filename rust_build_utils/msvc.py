import os
import re
import subprocess
from pathlib import Path
from typing import Optional

EDITION_PREFERENCES = [
    "BuildTools",
    "Enterprise",
    "Professional",
    "Community",
    "Preview",
]
MSV_PATHS = [
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio"),
    Path(r"C:\Program Files\Microsoft Visual Studio"),
]


def is_msvc_active() -> bool:
    return "VisualStudioVersion" in os.environ


def is_msv_version(path: Path):
    """Check if a given path is a MVS version installation.
    An installation should contain subdirectories of MSV editions
    """
    if not path.is_dir():
        return False
    for subdir in path.iterdir():
        if subdir.name in EDITION_PREFERENCES:
            return True
    return False


def msv_versions():
    for installation_path in MSV_PATHS:
        for version in installation_path.iterdir():
            if is_msv_version(version):
                yield version


def activate_msvc(
    arch: str,
    version_preference: Optional[str] = None,
    edition_preference: Optional[str] = None,
    direct_pass_arch: bool = False,
) -> dict[str, Optional[str]]:
    """Activate MSVC tools for building a specific arch

    Arguments:
    arch: build output (target) architecture. The arch will be appended to 'amd64_'
      (because our hosts are x64; if x64 or amd64 is given it will be passed directly) and passed to vcvarsall.bat.
      aarch64 will be converted to arm64
      For example:
        amd64   -> vcvarsall.bat amd64
        x64     -> vcvarsall.bat x64
        x86     -> vcvarsall.bat amd64_x86
        arm     -> vcvarsall.bat amd64_arm
        arm64   -> vcvarsall.bat amd64_arm64
        aarch64 -> vcvarsall.bat amd64_arm64
      https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170#vcvarsall-syntax
    version_preference (optional): version (year) preference (for example: "2022").
      When requested version is not found an exception will be raised. If not given, a highest version will be used.
      Folders in 'C:\Program Files (x86)\Microsoft Visual Studio' and 'C:\Program Files\Microsoft Visual Studio' can be used as versions.
    version_preference (optional): edition preference. There can be multiple editions of VS installed at the time.
      If requested edition is not found in automatically (or explicitly) chosen version,
      an exception will be raised. Example values are Community, Professional, Enterprise, BuildTools, Preview.
      If not given, a preference is given (in same order): BuildTools, Enterprise, Professional, Community, Preview.
      If none of these is found, edition will be picked at random.
      The editions are folders in 'C:\Program Files\Microsoft Visual Studio\<version>'.
    direct_pass_arch (optional): if True, the `arch` value will be passed to vcvarsall.bat
      without appending the 'amd64_' prefix.

    Returns:
    envrinmental variables and their original values that were modified by vcvarsall.bat script

    Example usage:
    orig_env = activate_msvc('arm64')
    print(subprocess.run("link"))
    print(subprocess.run("cl"))
    deactivate_msvc(orig_env)
    """

    # Sample location of vcvarsall script:
    # "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
    # We begin by finding microsoft visual studio installation.
    if not any(p.is_dir() for p in MSV_PATHS):
        raise Exception(
            "Microsoft Visual Studio might not be installed. Was looking in '{}'".format(
                MSV_PATHS
            )
        )

    # Multiple versions and multiple editions might be installed, so we iterate over versions installed.
    # If version preference is given, we filter only matching versions, othervise the highest version is picked.
    sorted_versions = sorted(
        [
            v
            for v in msv_versions()
            # version should match the preference if given
            if (version_preference is None or v.name == version_preference)
        ],
        key=lambda p: p.name,
        reverse=True,
    )
    if len(sorted_versions) == 0:
        raise Exception(
            "Microsoft Visual Studio version not found. Was looking in '{}'".format(
                MSV_PATHS
            )
        )
    msv_version = sorted_versions[0]

    # There can be multiple editions of visual studio installed, but we're choosing based on a preference list.
    # To pick the edition based on preference list, we create a function that returns an index in the list.
    # When used as a sort key, the first element will be the closes to the start of the list
    # To support values not in a list, the length of the list is used as fallback,
    # putting those values effectively at the end.
    def preference_index(e):
        if e in EDITION_PREFERENCES:
            return EDITION_PREFERENCES.index(e)
        else:
            return len(EDITION_PREFERENCES)

    # if edition_preference is given, the list will only contain that edition.
    msv_editions = sorted(
        [
            e
            for e in msv_version.iterdir()
            if e.is_dir()
            and (edition_preference is None or e.name == edition_preference)
        ],
        key=lambda p: preference_index(p.name),
    )
    if len(msv_editions) == 0:
        raise Exception(
            "Microsoft Visual Studio edition not found. Was looking in '{}'".format(
                msv_version
            )
        )
    msv = msv_editions[0]
    vcvarsall = msv.joinpath(r"VC\Auxiliary\Build\vcvarsall.bat")

    # architecture string that will be passed to vcvarsall
    if not direct_pass_arch and arch == "aarch64":
        arch = "arm64"
    if not direct_pass_arch and arch == "i686":
        arch = "x86"
    arch = (
        arch
        if direct_pass_arch or arch in ("amd64", "x64")
        else "amd64_{}".format(arch)
    )

    original_env = {}
    # Execute vcvarsall in a shell and print the environment after modification.
    # Because the change happens in a separate process, after it exits the changes made to the env are lost.
    # We collect the process output (modified environment) and set current environment to those values.
    # When setting the environment we save the old values so they can be restored after exiting the context.
    #
    # `chcp 65001` changes output encoding to utf-8.
    # https://learn.microsoft.com/en-gb/windows/win32/intl/code-page-identifiers?redirectedfrom=MSDN
    p = subprocess.run(
        ["chcp", "65001", "&", str(vcvarsall), arch, "&", "set"],
        shell=True,
        check=True,
        capture_output=True,
    )
    # Find ARG=VALUE pairs and capture them. Because the value might contain '=',
    # we match until the first '=' character.
    for m in re.finditer(r"^([^=]*)=(.*)$", p.stdout.decode("utf-8"), flags=re.M):
        env_var = m.group(1)
        env_new_val = m.group(2).strip()
        env_old_val = os.environ.get(env_var, None)
        if env_old_val != env_new_val:
            original_env[env_var] = env_old_val
            os.environ[env_var] = env_new_val
    return original_env


def deactivate_msvc(env: dict[str, Optional[str]]):
    """Deactivate MSVC tools that were activated with `activate_msvc()`.
    Restores the environmental variables set by vcvarsall.bat script

    Arguments:
    env: original system environment, returned from `activate_msvc()` call
    """
    for k, v in env.items():
        if v is None:
            del os.environ[k]
        else:
            os.environ[k] = v
