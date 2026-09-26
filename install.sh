#!/bin/sh
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 gjl. All rights reserved.
#
# gjl Installer for macOS and Linux
# Usage:
#   curl -fsSL https://gjl.io/install.sh | sh
# CLI-only (exclude Desktop GUI):
#   curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
#   # or: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
# Or via wget:
#   wget -qO- https://gjl.io/install.sh | sh

main() {
  set -eu

  owner="gjl-io"
  repo="gjl"

  # 1. Detect operating system
  os_raw="$(uname -s)"
  case "$os_raw" in
    Linux*)  os="linux" ;;
    Darwin*) os="darwin" ;;
    *)
      echo "Error: Unsupported operating system: $os_raw. gjl supports Linux and macOS." >&2
      exit 1
      ;;
  esac

  # 2. Detect CPU architecture
  arch_raw="$(uname -m)"
  case "$arch_raw" in
    x86_64|amd64)   arch="amd64" ;;
    aarch64|arm64)  arch="arm64" ;;
    *)
      echo "Error: Unsupported architecture: $arch_raw. gjl supports amd64 and arm64." >&2
      exit 1
      ;;
  esac

  # 3. HTTP download helper
  fetch() {
    url="$1"
    output="$2"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$url" -o "$output"
    elif command -v wget >/dev/null 2>&1; then
      wget -qO "$output" "$url"
    else
      echo "Error: Neither curl nor wget was found. Please install curl or wget first." >&2
      exit 1
    fi
  }

  fetch_text() {
    url="$1"
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL "$url" 2>/dev/null || true
    elif command -v wget >/dev/null 2>&1; then
      wget -qO- "$url" 2>/dev/null || true
    fi
  }

  # 4. Resolve release tag
  target_tag="${GJL_VERSION:-}"
  if [ -z "$target_tag" ]; then
    echo "Resolving latest gjl release..."
    releases_json="$(fetch_text "https://api.github.com/repos/${owner}/${repo}/releases" || true)"
    if [ -n "$releases_json" ]; then
      # Extract first tag_name from JSON array
      target_tag="$(printf '%s\n' "$releases_json" | grep -m1 '"tag_name":' | sed -E 's/.*"tag_name":[[:space:]]*"([^"]+)".*/\1/' || true)"
    fi
    if [ -z "$target_tag" ]; then
      target_tag="v0.0.1-alpha.1"
    fi
  fi

  # 5. Detect GUI availability
  cli_forced=0
  if [ "${GJL_CLI_ONLY:-0}" = "1" ] || [ "${GJL_CLI_ONLY:-false}" = "true" ]; then
    cli_forced=1
  fi

  for arg in "$@"; do
    case "$arg" in
      --cli-only|--cli|-c|--no-gui)
        cli_forced=1
        ;;
      --version=*|-v=*)
        target_tag="${arg#*=}"
        ;;
      --help|-h)
        echo "Usage: install.sh [--cli-only] [--version=vX.Y.Z]"
        exit 0
        ;;
    esac
  done

  has_gui=0
  if [ "$cli_forced" -eq 0 ]; then
    if [ "$os" = "darwin" ]; then
      # On macOS, check if running in a headless SSH session without graphics
      if [ -z "${SSH_CONNECTION:-}" ] && [ -z "${SSH_TTY:-}" ]; then
        has_gui=1
      elif pgrep -x WindowServer >/dev/null 2>&1; then
        has_gui=1
      fi
    elif [ "$os" = "linux" ]; then
      # On Linux, check for active display server
      if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
        has_gui=1
      fi
    fi
  fi

  # 6. Prepare target directories
  install_bin_dir="${GJL_INSTALL_DIR:-$HOME/.local/bin}"
  mkdir -p "$install_bin_dir"

  installed_desktop=0
  target_bin="$install_bin_dir/gjl"
  target_desktop=""

  # 7. Perform Download and Setup
  if [ "$has_gui" -eq 1 ] && [ "$os" = "darwin" ]; then
    # macOS Desktop + CLI bundle (ZIP)
    artifact_name="gjl-darwin-${arch}.zip"
    download_url="https://github.com/${owner}/${repo}/releases/download/${target_tag}/${artifact_name}"
    temp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t 'gjl')"
    temp_zip="$temp_dir/gjl.zip"

    echo "Downloading gjl Desktop & CLI (${target_tag}, ${artifact_name})..."
    fetch "$download_url" "$temp_zip"

    app_target_dir="/Applications"
    if [ ! -w "$app_target_dir" ]; then
      app_target_dir="$HOME/Applications"
      mkdir -p "$app_target_dir"
    fi

    echo "Extracting Desktop app to $app_target_dir..."
    rm -rf "$temp_dir/extracted"
    mkdir -p "$temp_dir/extracted"
    if command -v ditto >/dev/null 2>&1; then
      ditto -x -k "$temp_zip" "$temp_dir/extracted"
    else
      unzip -q "$temp_zip" -d "$temp_dir/extracted"
    fi

    found_app="$(find "$temp_dir/extracted" -maxdepth 2 -name "*.app" -type d | head -n 1)"
    if [ -n "$found_app" ]; then
      app_name="$(basename "$found_app")"
      rm -rf "$app_target_dir/$app_name"
      cp -R "$found_app" "$app_target_dir/$app_name"
      if [ -f "$app_target_dir/$app_name/Contents/Resources/gjl" ]; then
        ln -sf "$app_target_dir/$app_name/Contents/Resources/gjl" "$target_bin"
        chmod +x "$app_target_dir/$app_name/Contents/Resources/gjl"
      fi
      target_desktop="$app_target_dir/$app_name"
    fi

    rm -rf "$temp_dir"
    installed_desktop=1

  elif [ "$has_gui" -eq 1 ] && [ "$os" = "linux" ] && command -v unzip >/dev/null 2>&1; then
    # Linux Desktop + CLI bundle (ZIP)
    artifact_name="gjl-linux-${arch}.zip"
    download_url="https://github.com/${owner}/${repo}/releases/download/${target_tag}/${artifact_name}"
    desktop_app_dir="$HOME/.local/share/gjl"
    temp_dir="$(mktemp -d 2>/dev/null || mktemp -d -t 'gjl')"
    temp_zip="$temp_dir/gjl.zip"

    echo "Downloading gjl Desktop & CLI (${target_tag}, ${artifact_name})..."
    fetch "$download_url" "$temp_zip"

    echo "Extracting gjl bundle to $desktop_app_dir..."
    rm -rf "$desktop_app_dir"
    mkdir -p "$desktop_app_dir"
    unzip -q "$temp_zip" -d "$desktop_app_dir"
    chmod +x "$desktop_app_dir"/* 2>/dev/null || true
    desktop_bin="$(find "$desktop_app_dir" -maxdepth 1 -type f -perm /111 ! -name "gjl" 2>/dev/null | head -n 1 || true)"
    if [ -z "$desktop_bin" ]; then
      desktop_bin="$(find "$desktop_app_dir" -maxdepth 1 -type f ! -name "gjl" ! -name "*.json" ! -name "*.so" ! -name "*.png" 2>/dev/null | head -n 1 || true)"
    fi

    if [ -f "$desktop_app_dir/gjl" ]; then
      ln -sf "$desktop_app_dir/gjl" "$target_bin"
    fi

    # Create .desktop file if desktop applications folder exists
    apps_menu_dir="$HOME/.local/share/applications"
    if [ -d "$apps_menu_dir" ] || mkdir -p "$apps_menu_dir" 2>/dev/null; then
      icon_path="$(find "$desktop_app_dir" -name "*.png" 2>/dev/null | head -n 1 || true)"
      cat <<EOF > "$apps_menu_dir/gjl.desktop"
[Desktop Entry]
Name=gjl
Comment=A self-hosted policy boundary for LLM traffic
Exec=${desktop_bin:-$desktop_app_dir/gjl}
Icon=${icon_path:-gjl}
Terminal=false
Type=Application
Categories=Utility;Development;
EOF
      chmod +x "$apps_menu_dir/gjl.desktop" 2>/dev/null || true
    fi

    rm -rf "$temp_dir"
    installed_desktop=1
    target_desktop="${desktop_bin:-$desktop_app_dir}"

  else
    # Standalone CLI binary (Headless, CLI forced, or minimal Linux)
    binary_name="gjl-${os}-${arch}"
    download_url="https://github.com/${owner}/${repo}/releases/download/${target_tag}/${binary_name}"
    temp_bin="$install_bin_dir/gjl.tmp.$$"

    reason="Headless environment detected"
    if [ "$cli_forced" -eq 1 ]; then
      reason="CLI-only requested"
    elif [ "$has_gui" -eq 1 ] && [ "$os" = "linux" ] && ! command -v unzip >/dev/null 2>&1; then
      reason="unzip command not available; installing standalone CLI"
    fi

    echo "Downloading gjl CLI ($reason: ${target_tag}, ${binary_name})..."
    fetch "$download_url" "$temp_bin"

    if [ ! -s "$temp_bin" ]; then
      echo "Error: Downloaded binary is empty or missing." >&2
      rm -f "$temp_bin"
      exit 1
    fi

    chmod +x "$temp_bin"
    mv -f "$temp_bin" "$target_bin"
  fi

  # 8. Check and Update PATH in Shell Profiles
  in_path=0
  case ":$PATH:" in
    *":$install_bin_dir:"*) in_path=1 ;;
    *) in_path=0 ;;
  esac

  updated_profile=""
  if [ "$in_path" -eq 0 ]; then
    export_line="export PATH=\"$install_bin_dir:\$PATH\""
    for profile in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
      if [ -f "$profile" ] && [ -w "$profile" ]; then
        if ! grep -qF "$install_bin_dir" "$profile" 2>/dev/null; then
          printf '\n# gjl\n%s\n' "$export_line" >> "$profile"
          updated_profile="$profile"
          break
        fi
      fi
    done
  fi

  # 9. Print Success & Quick Start Instructions
  echo ""
  echo "============================================================"
  if [ "$installed_desktop" -eq 1 ]; then
    echo "gjl was successfully installed!"
    echo "  CLI:     $target_bin"
    echo "  Desktop: $target_desktop"
  else
    echo "gjl CLI was successfully installed!"
    echo "  CLI:     $target_bin"
  fi
  echo ""

  if [ "$in_path" -eq 0 ]; then
    if [ -n "$updated_profile" ]; then
      echo "Notice: Added $install_bin_dir to PATH in $updated_profile."
    fi
    echo "To use gjl right away in this terminal session, run:"
    echo "  export PATH=\"$install_bin_dir:\$PATH\""
    echo ""
  fi

  echo "To get started, run:"
  echo "  gjl run     # Start local relay daemon"
  if [ "$installed_desktop" -eq 1 ]; then
    echo "  gjl gui     # Launch Desktop management GUI"
  else
    echo "  gjl --help  # View CLI management commands"
  fi
  echo "============================================================"
  echo ""
}

main "$@"
