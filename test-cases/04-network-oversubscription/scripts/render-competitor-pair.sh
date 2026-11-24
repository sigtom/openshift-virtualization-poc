#!/bin/bash
# Print an extra competitor pair (server VM, internal Service, client VM) to the screen. Nothing is applied.
# usage: scripts/render-competitor-pair.sh NN > my-pair-NN.yaml     (NN = 03, 04, ... two digits)
# It copies manifests/02-competitor-pair-01.yaml and renames EVERY occurrence of "-01" in the
# object names (netload-server-01, netload-client-01, disks, hostnames, labels, Service selector).
# The result still has REPLACE_* placeholders: fill them in as for the other manifests.
set -eu
nn=${1:-}
case $nn in [0-9][0-9]) ;; *) echo "usage: $0 NN   (two digits, e.g. 03)" >&2; exit 2 ;; esac
[ "$nn" != "01" ] && [ "$nn" != "02" ] || { echo "01 and 02 already exist as manifests" >&2; exit 2; }
src="$(dirname "$0")/../manifests/02-competitor-pair-01.yaml"
sed -e "s/netload-server-01/netload-server-$nn/g" -e "s/netload-client-01/netload-client-$nn/g" "$src"
