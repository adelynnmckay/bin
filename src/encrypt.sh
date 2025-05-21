#!/bin/bash
set -euo pipefail

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

show_help() {
  echo "Usage: $0 [--for-each] <output.gpg> <input1> [input2 ...]"
  echo
  echo "Encrypt files or folders using GPG (AES-256 symmetric encryption)."
  echo
  echo "Arguments:"
  echo "  --for-each          Encrypt each file individually. Skips directories."
  echo "  output.tar.gz.gpg   Output file name (ignored if --for-each is used)."
  echo "  input(s)            Files and/or directories to encrypt."
  echo
  echo "Examples:"
  echo "  $0 archive.tar.gz.gpg notes/ pictures/"
  echo "  $0 --for-each encrypted/ secrets.txt configs/"
}

log() {
  echo "[encrypt.sh] $1"
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

if $FOR_EACH; then
  if [[ $# -lt 2 ]]; then
    show_help
    echo "❌ Error: Must specify output directory and at least one input when using --for-each"
    exit 1
  fi
  OUTDIR="$1"
  shift
  mkdir -p "$OUTDIR"
else
  if [[ $# -lt 2 ]]; then
    show_help
    echo "❌ Error: Must specify output filename and at least one input"
    exit 1
  fi
  OUTPUT="$1"
  shift
  if [[ "$OUTPUT" != *.tar.gz.gpg ]]; then
    log "❌ Output must end with .tar.gz.gpg"
    exit 1
  fi
fi

read -s -p "Enter password: " PASSWORD
echo
read -s -p "Confirm password: " CONFIRM
echo
if [[ "$PASSWORD" != "$CONFIRM" ]]; then
  log "❌ Passwords do not match"
  exit 1
fi

encrypt_file() {
  local input_file="$1"
  local output_file="$2"
  local base="$(basename "$input_file")"
  local temp="$(mktemp "$TMPDIR/${base//[^a-zA-Z0-9]/_}.XXXXXX.tar.gz")"

  tar -czf "$temp" -C "$(dirname "$input_file")" "$base"
  gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase "$PASSWORD" -o "$output_file" "$temp"
  log "🔐 Encrypted: $input_file → $output_file"
}

if $FOR_EACH; then
  for input in "$@"; do
    if [[ -f "$input" ]]; then
      out_file="$OUTDIR/$(basename "$input").tar.gz.gpg"
      encrypt_file "$input" "$out_file"
    elif [[ -d "$input" ]]; then
      while IFS= read -r -d '' file; do
        out_file="$OUTDIR/$(basename "$file").tar.gz.gpg"
        encrypt_file "$file" "$out_file"
      done < <(find "$input" -type f -print0)
    else
      log "⚠️ Skipping: $input (not a file or directory)"
    fi
  done
else
  TMP_TAR="$TMPDIR/bundle.tar.gz"
  tar -czf "$TMP_TAR" "$@"
  gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase "$PASSWORD" -o "$OUTPUT" "$TMP_TAR"
  log "✅ Archive created: $OUTPUT"
fi
