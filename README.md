# Rust build

## Overview
This is Nord Security's internal project. It contains utilities used for building libraries developed in Rust.

## Changelist
See CHANGELOG.md for changes

## Versioning
The Python library and the docker images share one version. Bump it according to [semver](https://semver.org).
A Rust toolchain bump is a minor change unless it breaks consumers.

Builder images are tagged `<rust version>-v<version>`, e.g. `ghcr.io/nordsecurity/build-linux-rust:1.99.1-v9.0.0`.
The Rust version is taken from `ARG RUST_VERSION` in the Dockerfile. Images without Rust are tagged `v<version>`.

Images released before 9.0.0 have the Rust version in the image name, e.g. `build-linux-rust1.99.1:v8.3.0`.

## Releasing
Every PR changing `rust_build_utils/`, `builders/` or `aar_templates/` must add a new version
on top of CHANGELOG.md. CI checks it, use the `skip-changelog` label to skip the check.

1. Make your changes. To bump Rust, update `ARG RUST_VERSION` in the builder Dockerfiles.
2. Add a new version with your changes on top of CHANGELOG.md:
   ```markdown
   ## 9.1.0
   - Add something
   ```
3. Push the branch and test your changes with the `debug-{commit hash}` images.
4. Merge the PR to `main`. All docker images are built and pushed, and the `v9.1.0` tag and GitHub Release are created.

Do not create `v<version>` tags manually, a tagged version is considered released.

### Debug images
With every push to a branch other than `main` debug images are built and tagged `debug-{commit hash}`.

## Contributions

We do not expect external contributions to this project.

## License

[This project is licensed under the terms of the GNU General Public License v3.0 only](LICENSE)
