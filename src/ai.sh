#!/bin/bash

set -oue pipefail

ollama run "llama3.2" "$@"