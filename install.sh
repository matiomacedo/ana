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
  *) echo "Unsupported OS: $(uname -s) (Windows is not supported in the latest release)"; exit 1 ;;
esac
case "$(uname -m)" in
  arm64|aarch64) arch="arm64" ;;
  x86_64|amd64)  arch="x64" ;;
  *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;;
esac
target="${os}-${arch}"

case "$target" in
  macos-arm64|linux-x64|linux-arm64) ;;
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

asset="ana-$tag-$target.tar.gz"
base="https://github.com/$REPO/releases/download/$tag"
share="${XDG_DATA_HOME:-$HOME/.local/share}/ana"
bin_dir="$HOME/.local/bin"

echo "Installing ana $tag ($target)..."
tmp="$(mktemp -d)"
staged=""
trap 'rm -rf "$tmp" "$staged"' EXIT
curl -fL --progress-bar "$base/$asset" -o "$tmp/$asset"

if ! curl -fsSL "$base/ana-$tag-checksums.txt" -o "$tmp/checksums.txt"; then
  echo "Could not download the checksums for $tag, so nothing was installed."
  echo "Try again, or check https://github.com/$REPO/releases/tag/$tag"
  exit 1
fi
expected="$(awk -v asset="$asset" '{ file = $2; sub(/^\*/, "", file); sub(/^\.\//, "", file); if (file == asset) print $1 }' "$tmp/checksums.txt")"
if command -v sha256sum > /dev/null 2>&1; then
  actual="$(sha256sum "$tmp/$asset" | awk '{ print $1 }')"
elif command -v shasum > /dev/null 2>&1; then
  actual="$(shasum -a 256 "$tmp/$asset" | awk '{ print $1 }')"
else
  echo "Install sha256sum or shasum so the download can be verified. Nothing was installed."
  exit 1
fi
if [ -z "$expected" ] || [ "$expected" != "$actual" ]; then
  echo "The download does not match its published checksum, so nothing was installed."
  echo "  expected: ${expected:-no entry for $asset}"
  echo "  actual:   $actual"
  exit 1
fi

# Unpack and run the new version beside the old one, so a bad archive or a
# binary that won't start leaves the existing install working.
mkdir -p "$(dirname "$share")" "$bin_dir"
staged="$(mktemp -d "$share.new.XXXXXX")"
tar -xzf "$tmp/$asset" -C "$staged" --strip-components 1
"$staged/ana" --help > /dev/null

previous=""
if [ -e "$share" ]; then
  previous="$(mktemp -d "$share.old.XXXXXX")"
  mv "$share" "$previous/"
fi
mv "$staged" "$share"
staged=""
[ -z "$previous" ] || rm -rf "$previous"

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
