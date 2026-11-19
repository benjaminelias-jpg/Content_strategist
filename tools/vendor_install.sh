#!/usr/bin/env bash
# Instala las dependencias vendorizadas en el entorno Python actual.
#
#   tools/vendor_install.sh            # las dos
#   tools/vendor_install.sh rea-video  # solo una
#
# Requiere ffmpeg y Python >= 3.10. earshot arrastra torch: se instala desde el
# indice de CPU para no bajar las ruedas de CUDA (varios GB que aqui no sirven).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHICH="${1:-all}"
PIP=(python3 -m pip install --quiet)

command -v ffmpeg >/dev/null || { echo "falta ffmpeg — instalalo antes"; exit 1; }

if [[ "$WHICH" == "all" || "$WHICH" == "rea-video" ]]; then
  echo "instalando rea-video ..."
  "${PIP[@]}" -e "$ROOT/vendor/rea-video"
fi

if [[ "$WHICH" == "all" || "$WHICH" == "earshot" ]]; then
  echo "instalando torch (CPU) ..."
  "${PIP[@]}" torch --index-url https://download.pytorch.org/whl/cpu
  echo "instalando earshot ..."
  "${PIP[@]}" -e "$ROOT/vendor/earshot"
fi

echo
command -v rea-video >/dev/null && rea-video --version 2>/dev/null || true
command -v earshot   >/dev/null && earshot --version   2>/dev/null || true
echo "listo"
