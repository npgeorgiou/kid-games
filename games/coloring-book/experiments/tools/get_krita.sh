#!/bin/sh
# Krita's source (GPL), only the parts the brushes come from, at the commit this folder's presets were read from.
# Usage: sh get_krita.sh [folder]   (default: the temp folder's krita/)
set -e
D=${1:-${TMPDIR:-/tmp}/krita}
SHA=de9efc0685194181030aa4f9fa6a03de8f9d3cff
rm -rf "$D" && git init -q "$D" && cd "$D"
git remote add origin https://github.com/KDE/krita
git config core.sparseCheckout true
printf '%s\n' plugins/paintops/colorsmudge plugins/paintops/defaultpaintops/brush plugins/paintops/libpaintop plugins/paintops/spray libs/brush 'libs/image/kis_*mask_generator*' 'libs/image/kis_brush_mask_applicator*' krita/data/bundles > .git/info/sparse-checkout
git fetch -q --depth 1 --filter=blob:none origin $SHA && git checkout -q FETCH_HEAD
echo "$D"
