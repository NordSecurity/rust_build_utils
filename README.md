# Rust build

## Overview
This is Nord Security's internal project. It contains utilities used for building libraries developed in Rust.

## Changelist
See CHANGELOG.md for changes

## Building docker images

### Debug images
With every push to the repository a new debug image is built and pushed to the GitHub Container Registry.
This debug image is tagged: debug-{commit hash}.

### Release images
It is recommended to use GitHub UI to build release versions of docker images. This way there is
a guarantee that the image is built from the versioned Dockerfile and does not contain
any local changes. Additionally the image is labeled with the revision of the project during CI build
so it is easy to trace back the source Dockerfile used to build the image.
Please release images only from the `main` branch.

To build a docker image on GitHub UI:
1. Go to the [Actions](https://github.com/NordSecurity/rust_build_utils/actions) page of the project.
2. Select the [Build and Push Docker Image](https://github.com/NordSecurity/rust_build_utils/actions/workflows/docker.yml) workflow on the left.
3. Click the `Run workflow` button.
4. Select `main` branch, set docker image name and tag and click the `Run workflow` button.
5. For builder images you must also specify Rust version this images is based on before running the workflow. It is used for naming the image.

## Contributions

We do not expect external contributions to this project.

## License

[This project is licensed under the terms of the GNU General Public License v3.0 only](LICENSE)
