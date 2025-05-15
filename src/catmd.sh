#!/bin/sh

# Exit on errors, undefined vars, and pipeline failures
set -eu

print_short_help() {
  echo 'Usage: catmd [OPTIONS] <PATH> [PATHS...]'
  echo
  echo 'Recursively prints the contents of all files not excluded'
  echo 'by a .gitignore as a markdown document.'
  echo
  echo 'Arguments:'
  echo '  PATH       The path to a file or directory to process.'
  echo '  PATHS...   Additional paths to process.'
  echo
  echo 'Options:'
  echo '  -h         Show this help message and exit'
  echo '  --help     Show the this help message with examples and exit'
  echo
}

print_long_help() {
  print_short_help
  echo 'Examples:'
  echo
  echo 'If we have a directory structure like this:'
  echo '  src/'
  echo '    ├── file1.txt'
  echo '    ├── file2.txt'
  echo '    └── .gitignore'
  echo '  notes.txt'
  echo '  config/'
  echo '    ├── file3.txt'
  echo '    └── config.yaml'
  echo
  echo 'Where src/file2.txt contains:'
  echo '  This is file2.'
  echo
  echo 'And src/.gitignore contains:'
  echo '  file1.txt'
  echo
  echo 'And notes.txt contains:'
  echo '  This is notes.'
  echo
  echo 'And config.yaml contains:'
  echo '  description: This is a config file.'
  echo
  echo 'Then running this script with the following command:'
  echo '  catmd src/ notes.txt config/*.yaml'
  echo
  echo 'Will print:'
  echo '  src/file2.txt'
  echo '  ```'
  echo '  This is file2.'
  echo '  ```'
  echo
  echo '  notes.txt'
  echo '  ```'
  echo '  This is notes.'
  echo '  ```'
  echo
  echo '  config/config.yaml'
  echo '  ```'
  echo '  description: This is a config file.'
  echo '  ```'
  echo
}

# Function to check if a file is ignored by a .gitignore in parent dirs
is_ignored() {
  FILE="$1"
  DIR=$(dirname "$FILE")

  while [ "$DIR" != "/" ] && [ -n "$DIR" ]; do
    if [ -f "$DIR/.gitignore" ]; then
      if git check-ignore --no-index -q --exclude-from="$DIR/.gitignore" "$FILE" 2>/dev/null; then
        return 0
      fi
    fi
    DIR=$(dirname "$DIR")
  done

  return 1
}

catmd() {
  if [ "$#" -eq 0 ]; then
    echo "Error: No input paths provided." >&2
    print_short_help
    exit 1
  fi

  for arg in "$@"; do
    case "$arg" in
      -h) print_short_help; exit 0 ;;
      --help) print_long_help; exit 0 ;;
    esac
  done

  for INPUT_PATH in "$@"; do
    case "$INPUT_PATH" in
      -h|--help) continue ;;
    esac

    case "$INPUT_PATH" in
      /*) ABS_PATH="$INPUT_PATH" ;;
      *) ABS_PATH="$(pwd)/$INPUT_PATH" ;;
    esac

    if [ -f "$ABS_PATH" ]; then
      ROOT_DIR=$(dirname "$ABS_PATH")
      FILES="$ABS_PATH"
    elif [ -d "$ABS_PATH" ]; then
      ROOT_DIR="$ABS_PATH"
      FILES=$(find "$ABS_PATH" -type f)
    else
      echo "Skipping invalid path: $INPUT_PATH" >&2
      continue
    fi

    echo "$FILES" | while IFS= read -r FILE; do
      if is_ignored "$FILE"; then
        continue
      fi

      REL_PATH="${FILE#$ROOT_DIR/}"

      echo "$REL_PATH"
      echo
      echo '```'
      cat "$FILE"
      echo '```'
      echo
    done
  done
}

catmd "$@"
