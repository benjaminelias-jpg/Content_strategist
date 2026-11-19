#!/usr/bin/env bash
# Trae (o actualiza) las dependencias vendorizadas desde sus repos originales.
#
#   tools/vendor_refresh.sh            # usa los commits fijados en vendor/pins.txt
#   tools/vendor_refresh.sh --latest   # trae la punta de la rama por defecto y reescribe los commits
#
# Copia solo el codigo ejecutable y las skills. Deja fuera docs, media, eval y tests
# del upstream: son ~80 MB de ejemplos que este proyecto no usa.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT/vendor"
SKILLS="$ROOT/.claude/skills"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

LATEST=0
[[ "${1:-}" == "--latest" ]] && LATEST=1

PINS="$VENDOR/pins.txt"
pinned() { awk -v k="$1" '$1==k {print $2}' "$PINS"; }

fetch() {  # fetch <slug> <url> -> clona en $WORK/<slug> al commit que toque
  local slug="$1" url="$2" ref
  if [[ $LATEST -eq 1 ]]; then
    GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "$url" "$WORK/$slug" >/dev/null 2>&1
  else
    ref="$(pinned "$slug")"
    [[ -n "$ref" ]] || { echo "sin commit fijado para $slug en vendor/pins.txt" >&2; exit 1; }
    GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none "$url" "$WORK/$slug" >/dev/null 2>&1
    git -C "$WORK/$slug" checkout --quiet "$ref"
  fi
  git -C "$WORK/$slug" rev-parse HEAD
}

copy() {  # copy <src-repo> <dest> <rutas...>
  local src="$1" dest="$2"; shift 2
  rm -rf "$dest"; mkdir -p "$dest"
  for p in "$@"; do
    [[ -e "$src/$p" ]] || { echo "falta $p en $src" >&2; exit 1; }
    cp -R "$src/$p" "$dest/"
  done
  find "$dest" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
}

echo "earshot ..."
EARSHOT_SHA="$(fetch earshot https://github.com/Leonxlnx/earshot)"
copy "$WORK/earshot" "$VENDOR/earshot" earshot pyproject.toml LICENSE README.md CHANGELOG.md
rm -rf "$SKILLS/earshot" "$SKILLS/real-sound"
cp -R "$WORK/earshot/skills/earshot"    "$SKILLS/earshot"
cp -R "$WORK/earshot/skills/real-sound" "$SKILLS/real-sound"

echo "rea-video ..."
REA_SHA="$(fetch rea-video https://github.com/JuneYaooo/rea-video)"
copy "$WORK/rea-video" "$VENDOR/rea-video" rea_video scripts pyproject.toml LICENSE NOTICE README.md
rm -rf "$SKILLS/rea-video"
cp -R "$WORK/rea-video/skills/rea-video" "$SKILLS/rea-video"

if [[ $LATEST -eq 1 ]]; then
  printf 'earshot   %s\nrea-video %s\n' "$EARSHOT_SHA" "$REA_SHA" > "$PINS"
  echo "commits actualizados en vendor/pins.txt — revisa el diff antes de confirmar"
fi

echo
echo "earshot   $EARSHOT_SHA"
echo "rea-video $REA_SHA"
du -sh "$VENDOR"/*
