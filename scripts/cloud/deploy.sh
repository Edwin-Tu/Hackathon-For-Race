#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname "$0")/deploy_ecs.sh" "$@"
