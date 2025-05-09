#!/bin/bash

set -ouex pipefail

main() {
    local -r path_to_submodule="${1:?}"
    git rm "${path_to_submodule}" || echo
    rm -rf ".git/modules/${path_to_submodule}"
    git config --remove-section "submodule.${path_to_submodule}"
}

main $@