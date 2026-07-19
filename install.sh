#!/bin/sh
# Ana installer for macOS and Linux.
#   curl -fsSL https://raw.githubusercontent.com/matiomacedo/ana/main/install.sh | sh
# Install a specific version (e.g. a prerelease):
#   curl -fsSL https://raw.githubusercontent.com/matiomacedo/ana/main/install.sh | sh -s -- v0.1.0-rc1
set -eu

REPO="matiomacedo/ana"
requested_tag="${1:-${ANA_VERSION:-}}"

case "$(uname -s)" in
  Darwin) os="macos" ;;
  Linux)  os="linux" ;;
  *) echo "Unsupported OS: $(uname -s) (on Windows, use install.ps1)"; exit 1 ;;
esac
case "$(uname -m)" in
  arm64|aarch64) arch="arm64" ;;
  x86_64|amd64)  arch="x64" ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
target="${os}-${arch}"

case "$target" in
  macos-arm64|linux-x64) ;;
  *) echo "No prebuilt binary for $target yet — open an issue: https://github.com/$REPO/issues"; exit 1 ;;
esac

if [ -n "$requested_tag" ]; then
  tag="$requested_tag"
else
  tag="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)"
fi
if [ -z "$tag" ]; then
  echo "Could not find a published release. If this is a fresh project, the"
  echo "first release may not be out yet — check https://github.com/$REPO/releases"
  exit 1
fi

url="https://github.com/$REPO/releases/download/$tag/ana-$tag-$target.tar.gz"
share="${XDG_DATA_HOME:-$HOME/.local/share}/ana"
bin_dir="$HOME/.local/bin"

echo "Installing ana $tag ($target)..."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fL --progress-bar "$url" -o "$tmp/ana.tar.gz"

rm -rf "$share"
mkdir -p "$share" "$bin_dir"
tar -xzf "$tmp/ana.tar.gz" -C "$share" --strip-components 1

# Wrapper (not a symlink) so the launcher always finds its _internal dir.
printf '#!/bin/sh\nexec "%s/ana" "$@"\n' "$share" > "$bin_dir/ana"
chmod +x "$bin_dir/ana"

"$bin_dir/ana" --help > /dev/null
echo "Installed: $bin_dir/ana ($tag)"
case ":$PATH:" in
  *":$bin_dir:"*) ;;
  *) echo "Note: $bin_dir is not on your PATH. Add this to your shell profile:"
     echo "  export PATH=\"$bin_dir:\$PATH\"" ;;
esac
echo "Next: make sure Ollama is running, then run 'ana' in a project directory."
