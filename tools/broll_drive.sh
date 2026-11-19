#!/usr/bin/env bash
# Sincroniza el b-roll desde la carpeta de Drive del usuario.
#
#   tools/broll_drive.sh            # baja lo que falte en media/broll_drive/
#   tools/broll_drive.sh --forzar   # vuelve a bajarlo todo
#
# La carpeta esta compartida por enlace, asi que se bajan por el endpoint
# publico de Drive y no hace falta credencial. Para listar lo que hay (y
# detectar clips nuevos) se usa el conector de Google Drive, no este script:
# aqui los ids van fijados en ids.txt porque un script no deberia depender de
# un conector para algo que tiene que poder correr solo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="$ROOT/media/broll_drive"
IDS="$DST/ids.txt"
CARPETA="https://drive.google.com/drive/folders/1WEtcffz7ng4FSCyl0aA4hFwuwiXJUfnh"

[[ -f "$IDS" ]] || { echo "falta $IDS (dos columnas: <drive_id> <nombre>)"; exit 1; }
mkdir -p "$DST"
FORZAR=0
[[ "${1:-}" == "--forzar" ]] && FORZAR=1

nuevos=0
while read -r id nombre; do
  [[ -z "${id:-}" ]] && continue
  f="$DST/pin_${nombre}.mp4"
  if [[ -s "$f" && $FORZAR -eq 0 ]]; then continue; fi
  echo "bajando $nombre ..."
  curl -sSL --max-time 300 -o "$f" "https://drive.google.com/uc?export=download&id=${id}"
  # Drive devuelve HTML cuando el archivo no es publico o pide confirmacion:
  # sin esta comprobacion acabas con un .mp4 que es una pagina de error.
  if ! ffprobe -v error -show_entries format=format_name -of csv=p=0 "$f" >/dev/null 2>&1; then
    echo "  ERROR: lo descargado no es un video. Revisa que $CARPETA siga compartido por enlace."
    rm -f "$f"; continue
  fi
  nuevos=$((nuevos+1))
done < "$IDS"

echo
echo "$nuevos nuevos | $(ls "$DST"/*.mp4 2>/dev/null | wc -l) clips en total"
echo "catalogo: $DST/catalogo.json  (regeneralo si has anadido clips)"
