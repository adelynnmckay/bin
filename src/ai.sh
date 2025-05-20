#!/bin/bash

set -oue pipefail

ollama run --model "llama2" --prompt "$@"