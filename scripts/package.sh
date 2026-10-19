#!/usr/bin/env bash
# Package a built dist/ into release assets, reproducibly.
#   scripts/package.sh <dist> <outdir>
# Writes hebrew-bible-<version>.sqlite.gz, hb<v>-chapters.tgz, hb<v>-report.tgz and SHA256SUMS.
# README.md, LICENSE-DATA.md and LICENSE sit next to the data inside both tars.
set -euo pipefail
dist="$1"
out="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
version="$(sed -n 's/^DATASET_VERSION=//p' "$root/sources/PINS.txt")"
short="hb${version//./}"
epoch="${SOURCE_DATE_EPOCH:-$(git -C "$root" log -1 --format=%ct)}"
mkdir -p "$out"
cp "$root/README.md" "$root/LICENSE-DATA.md" "$root/LICENSE" "$dist/"
tarball() {
  local name="$1"; shift
  tar --sort=name --mtime="@$epoch" --owner=0 --group=0 --numeric-owner --format=gnu \
    -C "$dist" -cf - "$@" | gzip -n -9 > "$out/$name"
}
tarball "$short-chapters.tgz" json README.md LICENSE-DATA.md LICENSE
tarball "$short-report.tgz" build-report README.md LICENSE-DATA.md LICENSE
gzip -n -9 -c "$dist/hebrew-bible.sqlite" > "$out/hebrew-bible-$version.sqlite.gz"
(cd "$out" && sha256sum "hebrew-bible-$version.sqlite.gz" "$short-chapters.tgz" "$short-report.tgz" > SHA256SUMS)
cat "$out/SHA256SUMS"
