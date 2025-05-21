#!/bin/bash
set -euo pipefail

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

show_help() {
  echo "Usage: $0 [--for-each] <input.gpg or dir> [output_dir]"
  echo
  echo "Decrypt GPG-encrypted TAR archives (created with encrypt.sh)."
  echo
  echo "Arguments:"
  echo "  --for-each      Decrypt each .tar.gz.gpg file inside a folder"
  echo "  input           tar.gz.gpg file or directory of tar.gz.gpg files"
  echo "  output_dir      Optional. Defaults to current directory."
  echo
  echo "Examples:"
  echo "  $0 secrets.tar.gz.gpg decrypted/"
  echo "  $0 --for-each encrypted/ output/"
}

log() {
  echo "[decrypt.sh] $1"
}

if [[ $# -lt 1 ]] || [[ "$1" == "--help" ]]; then
  show_help
  exit 0
fi

FOR_EACH=false
if [[ "$1" == "--for-each" ]]; then
  FOR_EACH=true
  shift
fi

if [[ $# -lt 1 ]]; then
  show_help
  echo "❌ Error: Missing input file or directory"
  exit 1
fi

INPUT="$1"
OUTDIR="${2:-.}"
mkdir -p "$OUTDIR"

read -s -p "Enter password to decrypt: " PASSWORD
echo

decrypt_file() {
  local infile="$1"
  local base="$(basename "$infile" .tar.gz.gpg)"
  local temp="$TMPDIR/$base.tar.gz"
  local outdir="$OUTDIR/$base"
  mkdir -p "$outdir"

  gpg --batch --yes --passphrase "$PASSWORD" -o "$temp" -d "$infile"
  tar -xzf "$temp" -C "$outdir"
  log "🔓 Decrypted: $infile → $outdir/"
}

if $FOR_EACH; then
  if [[ ! -d "$INPUT" ]]; then
    log "❌ Input must be a directory when using --for-each"
    exit 1
  fi
  shopt -s nullglob
  for file in "$INPUT"/*.tar.gz.gpg; do
    decrypt_file "$file"
  done
else
  if [[ ! -f "$INPUT" ]]; then
    log "❌ File not found: $INPUT"
    exit 1
  fi
  decrypt_file "$INPUT"
fi
