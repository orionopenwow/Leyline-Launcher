#!/bin/bash
# macOS: double-click to host a Leyline realm on this Mac (Docker). Linux: bash labs/openvanilla-realm/host/ovhost install
cd "$(dirname "$0")" || exit 1
bash ovhost install "$@"
echo
read -r -p "Press Enter to close this window." _
