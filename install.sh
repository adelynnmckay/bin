#!/bin/bash

set -oue pipefail

if [ ! -d "$HOME/.local/share/ade/bin" ]; then
    mkdir -p "$HOME/.local/share/ade/bin"
    git clone https://github.com/adelynnmckay/bin.git "$HOME/.local/share/ade/bin"
fi

if [ "${PWD}" != "$HOME/.local/share/ade/bin" ]; then
    echo "Updating scripts in ~/.local/share/ade/bin..."
    cd "$HOME/.local/share/ade/bin"
    git pull
fi

cd ./src

mkdir -p "$HOME/.bin"

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

chmod +x "$HOME/.local/share/ade/bin/"*
chmod +x "$HOME/.bin/"*

echo "Done!"