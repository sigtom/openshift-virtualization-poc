#!/bin/bash
# Print an extra competitor VM manifest to the screen (or a file you choose). Nothing is applied.
# usage: scripts/render-competitor.sh NN > my-load-NN.yaml     (NN = 03, 04, ... two digits)
# It copies manifests/02-competitor-vm-01.yaml and renames EVERY occurrence of
# "cpumem-load-01" (VM, disk, hostname, labels). The result still has REPLACE_* placeholders:
# fill them in the same way as the other manifests before applying.
set -eu
nn=${1:-}
case $nn in [0-9][0-9]) ;; *) echo "usage: $0 NN   (two digits, e.g. 03)" >&2; exit 2 ;; esac
[ "$nn" != "01" ] && [ "$nn" != "02" ] || { echo "01 and 02 already exist as manifests" >&2; exit 2; }
src="$(dirname "$0")/../manifests/02-competitor-vm-01.yaml"
sed "s/cpumem-load-01/cpumem-load-$nn/g" "$src"
