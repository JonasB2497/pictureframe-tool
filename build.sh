#!/usr/bin/env bash
# Build a .deb package from this project using fpm.
# fpm can target many formats, so switching to .rpm/.pacman/etc. later is trivial.

set -euo pipefail

# --- metadata (edit these to match your project) ---
NAME="pictureframe-tool"
VERSION="${VERSION:-1.0.0}"
ARCHITECTURE="all"
MAINTAINER="@JonasB2497"
DESCRIPTION="Digital pictureframe tool - scales and crops images to a given screen size."
LICENSE="MIT"
URL="https://example.com/pictureframe-tool"
DEPENDS=("python3" "python3-pyside6" "python3-pillow")

# --- paths ---
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SRC_DIR}/build/package"
OUTPUT_DIR="${SRC_DIR}/build"

# files to ship (relative to project root)
PACKAGE_FILES=(
    "cli.py"
    "converter.py"
    "ui.py"
    "ui"
)

# install location on the target system
INSTALL_PREFIX="/opt/${NAME}"

# --- helpers ---
err() { echo "error: $*" >&2; }
die() { err "$*"; exit 1; }

# --- checks ---
command -v fpm >/dev/null 2>&1 || die "fpm not found. Install it:
    gem install fpm     # via Ruby (recommended)
  or:
    apt-get install ruby ruby-dev && gem install fpm"

# --- prepare staging dir ---
rm -rf "${BUILD_DIR}"
mkdir -p "${INSTALL_PREFIX#/}"  # strip leading /
STAGING="$(mktemp -d)"
trap 'rm -rf "${STAGING}"' EXIT

DEST="${STAGING}${INSTALL_PREFIX}"
mkdir -p "${DEST}"

for f in "${PACKAGE_FILES[@]}"; do
    src="${SRC_DIR}/${f}"
    [ -e "${src}" ] || die "missing package file: ${f}"
    if [ -d "${src}" ]; then
        mkdir -p "${DEST}/$(dirname "${f}")"
        cp -a "${src}" "${DEST}/$(dirname "${f}")"
    else
        mkdir -p "${DEST}/$(dirname "${f}")"
        cp -a "${src}" "${DEST}/$(dirname "${f}")"
    fi
done

# make CLI entrypoint executable
chmod +x "${DEST}/cli.py" 2>/dev/null || true

# wrapper script so users get a command on PATH
BIN_DIR="${STAGING}/usr/bin"
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/${NAME}" <<EOF
#!/bin/sh
exec python3 "${INSTALL_PREFIX}/cli.py" "\$@"
EOF
chmod +x "${BIN_DIR}/${NAME}"
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/${NAME}-ui" <<EOF
#!/bin/sh
exec python3 "${INSTALL_PREFIX}/ui.py" "\$@"
EOF
chmod +x "${BIN_DIR}/${NAME}-ui"

# --- build depends flags ---
depends_args=()
for d in "${DEPENDS[@]}"; do
    depends_args+=(--depends "${d}")
done

mkdir -p "${OUTPUT_DIR}"

# --- run fpm ---
fpm \
    --input-type dir \
    --output-type deb \
    --name "${NAME}" \
    --version "${VERSION}" \
    --architecture "${ARCHITECTURE}" \
    --maintainer "${MAINTAINER}" \
    --description "${DESCRIPTION}" \
    --license "${LICENSE}" \
    --url "${URL}" \
    "${depends_args[@]}" \
    --chdir "${STAGING}" \
    --package "${OUTPUT_DIR}/${NAME}_${VERSION}_${ARCHITECTURE}.deb" \
    .

echo
echo "Package built: ${OUTPUT_DIR}/${NAME}_${VERSION}_${ARCHITECTURE}.deb"