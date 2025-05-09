#!/bin/bash

set -ouex pipefail

if [ ! -f "$HOME/.local/share/ade/bin" ]; then
    mkdir -p "$HOME/.local/share/ade/"
    git clone https://github.com/adelynnmckay/bin.git "$HOME/.local/share/ade/bin"
fi

if [ "${PWD}" != "$HOME/.local/share/ade/bin" ]; then
    cd "$HOME/.local/share/ade/bin"
fi

cd ./src

for file in *; do
  if [[ "$file" == *.py || "$file" == *.sh ]]; then
    name="${file%.*}"
    binfile="$HOME/.bin/$name"
    bakfile="$binfile.bak"
    if [ -e "$binfile" ]; then
      if [ ! -L "$binfile" ] || [ "$(readlink -- "$binfile")" != "$(realpath -- "$file")" ]; then
        if [ -e "$bakfile" ]; then
          echo "Error: Backup file already exists: $bakfile"
          exit 1
        fi
        echo "Backing up $binfile to $bakfile"
        cp -a -- "$binfile" "$bakfile"
      fi
    fi
  fi
done

for file in *; do
  if [[ "$file" == *.py || "$file" == *.sh ]]; then
    name="${file%.*}"
    binfile="$HOME/.bin/$name"
    target_path="$(realpath -- "$file")"
    echo "Linking $target_path -> $binfile"
    ln -sf -- "$target_path" "$binfile"
  fi
done

echo "Done!"