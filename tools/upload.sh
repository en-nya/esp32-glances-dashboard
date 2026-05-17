#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-}"

if [[ -z "$PORT" ]]; then
  echo "Usage: ./tools/upload.sh <serial-port>"
  echo "Example: ./tools/upload.sh COM3"
  exit 1
fi

mpremote connect "$PORT" fs cp boot.py :boot.py
mpremote connect "$PORT" fs cp main.py :main.py
mpremote connect "$PORT" fs cp config.py :config.py
mpremote connect "$PORT" fs mkdir :lib || true
mpremote connect "$PORT" fs cp lib/pins.py :lib/pins.py
mpremote connect "$PORT" fs cp lib/display.py :lib/display.py
mpremote connect "$PORT" fs cp lib/glances_client.py :lib/glances_client.py
mpremote connect "$PORT" reset
