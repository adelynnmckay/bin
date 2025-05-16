#!/bin/sh

set -eu

print_help() {
  echo "Usage: rsed [-i] [-e SCRIPT]... [-f FILE]... [--] <SED_EXPRESSION | -e/-f ...> <PATH> [PATHS...]"
  echo
  echo "Recursively apply sed expressions to files not ignored by .gitignore."
  echo
  echo "Options:"
  echo "  -i              Edit files in-place"
  echo "  -e SCRIPT       Add a sed script to execute"
  echo "  -f FILE         Add a file containing sed scripts to execute"
  echo "  -h, --help      Show this help message and exit"
  echo
  echo "Examples:"
  echo "  rsed 's/foo/bar/g' file1.txt dir/"
  echo "  rsed -i -e 's/foo/bar/g' -e 's/baz/qux/' dir/"
  echo
}

is_ignored() {
  FILE="$1"
  DIR=$(dirname "$FILE")
  PREV_DIR=""

  while [ "$DIR" != "/" ] && [ -n "$DIR" ] && [ "$DIR" != "$PREV_DIR" ]; do
    if [ -f "$DIR/.gitignore" ]; then
      if git check-ignore --no-index -q --exclude-from="$DIR/.gitignore" "$FILE" 2>/dev/null; then
        return 0
      fi
    fi
    PREV_DIR="$DIR"
    DIR=$(dirname "$DIR")
  done

  return 1
}

rsed() {
  INPLACE=""
  SED_ARGS=""
  SED_PROVIDED=0
  FILES=""

  # Parse options and detect sed expressions
  while [ $# -gt 0 ]; do
    case "$1" in
      -h|--help)
        print_help
        exit 0
        ;;
      -i)
        INPLACE='-i'
        shift
        ;;
      -e)
        if [ $# -lt 2 ]; then
          echo "Error: -e requires an argument." >&2
          exit 1
        fi
        SED_ARGS="$SED_ARGS -e \"$2\""
        SED_PROVIDED=1
        shift 2
        ;;
      -f)
        if [ $# -lt 2 ]; then
          echo "Error: -f requires a file path." >&2
          exit 1
        fi
        SED_ARGS="$SED_ARGS -f \"$2\""
        SED_PROVIDED=1
        shift 2
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "Unknown option: $1" >&2
        exit 1
        ;;
      *)
        break
        ;;
    esac
  done

  # If no -e or -f provided, treat first non-option as a sed expression
  if [ "$SED_PROVIDED" -eq 0 ]; then
    if [ $# -eq 0 ]; then
      echo "Error: No sed expression provided." >&2
      exit 1
    fi
    SED_ARGS="-e \"$1\""
    shift
  fi

  # Remaining args = paths
  if [ $# -eq 0 ]; then
    echo "Error: No input paths provided." >&2
    print_help
    exit 1
  fi

  # Collect files
  for INPUT_PATH in "$@"; do
    case "$INPUT_PATH" in
      /*) ABS_PATH="$INPUT_PATH" ;;
      *) ABS_PATH="$(pwd)/$INPUT_PATH" ;;
    esac

    if [ -f "$ABS_PATH" ]; then
      FILES="$FILES
$ABS_PATH"
    elif [ -d "$ABS_PATH" ]; then
      FOUND=$(find "$ABS_PATH" -type f)
      FILES="$FILES
$FOUND"
    else
      echo "Skipping invalid path: $INPUT_PATH" >&2
    fi
  done

  # Apply sed to each file
  echo "$FILES" | while IFS= read -r FILE; do
    [ -z "$FILE" ] && continue
    is_ignored "$FILE" && continue

    if [ -n "$INPLACE" ]; then
      if sed -i '' $(eval echo "$SED_ARGS") "$FILE" 2>/dev/null; then
        :
      else
        TMP=$(mktemp)
        eval sed "$SED_ARGS" "\"$FILE\"" > "$TMP"
        mv "$TMP" "$FILE"
      fi
    else
      eval sed "$SED_ARGS" "\"$FILE\""
    fi
  done
}

rsed "$@"
